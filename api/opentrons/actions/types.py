def makeRobotActionName(name):
    return 'robot.command'  # .' + name

ASPIRATE = makeRobotActionName('ASPIRATE')
DISPENSE = makeRobotActionName('DISPENSE')
CONSOLIDATE = makeRobotActionName('CONSOLIDATE')
DISTRIBUTE = makeRobotActionName('DISTRIBUTE')
TRANSFER = makeRobotActionName('TRANSFER')
PICK_UP_TIP = makeRobotActionName('PICK_UP_TIP')
DROP_TIP = makeRobotActionName('DROP_TIP')
COMMENT = makeRobotActionName('COMMENT')
