import XPS_Q8_drivers

myxps = XPS_Q8_drivers.XPS()

socketId = myxps.TCP_ConnectToServer('164.54.164.104', 5001, 20)
# ###print socketId
# ###group = 'Group3'
# ###positioner = group + '.Pos'
# ###print positioner
# ###ec, cp = myxps.GroupPositionCurrentGet(socketId, positioner, 1)
# ###print ec, cp
# ###myxps.GPIODigitalSet(socketId, 'GPIO3.DO', 1, 1)
# ###print myxps.GPIODigitalGet(socketId, 'GPIO3.DO')
# ###myxps.GPIODigitalSet(socketId, 'GPIO3.DO', 2, 1)
# ###print myxps.GPIODigitalGet(socketId, 'GPIO3.DO')
# ###myxps.GPIODigitalSet(socketId, 'GPIO3.DO', 1, 0)
# ###print myxps.GPIODigitalGet(socketId, 'GPIO3.DO')
myxps.EventExtendedConfigurationTriggerSet(socketId, ('Always', 'Group4.Pos.SGamma.MotionStart'), ('0','0'), ('0','0'), ('0','0'), ('0','0'))
myxps.EventExtendedConfigurationActionSet(socketId, ['GPIO3.DO.DOSet'], '1', '1', '0', '0')
myxps.EventExtendedStart(socketId)
myxps.TCP_CloseSocket(socketId)
