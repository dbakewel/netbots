# Ahoy! It's a "warship"

import os
import sys
import argparse
import time
import signal
import math
import random
import threading
from queue import Queue

import bot_controller as botctrl

#include the netbot src directory in sys.path so we can import modules from it.
robotpath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(os.path.dirname(robotpath),"src")
sys.path.insert(0,srcpath)

from netbots_log import log
from netbots_log import setLogLevel
import netbots_ipc as nbipc
import netbots_math as nbmath

# whether a given key is pressed
# capitalized because tkinter keyboard keys are capitalized
keysDown = {"Up": False, "Down": False, "Left": False, "Right": False}

robotName = "HMCS Victoria"

# following are also set in arguments
upKey = "Up"
downKey = "Down"
leftKey = "Left"
rightKey = "Right"
steering = True

controller = None  # controller window/viewer

# basically snagged both these off here:
# https://stackoverflow.com/questions/21440731/tkinter-getting-key-pressed-event-from-a-function
# as answered by "User"
def keyPressHandler(event):
    global keysDown;
    sym = event.keysym
    if(sym == upKey):
        keysDown["Up"] = True
        keysDown["Down"] = False
    elif(sym == downKey):
        keysDown["Down"] = True
        keysDown["Up"] = False
    
    if(sym == leftKey):
        keysDown["Left"] = True
        keysDown["Right"] = False
    elif(sym == rightKey):
        keysDown["Right"] = True
        keysDown["Left"] = False

def keyReleaseHandler(event):
    global keysDown;

    sym = event.keysym
    if(sym == upKey):
        keysDown["Up"] = False
    elif(sym == downKey):
        keysDown["Down"] = False
    
    if(sym == leftKey):
        keysDown["Left"] = False
    elif(sym == rightKey):
        keysDown["Right"] = False

# mouse handler inside play for... reasons


