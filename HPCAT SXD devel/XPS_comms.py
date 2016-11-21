import XPS_Q8_drivers

myxps = XPS_Q8_drivers.XPS()

socketId = myxps.TCP_ConnectToServer('164.54.164.46', 5001, 20)
print socketId
group = 'M'
positioner = group + '.X'
print positioner
ec, cp = myxps.GroupPositionCurrentGet(socketId, positioner, 1)
print ec, cp
status = myxps.GroupStatusGet(socketId, 'M')
print status
if 9 < status[1] < 20:
    print 'okay'
else:
    print 'trouble'
    kill = myxps.GroupKill(socketId, group)
    print kill
    initialize = myxps.GroupInitialize(socketId, group)
    print initialize
    home = myxps.GroupHomeSearch(socketId, group)
    print home
    move = myxps.GroupMoveAbsolute(socketId, group, [1.000])
    print move
    # enable = myxps.GroupMotionEnable(socketId, group)
    # print enable
myxps.TCP_CloseSocket(socketId)
