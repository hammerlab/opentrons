import copy
import json
import logging
import os
import sys

from opentrons.util import environment
from opentrons.util.vector import Vector, VectorEncoder


JSON_ERROR = None
if sys.version_info > (3, 4):
    JSON_ERROR = ValueError
else:
    JSON_ERROR = json.decoder.JSONDecodeError

log = logging.getLogger(__name__)


class CalibratorFileManager(object):
    def __init__(self, calibration_file : str):
        self.calibration_file = calibration_file

        # calibration_data_version = 1
        # calibration_key = "unique_name"
        # persisted_attributes = []
        # persisted_defaults = {}
        self.persisted_attributes = ['calibration_data', 'positions', 'max_volume']
        self.persisted_defaults = {}

    def exists(self):
        """
        Returns true if calibration data file exists
        :return: bool
        """
        return os.path.exists(self.calibration_file)

    def load(self):
        with open(self.calibration_file) as f:
            return json.load(f)

    def get(self, instrument_id : str):
        

    def create(self, instrument_id : str):
        """
        Creates empty calibrations data if not already present

        Parameters
        ----------
        key : str
            The unique string to save this instrument's calibration data

        attributes : list
            A list of this instrument's attribute names to be saved
        """

        calibration_data = {}
        try:
            calibration_data = self.load()
        except (FileNotFoundError, JSON_ERROR):
            self._write_blank_calibrations_file()

        self.calibration_key = instrument_id
        for key in self.persisted_attributes:
            self.persisted_defaults[key] = copy.copy(getattr(self, key))

        if not os.path.isfile(self._get_calibration_file_path()):
            self._write_blank_calibrations_file()

    def update_calibrations(self):
        """
        Saves the instrument's persisted attributes to file
        """
        last_persisted_data = self._read_calibrations()

        last_persisted_data['data'][self.calibration_key] = (
            self._strip_vector(
                self._build_calibration_data())
        )

        last_persisted_data = self._strip_vector(last_persisted_data)

        with open(self._get_calibration_file_path(), 'w') as f:
            f.write(json.dumps(last_persisted_data, indent=4))

    def load_persisted_data(self):
        """
        Loads and sets the instrument's peristed attributes from file
        """
        last_persisted_data = self._get_calibration()
        if last_persisted_data:
            last_persisted_data = self._restore_vector(last_persisted_data)
            for key, val in last_persisted_data.items():
                setattr(self, key, val)

    def delete_calibration_data(self):
        """
        Set the instrument's properties to their initialized values,
        and saves those initialized values to file
        """
        for key, val in self.persisted_defaults.items():
            setattr(self, key, val)
        self.update_calibrations()

    def _delete_calibration_file(self):
        """
        Deletes the entire calibrations file
        """
        file_path = self._get_calibration_file_path()
        if os.path.exists(file_path):
            os.remove(file_path)

    def _write_blank_calibrations_file(self):
        self._delete_calibration_file()
        with open(self._get_calibration_file_path(), 'w') as f:
            f.write(json.dumps({
                'version': 1,  # TODO this should prob not be handled here
                'data': {}
            }))

    def _get_calibration_file_path(self):
        """
        :return: the absolute file path of the calibration file
        """
        return environment.get_path('CALIBRATIONS_FILE')

    def _get_calibration(self):
        """
        :return: this instrument's saved calibrations data
        """
        data = self._read_calibrations()['data']
        return data.get(self.calibration_key)

    def _build_calibration_data(self):
        """
        :return: copy of this instrument's persisted attributes
        """
        calibration = {}
        for attr in self.persisted_attributes:
            calibration[attr] = copy.copy(getattr(self, attr))
        return calibration

    def _read_calibrations(self):
        """
        Reads calibration data from file system.
        Expects a valid valibration format
        :return: json of calibration data
        """
        file_path = self._get_calibration_file_path()
        self._validate_calibration_file(file_path)
        loaded_json = ""
        with open(file_path) as f:
            loaded_json = json.load(f)

        return self._restore_vector(loaded_json)

    def _validate_calibration_file(self, file_path):
        """
        Read calibration file, and checks for version number
        If no version number, file is replaced with version number
        """
        valid = False
        with open(file_path) as f:
            try:
                file = json.load(f)
                version = file.get('version')
                data = file.get('data')
                if version and data and len(file.keys()) == 2:
                    valid = True
            except json.decoder.JSONDecodeError as e:
                log.error(
                    'Error parsing calibration data (file: {}): {}'.format(
                        file_path, e))

        if not valid:
            self._write_blank_calibrations_file()

    def _strip_vector(self, obj, root=True):
        """
        Iterates through a dictionary, converting Vector classes
        to serializable dictionaries
        :return: json of calibration data
        """
        obj = (copy.deepcopy(obj) if root else obj)
        for key, val in obj.items():
            if isinstance(val, Vector):
                res = json.dumps(val, cls=VectorEncoder)
                obj[key] = res
            elif isinstance(val, dict):
                self._strip_vector(val, root=False)

        return obj

    def _restore_vector(self, obj, root=True):
        """
        Iterates through a dictionary, converting serializable
        Vector dictionaries to Vector classes
        :return: json of calibration data
        """
        obj = (copy.deepcopy(obj) if root else obj)
        for key, val in obj.items():
            if isinstance(val, dict):
                self._restore_vector(val, root=False)
            elif isinstance(val, str):
                try:
                    res = Vector(json.loads(val))
                    obj[key] = res
                except JSON_ERROR:
                    pass
        return obj