def play(botSocket, srvConf, q):
    arenaSize = srvConf["arenaSize"]
    gameNumber = 0        #The last game number bot got from the server (0 == no game has been started)
    getLocationReply = {"x": 0, "y": 0}
    mouseDown = False
    mousePos = {"x": 0, "y": 0}
    waiting = True  # whether to wait for shell to explode
    firing_distance = 0
    shell_time = 0
    global keysDown
    global steering


    def shoot():
        nonlocal mousePos

        angle = nbmath.angle(getLocationReply["x"], getLocationReply["y"],
                mousePos["x"], mousePos["y"])
        dist = nbmath.distance(getLocationReply["x"], getLocationReply["y"],
                mousePos["x"], mousePos["y"])
        botSocket.sendMessage({"type": "fireCanonRequest",
                "direction": angle, "distance": dist})
        
        shell_time = time.perf_counter()
        firing_distance = dist
    
    # log the keys being used
    log("The up key is " + str(upKey), "INFO")
    log("The down key is " + str(downKey), "INFO")
    log("The left key is " + str(leftKey), "INFO")
    log("The right key is " + str(rightKey), "INFO")

    # log the current movement mode
    if(steering):
        log("Steering. Use left and right keys to steer, and up and down to " +
                "control speed.", "INFO")
    else:
        log("Directional movement. Bot will go in direction of keys pressed.", "INFO")

    while True:
        try:
            #Get information to determine if bot is alive (health > 0) and if a new game has started.
            getInfoReply = botSocket.sendRecvMessage({'type': 'getInfoRequest'})
        except nbipc.NetBotSocketException as e:
            #We are always allowed to make getInfoRequests, even if our health == 0. Something serious has gone wrong.
            log(str(e),"FAILURE")
            log("Is netbot server still running?")
            quit()

        if getInfoReply['health'] == 0:
            #we are dead, there is nothing we can do until we are alive again.
            continue

        if getInfoReply['gameNumber'] != gameNumber:
            #A new game has started. Record new gameNumber and reset any variables back to their initial state
            gameNumber = getInfoReply['gameNumber']
            log("Game " + str(gameNumber) + " has started. Points so far = " + str(getInfoReply['points']))

            # Reset variables
            keysDown["Up"] = False
            keysDown["Down"] = False
            keysDown["Left"] = False
            keysDown["Right"] = False
            mouseDown = False
            waiting = True

        try:
            getLocationReply = botSocket.sendRecvMessage({"type": "getLocationRequest"})
            getSpeedReply = botSocket.sendRecvMessage({"type": "getSpeedRequest"})
            radians = 0
            requestedSpeed = getSpeedReply["currentSpeed"] # will add to later
            
            
            # check for shots using a queue (good asynchronous/threading practice)
            # hey wait why is this a queue but key-presses aren't?? MARTIN!
            while not q.empty():
                nextData = q.get()
                if("mousePos" in nextData):
                    mousePos = nextData["mousePos"]
                elif("mouseDown" in nextData):
                    mouseDown = nextData["mouseDown"]
                    
                    # force a shot on click to emulate old behaviour for
                    # those who thoroughly enjoyed clicking to shoot
                    if(mouseDown == True):
                        shoot()
                        waiting = True
                    else:
                        waiting = False
                else:
                    # no I don't feel like ending the program today
                    log("Unexpected index name in q: " + str(q), "WARNING")
                q.task_done()
                

            # bot steers left and right, and up and down control speed
            if(steering):
                currAngle = botSocket.sendRecvMessage({"type": "getDirectionRequest"})

                radians = currAngle["currentDirection"] # will add to later

                # steer
                if(keysDown["Left"]):
                    radians += 1  # ~pi/3 radians or ~60
                    radians = nbmath.normalizeAngle(radians)
                elif(keysDown["Right"]):
                    radians -= 1
                    radians = nbmath.normalizeAngle(radians)
                
                # speed up
                if(keysDown["Up"]):
                    requestedSpeed = 100
                        
                # slow down
                elif(keysDown["Down"]):
                    requestedSpeed = 0
                
            # bot moves in direction of arrow keys
            else:
                xDir = 0
                yDir = 0

                if(keysDown["Left"]):
                    xDir = -1
                elif(keysDown["Right"]):
                    xDir = 1
                else:
                    xDir = 0

                if(keysDown["Up"]):
                    yDir = 1
                elif(keysDown["Down"]):
                    yDir = -1
                else:
                    yDir = 0

                if(xDir == 0 and yDir == 0):
                    requestedSpeed = 0
                else:
                    radians = nbmath.normalizeAngle(math.atan2(yDir, xDir))
                    requestedSpeed = 50

            botSocket.sendMessage({"type": "setDirectionRequest", "requestedDirection": radians})
            botSocket.sendMessage({"type": "setSpeedRequest", "requestedSpeed": requestedSpeed})

            # wait until shell explodes before shooting again, or if player clicks again
            if(mouseDown):
                if(waiting):
                    if firing_distance - (time.perf_counter() - shell_time) / srvConf['stepSec'] * srvConf['shellSpeed'] <= 0:
                        waiting = False

                if(not waiting):
                    waiting = True
                    shoot()
        except nbipc.NetBotSocketException as e:
            #Consider this a warning here. It may simply be that a request returned 
            #an Error reply because our health == 0 since we last checked. We can 
            #continue until the next game starts.
            log(str(e),"WARNING")
            continue

##################################################################
### Standard stuff below.
##################################################################

def quit(signal=None, frame=None):
    global botSocket
    log(botSocket.getStats())
    log("Quiting","INFO")
    exit()

