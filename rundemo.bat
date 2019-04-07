start "NetBot-Server" cmd /K python src/netbots_server.py -p 20000

start "hideincorner" cmd /K python robots/hideincorner.py -p 20002 -sp 20000
start "lighthouse" cmd /K python robots/lighthouse.py -p 20003 -sp 20000
start "train" cmd /K python robots/train.py -p 20004 -sp 20000
start "wallbanger" cmd /K python robots/wallbanger.py -p 20005 -sp 20000

start "NetBot-Viewer" cmd /K python src/netbots_viewer.py -p 20001 -sp 20000