import unittest

from opentrons import drivers
from opentrons.containers import load as containers_load
from opentrons.containers.placeable import Deck
from opentrons.instruments import pipette
from opentrons.robot.robot import Robot
from opentrons.util.vector import Vector
from opentrons.util.testing.fixtures import robot
from opentrons.util.testing.util import build_temp_db, approx


def test_pos_tracker_persistance(robot, tmpdir):

    build_temp_db(tmpdir)
    p200 = pipette.Pipette(
        robot, axis='b', name='my-fancy-pancy-pipette'
    )
    plate = containers_load(robot, 'trough-12row', 'B2')
    assert robot.max_deck_height() == 40

    robot.move_head(x=10, y=10, z=10)
    robot.calibrate_container_with_instrument(plate, p200, save=False)
    print('saved')
    assert robot.max_deck_height() == 50

def test_calibrated_max_z(robot, tmpdir):
    print('pt_len: ', len(robot.position_tracker._position_dict))
    print("TEST_MAX IN SUB: ", robot.position_tracker.max_z_in_subtree(robot._deck))
    print("TEST_deck id: ", id(robot._deck))

    build_temp_db(tmpdir)
    p200 = pipette.Pipette(
        robot, axis='b', name='my-fancy-pancy-pipette'
    )

    plate = containers_load(robot, '96-flat', 'A1')
    assert robot.max_deck_height() == 10.5

    robot.move_head(x=10, y=10, z=10)
    robot.calibrate_container_with_instrument(plate, p200, save=False)

    assert robot.max_deck_height() == 20.5

