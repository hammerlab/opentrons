import pytest
from opentrons.robot.robot import Robot

#conf tests look for default fixtures declaration convention

@pytest.fixture
def robot():

    from opentrons import robot
    _robot = Robot()
    print('robot_fixture OLD ROBOT')
    print('robot_fixture - rob_id: ', id(robot))
    print('robot_fixture - pos_tracker: ', id(robot.position_tracker))
    print('pt_len: ', len(robot.position_tracker._position_dict))
    robot.__dict__ = {**_robot.__dict__}
    print('robot_fixture NEW ROBOT')
    print('robot_fixture - rob_id: ', id(robot))
    print('robot_fixture - pos_tracker: ', id(robot.position_tracker))
    print('pt_len: ', len(robot.position_tracker._position_dict))
    # print('_rob_id: ', id(_robot))
    # print('_rob_id_POS: ', id(_robot.position_tracker))

    print("FIXTURE_MAX IN SUB: ", robot.position_tracker.max_z_in_subtree(robot._deck))

    return robot

@pytest.fixture
def message_broker():
    from opentrons.util.trace import MessageBroker
    return MessageBroker()