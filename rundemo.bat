CD /d "%~dp0"

start "NetBot-Server" cmd /K py -3 src/netbots_server.py -p 20000 -stepsec 0.05 -games 10 -stepmax 3000

start "hideincorner" cmd /K py -3 robots/hideincorner.py -p 20002 -sp 20000
start "lighthouse" cmd /K py -3 robots/lighthouse.py -p 20003 -sp 20000
start "scaredycat" cmd /K py -3 robots/scaredycat.py -p 20004 -sp 20000
start "wallbanger" cmd /K py -3 robots/wallbanger.py -p 20005 -sp 20000

start "NetBot-Viewer" cmd /K py -3 src/netbots_viewer.py -p 20001 -sp 20000
