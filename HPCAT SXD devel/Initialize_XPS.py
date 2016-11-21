import XPS_Q8_drivers

myxps = XPS_Q8_drivers.XPS()
socketId = myxps.TCP_ConnectToServer('164.54.164.46', 5001, 20)
print socketId
group = 'M'
trajectory = 'testfast.trj'

preflight = myxps.MultipleAxesPVTVerification(socketId, group, trajectory)
print preflight[0]
if not preflight[0] == 0:
    print 'This is some crazy trj you wanna do'
else:
    myxps.MultipleAxesPVTExecution(socketId, group, trajectory, 1)
myxps.TCP_CloseSocket(socketId)
raw_input('Press Enter to close this program')
