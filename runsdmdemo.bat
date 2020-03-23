CD /d "%~dp0"

start "NetBot-Server" cmd /K py -3 src/netbots_server.py -p 20000 -stepsec 0.001 -games 10 -stepmax 3000 -sdmipc -botdir robots -startbots hideincorner lighthouse scaredycat wallbanger

