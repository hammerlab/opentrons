from collections import OrderedDict
import json
import os

from opentrons.containers.container_file_loading import get_persisted_container
from opentrons.containers import container_file_loading
from opentrons.containers.placeable import (
    Deck,
    Slot,
    Container,
    Well,
    WellSeries,
    unpack_location
)
from opentrons.containers.calibrator import apply_calibration
from opentrons.util import environment

__all__ = [
    get_persisted_container,
    Deck,
    Slot,
    Container,
    Well,
    WellSeries,
    unpack_location,
    apply_calibration]


def load(robot, container_name, slot, label=None):
    """
    Examples
    --------
    >>> from opentrons import containers
    >>> containers.load('96-flat', 'A1')
    <Deck>/<Slot A1>/<Container 96-flat>
    >>> containers.load('96-flat', 'A2', 'plate')
    <Deck>/<Slot A2>/<Container plate>
    >>> containers.load('non-existent-type', 'A2') # doctest: +ELLIPSIS
    Exception: Container type "non-existent-type" not found in file ...
    """
    return robot.add_container(container_name, slot, label)


def list():
    return container_file_loading.list_container_names()


def create(name, grid, spacing, diameter, depth, volume=0):
    columns, rows = grid
    col_spacing, row_spacing = spacing
    custom_container = Container()
    properties = {
        'type': 'custom',
        'diameter': diameter,
        'height': depth,
        'total-liquid-volume': volume
    }

    for r in range(rows):
        for c in range(columns):
            well = Well(properties=properties)
            well_name = chr(c + ord('A')) + str(1 + r)
            coordinates = (c * col_spacing, r * row_spacing, 0)
            custom_container.add(well, well_name, coordinates)
    json_container = container_to_json(custom_container, name)
    save_custom_container(json_container)
    container_file_loading.load_all_containers_from_disk()

#FIXME: [Jared - 8/31/17] This is not clean
#FIXME: fix it by using the same reference points in saved containers and Container/Well objects
def container_to_json(c, name):
    locations = []
    c_x, c_y, c_z = c._coordinates
    container_offset = {'x': c_x,'y': c_y, 'z': c_z}
    for w in c:
        x, y, z = w._coordinates + w.bottom()[1]
        properties_dict = {
            'x': x, 'y': y, 'z': z,
            'depth': w.z_size(),
            'total-liquid-volume': w.max_volume()
        }
        if w.properties.get('diameter'):
            properties_dict.update({'diameter': w.properties['diameter']})
        else:
            properties_dict.update({'width': w.properties['width'], 'length': w.properties['length']})
        locations.append((
            w.get_name(),
            properties_dict

        ))
    return {name: {'origin-offset': container_offset,'locations': OrderedDict(locations)}}


def save_custom_container(data):
    container_file_path = environment.get_path('CONTAINERS_FILE')
    if not os.path.isfile(container_file_path):
        with open(container_file_path, 'w') as f:
            f.write(json.dumps({'containers': {}}))
    with open(container_file_path, 'r+') as f:
        old_data = json.load(f)
        old_data['containers'].update(data)
        f.seek(0)
        f.write(json.dumps(old_data, indent=4))
        f.truncate()
