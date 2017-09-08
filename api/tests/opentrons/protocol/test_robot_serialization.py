import dill
import unittest

from opentrons import Robot
from opentrons.containers import load as containers_load
from opentrons.instruments import pipette

from tests.opentrons.conftest import patch_robot
from opentrons.broker import subscribe


class RobotSerializationTestCase(unittest.TestCase):
    def setUp(self):
        self.robot = Robot()
        commands = []

        def on_command(name, payload):
            if payload['$'] == 'before':
                commands.append(payload['text'].format(**payload))
        patch_robot(self.robot, commands)
        self.unsubscribe, = subscribe(['robot.command'], on_command)

    def tearDown(self):
        self.unsubscribe()
        del self.robot

    def test_serializing_and_deserializing_unconfigured_robot(self):
        robot_as_bytes = dill.dumps(self.robot)
        self.assertIsInstance(robot_as_bytes, bytes)
        dill.loads(robot_as_bytes)

    def test_serializing_configured_robot(self):
        plate = containers_load(self.robot, '96-flat', 'A1')
        p200 = pipette.Pipette(self.robot, axis='b', max_volume=200)

        for well in plate:
            p200.aspirate(well).delay(5).dispense(well)

        original_robot_cmd_cnts = len(self.robot.commands())
        robot_as_bytes = dill.dumps(self.robot)
        self.assertIsInstance(robot_as_bytes, bytes)
        deserialized_robot = dill.loads(robot_as_bytes)
        deserialized_robot_cmd_cnts = len(deserialized_robot.commands())
        self.assertEqual(deserialized_robot_cmd_cnts, original_robot_cmd_cnts)

        original_robot_instruments = self.robot.get_instruments()
        deserialized_robot_instruments = self.robot.get_instruments()
        self.assertEqual(
            len(original_robot_instruments),
            len(deserialized_robot_instruments),
        )
        self.assertEqual(
            original_robot_instruments[0][0],
            deserialized_robot_instruments[0][0],
        )

    def test_serializing_configured_robot_with_2_instruments(self):
        plate = containers_load(self.robot, '96-flat', 'A1')
        trash = containers_load(self.robot, 'point', 'A2')
        tiprack = containers_load(self.robot, 'tiprack-200ul', 'A3')

        p200 = pipette.Pipette(
            self.robot,
            axis='b',
            tip_racks=[tiprack],
            trash_container=trash,
            max_volume=200
        )
        p100 = pipette.Pipette(
            self.robot,
            axis='a',
            channels=8,
            tip_racks=[tiprack],
            trash_container=trash,
            max_volume=100
        )
        self.make_commands(p200, plate, p100, plate)

        # original_robot_cmds_txt = self.robot.commands()
        original_robot_cmd_cnts = len(self.robot.commands())

        robot_as_bytes = dill.dumps(self.robot)
        self.assertIsInstance(robot_as_bytes, bytes)

        deserialized_robot = dill.loads(robot_as_bytes)
        deserialized_robot_cmd_cnts = len(deserialized_robot.commands())

        # Check commands are unmarshalled
        self.assertEqual(deserialized_robot_cmd_cnts, original_robot_cmd_cnts)

        # Check instruments are unmarshalled
        original_robot_instruments = self.robot.get_instruments()
        deserialized_robot_instruments = self.robot.get_instruments()
        self.assertEqual(
            len(original_robot_instruments),
            len(deserialized_robot_instruments),
        )
        self.assertEqual(
            original_robot_instruments[0][0],
            deserialized_robot_instruments[0][0],
        )

        # Set deserialized robot as the global robot and attempt to
        # reconstruct the same commands again
        r2_p200 = deserialized_robot_instruments[0][1]
        r2_p100 = deserialized_robot_instruments[1][1]
        self.make_commands(r2_p200, plate, r2_p100, plate)
        # self.assertEqual(
        #     original_robot_cmd_cnts,
        #     len(deserialized_robot._commands)
        # )
        # self.assertListEqual(
        #     original_robot_cmds_txt,
        #     deserialized_robot.commands()
        # )

    def make_commands(self, inst1, inst1_plate, inst2, inst2_plate):
        for well in inst1_plate:
            inst1.aspirate(well).delay(5).dispense(well)
        for row in inst2_plate.rows[::-1]:
            inst2.aspirate(row).delay(5).dispense(row)
