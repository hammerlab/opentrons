ROBOT_COMMAND = 'robot.command'


# Robot #
def makeRobotActionName(name):
    return '{}.{}'.format(ROBOT_COMMAND, name)

ASPIRATE = makeRobotActionName('ASPIRATE')
DISPENSE = makeRobotActionName('DISPENSE')
CONSOLIDATE = makeRobotActionName('CONSOLIDATE')
DISTRIBUTE = makeRobotActionName('DISTRIBUTE')
TRANSFER = makeRobotActionName('TRANSFER')
PICK_UP_TIP = makeRobotActionName('PICK_UP_TIP')
DROP_TIP = makeRobotActionName('DROP_TIP')
COMMENT = makeRobotActionName('COMMENT')


# State #
STATE_CHANGE = 'session.state.change'
