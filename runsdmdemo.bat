CD /d "%~dp0"

start "NetBot-Server" cmd /K py -3 src/netbots_server.py -p 20000 -stepsec 0.05 -games 10 -stepmax 3000 -sdmipc -botdir robots -startbots hideincorner lighthouse scaredycat wallbanger

start "NetBot-Viewer" cmd /K py -3 src/netbots_viewer.py -p 20001 -sp 20000
