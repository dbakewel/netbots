CD /d "%~dp0"

start "NetBot-Server" cmd /K py -3 src/netbots_server.py -p 20000 -stepsec 0.05 -games 10 -stepmax 3000

start "hideincorner" cmd /K py -3 robots/hideincorner.py -p 20002 -sp 20000
start "lighthouse" cmd /K py -3 robots/lighthouse.py -p 20003 -sp 20000

REM team will use port 20004 and 20005 (20004+1)
start "team" cmd /K py -3 robots/team.py -p 20004 -sp 20000

start "NetBot-Viewer" cmd /K py -3 src/netbots_viewer.py -p 20001 -sp 20000