class RobotTest(unittest.TestCase):
    def setUp(self):
        self.robot = Robot()

        self.smoothie_version = 'edge-1c222d9NOMSD'

        self.robot.reset()
        self.robot.connect(options={'firmware': self.smoothie_version})
        self.robot.home(enqueue=False)

    def test_firmware_verson(self):
        self.assertEquals(
            self.smoothie_version, self.robot._driver.firmware_version)

    def test_add_container(self):
        c1 = self.robot.add_container('96-flat', 'A1')
        res = self.robot.get_containers()
        expected = [
            c1
        ]
        self.assertEquals(res, expected)

        c2 = self.robot.add_container('96-flat', 'A2', 'my-special-plate')
        res = self.robot.get_containers()
        expected = [
            c1,
            c2
        ]
        self.assertEquals(res, expected)

    def test_comment(self):
        self.robot.clear_commands()
        self.robot.comment('hello')
        self.assertEquals(len(self.robot.commands()), 1)
        self.assertEquals(self.robot._commands[0], 'hello')

    def test_home_after_disconnect(self):
        self.robot._driver.connection = None
        self.assertRaises(RuntimeError, self.robot.home)

    # TODO: reevaluate/implement this test...
    # def test_stop_run(self):
    #     p200 = pipette.Pipette(
    #         self.robot, axis='b', name='my-fancy-pancy-pipette'
    #     )
    #     p200.calibrate_plunger(top=0, bottom=5, blow_out=6, drop_tip=7)
    #
    #     for i in range(1000):
    #         p200.aspirate().dispense()
    #
    #     res = None
    #
    #     def _run():
    #         nonlocal res
    #         self.assertRaises(RuntimeError, self.robot.run)
    #
    #     thread = threading.Thread(target=_run)
    #     thread.start()
    #
    #     self.robot.stop()
    #
    #     thread.join()


    def test_create_arc(self):
        p200 = pipette.Pipette(
            self.robot, axis='b', name='my-fancy-pancy-pipette'
        )
        plate = containers_load(self.robot, '96-flat', 'A1')
        plate2 = containers_load(self.robot, '96-flat', 'B1')
        self.robot.move_head(x=10, y=10, z=10)
        self.robot.calibrate_container_with_instrument(plate, p200, save=False)

        res = self.robot._create_arc((0, 0, 0), plate[0])
        expected = [
            {'z': 25.5},
            {'x': 0, 'y': 0},
            {'z': 0}
        ]
        self.assertEquals(res, expected)

        self.robot.move_head(x=10, y=10, z=100)
        self.robot.calibrate_container_with_instrument(plate, p200, save=False)
        res = self.robot._create_arc((0, 0, 0), plate[0])
        expected = [
            {'z': 100},
            {'x': 0, 'y': 0},
            {'z': 0}
        ]
        self.assertEquals(res, expected)

    def test_disconnect(self):
        self.robot.disconnect()
        res = self.robot.is_connected()
        self.assertEquals(bool(res), False)

    def test_get_connected_port(self):
        res = self.robot.get_connected_port()
        self.assertEquals(res, drivers.VIRTUAL_SMOOTHIE_PORT)

    def test_robot_move_to(self):
        self.robot.move_to((self.robot._deck, (100, 0, 0)))
        position = self.robot._driver.get_head_position()['current']
        self.assertEqual(position, (100, 0, 0))

    def test_move_head(self):
        self.robot.move_head(x=100, y=0, z=20)
        current = self.robot._driver.get_head_position()['current']
        self.assertEquals(current, (100, 0, 20))

    def test_home(self):
        self.robot.disconnect()
        self.robot.connect()

        # Check that all axes are marked as not homed
        self.assertDictEqual(self.robot.axis_homed, {
            'x': False, 'y': False, 'z': False, 'a': False, 'b': False
        })

        # self.robot.clear_commands()
        # Home X & Y axes
        self.robot.home('xa')
        # self.assertDictEqual(self.robot.axis_homed, {
        #     'x': False, 'y': False, 'z': False, 'a': False, 'b': False
        # })

        # Verify X & Y axes are marked as homed
        self.assertDictEqual(self.robot.axis_homed, {
            'x': True, 'y': False, 'z': False, 'a': True, 'b': False
        })

        # Home all axes
        self.robot.home()

        # Verify all axes are marked as homed
        self.assertDictEqual(self.robot.axis_homed, {
            'x': True, 'y': True, 'z': True, 'a': True, 'b': True
        })

    def test_robot_pause_and_resume(self):
        self.robot.move_to((self.robot._deck, (100, 0, 0)))
        self.robot.move_to((self.robot._deck, (101, 0, 0)))
        self.assertEqual(len(self.robot._commands), 0)

        #
        # FIXME: pause and resume can't be measured based on whether commands
        # in the command queue are executed since all robot actions will be
        # called immediately
        #

        # self.robot.pause()
        #
        # def _run():
        #     self.robot.run()
        #
        # thread = threading.Thread(target=_run)
        # thread.start()
        # self.robot.resume()
        # thread.join(0.5)
        #
        # self.assertEquals(thread.is_alive(), False)
        # self.assertEqual(len(self.robot._commands), 2)
        #
        # self.robot.clear_commands()
        # self.assertEqual(len(self.robot._commands), 0)
        #
        # self.robot.move_to((Deck(), (100, 0, 0)), enqueue=True)
        # self.robot.move_to((Deck(), (101, 0, 0)), enqueue=True)
        #
        # def _run():
        #     self.robot.run()
        #
        # self.robot.pause()
        #
        # thread = threading.Thread(target=_run)
        # thread.start()
        # thread.join(0.01)
        #
        # self.assertEquals(thread.is_alive(), True)
        # self.assertEqual(len(self.robot._commands) > 0, True)
        #
        # self.robot.resume()
        #
        # thread.join(1)
        # self.assertEqual(len(self.robot._commands), 2)

    def test_versions(self):
        res = self.robot.versions()
        expected = {
            'config': {
                'version': 'v2.0.0',
                'compatible': True
            },
            'firmware': {
                'version': self.smoothie_version,
                'compatible': True
            },
            'ot_version': {
                'version': 'one_pro_plus',
                'compatible': True
            }
        }
        self.assertDictEqual(res, expected)

    def test_diagnostics(self):
        res = self.robot.diagnostics()
        expected = {
            'axis_homed': {
                'x': True, 'y': True, 'z': True, 'a': True, 'b': True
            },
            'switches': {
                'x': False,
                'y': False,
                'z': False,
                'a': False,
                'b': False
            },
            'steps_per_mm': {
                'x': 80.0,
                'y': 80.0
            }
        }
        self.assertDictEqual(res, expected)

        self.robot.disconnect()
        self.robot.connect()
        self.assertRaises(RuntimeWarning, self.robot.move_head, x=-199)
        res = self.robot.diagnostics()
        expected = {
            'axis_homed': {
                'x': False, 'y': False, 'z': False, 'a': False, 'b': False
            },
            'switches': {
                'x': True,
                'y': False,
                'z': False,
                'a': False,
                'b': False
            },
            'steps_per_mm': {
                'x': 80.0,
                'y': 80.0
            }
        }
        self.assertDictEqual(res, expected)

        self.robot.home('x', enqueue=False)
        res = self.robot.diagnostics()
        expected = {
            'axis_homed': {
                'x': True, 'y': False, 'z': False, 'a': False, 'b': False
            },
            'switches': {
                'x': False,
                'y': False,
                'z': False,
                'a': False,
                'b': False
            },
            'steps_per_mm': {
                'x': 80.0,
                'y': 80.0
            }
        }
        self.assertDictEqual(res, expected)

    def test_get_motor_caching(self):
        a_motor = self.robot.get_motor('a')
        self.assertEqual(a_motor, self.robot.get_motor('a'))

        b_motor = self.robot.get_motor('b')
        self.assertEqual(b_motor, self.robot.get_motor('b'))

    def test_get_mosfet_caching(self):
        m0 = self.robot.get_mosfet(0)
        self.assertEqual(m0, self.robot.get_mosfet(0))
        m1 = self.robot.get_mosfet(1)
        self.assertEqual(m1, self.robot.get_mosfet(1))