def main():
    q = Queue()  # mouse event queue
    arenaSize = 0
    mouseDown = False # whether mouse button is pressed
    waiting = False   # whether waiting for explosion
    global botSocket  # This is global so quit() can print stats in botSocket
    global robotName
    global upKey
    global downKey
    global leftKey
    global rightKey
    global steering
    global controller
    
    # mmmmmm closure why do I do this?
    def mousePressHandler(event):
        nonlocal q
        nonlocal arenaSize
        nonlocal mouseDown
        nonlocal waiting
        global controller
        mousePos = {"x": 0, "y": 0}
        
        mouseDown = True

        # event.x and event.y are in canvas coordinates, which are from
        # the top left corner and are in terms of the canvas size. We want
        # a location within arenaSize
        ratio = arenaSize / controller.canvas.winfo_width()
        
        mousePos["x"] = event.x * ratio
        
        # TOP left corner, remember?
        mousePos["y"] = (controller.canvas.winfo_width() - event.y) * ratio
        
        q.put({"mousePos": mousePos})
        q.put({"mouseDown": True}) # put this after or weird things happen

    def mouseMoveHandler(event):
        nonlocal arenaSize
        nonlocal mouseDown
        global controller
        mousePos = {"x": 0, "y": 0}
        
        if(mouseDown):
            canvasSize = controller.canvas.winfo_width()
            ratio = arenaSize / canvasSize
            mousePos["x"] = event.x * ratio
            mousePos["y"] = (canvasSize - event.y) * ratio
            q.put({"mousePos": mousePos})

    def mouseReleaseHandler(event):
        nonlocal mouseDown
        
        mouseDown = False
        q.put({"mouseDown": False})

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-ip', metavar='My IP', dest='myIP', type=nbipc.argParseCheckIPFormat, nargs='?', default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='My Port', dest='myPort', type=int, nargs='?', default=20010, help='My port number')
    parser.add_argument('-sip', metavar='Server IP', dest='serverIP', type=nbipc.argParseCheckIPFormat, nargs='?', default='127.0.0.1', help='Server IP Address')
    parser.add_argument('-sp', metavar='Server Port',dest='serverPort', type=int, nargs='?', default=20000, help='Server port number')
    parser.add_argument('-debug', dest='debug', action='store_true', default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true', default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    parser.add_argument("-vp", metavar = "Viewer/Controller Port", dest = "viewerPort", type = int,
            nargs = "?", default = 20018, help = "Viewer/Controller port number")
    
    # account for movement keys
    parser.add_argument("-up", metavar = "Up Key", dest = "upKey", type = str, nargs = "?",
            default="Up", help = "Up movement key")
    parser.add_argument("-down", metavar = "Down Key", dest = "downKey", type = str, nargs = "?",
            default="Down", help = "Down movement key")
    parser.add_argument("-left", metavar = "Left Key", dest = "leftKey", type = str, nargs = "?",
            default="Left", help = "Left movement key")
    parser.add_argument("-right", metavar = "Right Key", dest = "rightKey", type = str, nargs = "?",
            default="Right", help = "Right movement key")

    # determine whether should use directional movement or steering
    parser.add_argument('-directional', dest='directional', action='store_true',
            default=False, help='Use directional movement instead of steering')
    
    args = parser.parse_args()
    setLogLevel(args.debug, args.verbose)
    
    upKey = args.upKey
    downKey = args.downKey
    leftKey = args.leftKey
    rightKey = args.rightKey
    if(args.directional):
        steering = False

    try:
        botSocket = nbipc.NetBotSocket(args.myIP, args.myPort, args.serverIP, args.serverPort)
        joinReply = botSocket.sendRecvMessage({'type': 'joinRequest', 'name': robotName})
    except nbipc.NetBotSocketException as e:
        log("Is netbot server running at" + args.serverIP + ":" + str(args.serverPort) + "?")
        log(str(e),"FAILURE")
        quit()

    log("Join server was successful. We are ready to play!")

    #the server configuration tells us all about how big the arena is and other useful stuff.
    srvConf = joinReply['conf']
    log(str(srvConf), "VERBOSE")

    # controller is a viewer that needs information: but the IP and port
    # info must NOT BE THE SAME as the bot's, otherwise the server will boot us
    controller = botctrl.createController(args.myIP, args.viewerPort, args.serverIP, args.serverPort)

    # Don't snitch to Ms. Wear that I didn't use proper encapsulation
    controller.window.title("NetBots (Controlling " + robotName + ")")
    
    # set key handling functions
    controller.setKeyPressHandler(keyPressHandler)
    controller.setKeyReleaseHandler(keyReleaseHandler)
    arenaSize = srvConf["arenaSize"]
    controller.setMousePressHandler(mousePressHandler)
    controller.setMouseMoveHandler(mouseMoveHandler)
    controller.setMouseReleaseHandler(mouseReleaseHandler)

    #Now we can play, but we may have to wait for a game to start.
    playThread = threading.Thread(target = play, args = (botSocket, srvConf, q))
    playThread.start()

    # start updating window
    # use controller.window.mainloop() for a simpler click to shoot, and no dir lines
    # otherwise you probably want something like:
    # while(playThread.is_alive()):
    #     # optional: dir line should go here
    #     controller.window.update()
    controller.window.mainloop()

    # I have no idea what happens here. I think this is what you do...
    playThread.join()
    controller.window.destroy()

if __name__ == "__main__":
    # execute only if run as a script
    signal.signal(signal.SIGINT, quit)
    main()
