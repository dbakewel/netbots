CD /d "%~dp0"

start "NetBot-Server" cmd /K py -3 src/netbots_server.py -p 20000 -stepsec 0.05 -games 10 -stepmax 3000 -sdmipc -startviewer -botdir robots -startbots hideincorner lighthouse scaredycat wallbanger

