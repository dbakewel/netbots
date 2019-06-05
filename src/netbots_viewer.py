import argparse
import time
import signal
import tkinter as t
import random
import math

from netbots_log import log
from netbots_log import setLogLevel
from netbots_server import SrvData
import netbots_ipc as nbipc
import netbots_math as nbmath


class ViewerData():
    viewerSocket = None

    window = None
    frame = None
    statusWidget = None
    replayWidget = None
    canvas = None
    botWidgets = {}
    botCurrentDirection = {}
    botRequestedDirection = {}
    botCanon = {}
    botTrackLeft = {}
    botTrackRight = {}
    botScan = {}
    botStatusWidgets = {}
    shellWidgets = {}
    explWidgets = {}
    bigMsg = None
    colors = ['#ACACAC','#87FFCD','#9471FF','#FF9DB6','#2ED2EB','#FA8737','#29B548','#FFBC16','#308AFF','#FF3837']
    lastViewData = time.time()
    scale = 1

    borderSize = 10

    nextKeepAlive = time.time() + 2
    srvIP = None
    srvPort = None
    conf = None
    
    replayData = []
    playingData = []
    isReplaying = False
    toggleReplaying = False
    replaySec = 7
    replayStepSec = 0.05
    replaySaveEveryNth = 1
    replaySaveSteps = math.ceil(replaySec / replayStepSec)


def colorVariant(hexColor, brightnessOffset=1):
    """ takes a color like #87c95f and produces a lighter or darker variant """
    if len(hexColor) != 7:
        raise Exception("Passed %s into colorVariant(), needs to be in #87c95f format." % hexColor)
    rgbHex = [hexColor[x:x+2] for x in [1, 3, 5]]
    newRGBInt = [int(hexValue, 16) + brightnessOffset for hexValue in rgbHex]
    newRGBInt = [min([255, max([0, i])]) for i in newRGBInt] # make sure new values are between 0 and 255
    
    hexstr = "#"
    for i in newRGBInt:
        if i < 16:
            hexstr += "0"
        # hex() produces "0x88" or "0x8", we want just "88" or "8"
        hexstr += hex(i)[2:]
    return hexstr

def checkForUpdates(d):
    msg = {"type": "Error", "result": "We never got any new data from server."}
    try:
        # keep getting messages until we get the last one and then an exception is thrown.
        while True:
            msg, ip, port = d.viewerSocket.recvMessage()
            
            d.replayData.append(msg)
            while len(d.replayData) > d.replaySaveSteps / d.replaySaveEveryNth:
                d.replayData.pop(0)
    except nbipc.NetBotSocketException as e:
        # if message type is Error and we have not got good data for 100 steps then quit
        if msg['type'] == 'Error' and d.lastViewData + d.conf['stepSec'] * 100 < time.time():
            # We didn't get anything from the buffer or it was an invalid message.
            d.canvas.itemconfigure(d.bigMsg, text="Server stopped sending data.")
    except Exception as e:
        log(str(e), "ERROR")
        quit()

    if msg['type'] == 'viewData':
        
        # turn replay on or off if space bar pressed
        if d.toggleReplaying:
            if d.isReplaying:
                d.playingData = []
                d.toggleReplaying = False
                d.isReplaying = False
            else:
                d.playingData = []
                d.playingData.extend(d.replayData)
                d.toggleReplaying = False
                d.isReplaying = True

        # play back and then remove data
        if d.isReplaying:
            if len(d.playingData) > 0:
                msg = d.playingData[0]
                d.playingData.pop(0)

            # replay is over
            else:
                d.isReplaying = False

        # draw red border on arena and red instant replay widget
        if d.isReplaying:
            d.canvas.config(highlightbackground='#FF0000')

            if d.replayWidget is None:
                d.replayWidget = t.Message(d.frame, width=200, justify='center')
                d.replayWidget.config(highlightbackground='#FF0000')
                d.replayWidget.config(highlightthickness=d.borderSize)
                d.replayWidget.pack(fill=t.X)
                d.replayWidget.config(text="Instant Replay!")

        else:
            d.canvas.config(highlightbackground='#000')

            if d.replayWidget is not None:
                d.replayWidget.destroy()
                d.replayWidget = None
                
        # if gameNumber == 0 then post message
        if msg['state']['gameNumber'] == 0:
            leftToJoin = d.conf['botsInGame'] - len(msg['bots'])
            if leftToJoin == 1:
                s = ""
            else:
                s = "s"
            d.canvas.itemconfigure(d.bigMsg, text="Waiting for " +
                                   str(leftToJoin) +
                                   " robot" + s + " to join.")
        else:
            d.canvas.itemconfigure(d.bigMsg, text="")

        for src, bot in msg['bots'].items():
            # ensure all bots on server have widgets
            if not src in d.botStatusWidgets:
                # pick color for this bot
                c = d.colors.pop()

                # create bot status widget
                d.botStatusWidgets[src] = t.Message(d.frame, width=200, justify='center')
                d.botStatusWidgets[src].config(highlightbackground=c)
                d.botStatusWidgets[src].config(highlightthickness=d.borderSize)
                d.botStatusWidgets[src].pack(fill=t.X)

                # create bot widgets
                d.botScan[src] = d.canvas.create_arc(0, 0, 50, 50, start=0, extent=0,
                             style='arc', width=4, outline='#bbb')
                d.botTrackLeft[src] = d.canvas.create_line(0, 0, 50, 50, width=
                    d.conf['botRadius'] * (10 / 24.0), fill='grey')
                d.botTrackRight[src] = d.canvas.create_line(0, 0, 50, 50, width=
                    d.conf['botRadius'] * (10 / 24.0), fill='grey')
                d.botWidgets[src] = d.canvas.create_oval(0, 0, 0, 0, fill=c)
                d.botCanon[src] = d.canvas.create_line(0, 0, 50, 50, width=
                    d.conf['botRadius'] * (1/3.0), fill=c)
                d.botRequestedDirection[src] = d.canvas.create_line(0, 0, 50, 50, width=
                    d.conf['botRadius'] * (5 / 24.0), arrow=t.LAST, fill=colorVariant(c,-100))
                d.botCurrentDirection[src] = d.canvas.create_line(0, 0, 50, 50, width=
                    d.conf['botRadius'] * (5 / 24.0), arrow=t.LAST, fill=colorVariant(c,100))

            # update text for each bot
            d.botStatusWidgets[src].config(text=bot['name'] +
                                           "\n" + "__________________________________" +
                                           "\nPoints: " + str(bot['points']) +
                                           "\nCanon Fired: " + str(bot['firedCount']) +
                                           "\nShell Damage Inflicted: " + '%.1f' % (bot['shellDamage']) +
                                           "\n" + "__________________________________" +
                                           "\nHealth: " + '%.1f' % (bot['health']) + "%"
                                           "   Speed: " + '%.1f' % (bot['currentSpeed']) + "%")

            # update location of bot widgets or hide if health == 0
            if bot['health'] == 0:
                d.canvas.itemconfigure(d.botWidgets[src], state='hidden')
                d.canvas.itemconfigure(d.botRequestedDirection[src], state='hidden')
                d.canvas.itemconfigure(d.botCurrentDirection[src], state='hidden')
                d.canvas.itemconfigure(d.botTrackLeft[src], state='hidden')
                d.canvas.itemconfigure(d.botTrackRight[src], state='hidden')
                d.canvas.itemconfigure(d.botScan[src], state='hidden')
                d.canvas.itemconfigure(d.botCanon[src], state='hidden')
            else:
                centerX = bot['x'] * d.scale + d.borderSize
                centerY = d.conf['arenaSize'] - bot['y'] * d.scale + d.borderSize
                d.canvas.coords(d.botWidgets[src],
                                centerX - d.conf['botRadius'],
                                centerY - d.conf['botRadius'],
                                centerX + d.conf['botRadius'],
                                centerY + d.conf['botRadius'])

                d.canvas.coords(d.botRequestedDirection[src], centerX + d.conf['botRadius'] * (19.0 / 24.0)
                                * math.cos(-bot['requestedDirection']),  # 19
                                centerY + d.conf['botRadius'] * (19.0 / 24.0) * math.sin(
                                    -bot['requestedDirection']),
                                d.conf['botRadius'] * math.cos(-bot['requestedDirection']) + centerX,  # 24
                                d.conf['botRadius'] * math.sin(-bot['requestedDirection']) + centerY)

                d.canvas.coords(d.botCurrentDirection[src], centerX + d.conf['botRadius'] * (19.0 / 24.0)
                                * math.cos(-bot['currentDirection']),  # 19
                                centerY + d.conf['botRadius'] * (19.0 / 24.0) * math.sin(
                                    -bot['currentDirection']),
                                d.conf['botRadius'] * math.cos(-bot['currentDirection']) + centerX,  # 24
                                d.conf['botRadius'] * math.sin(-bot['currentDirection']) + centerY)

                d.canvas.coords(d.botTrackLeft[src],
                                centerX + d.conf['botRadius'] * (30.0 / 24.0)
                                * math.cos(-bot['currentDirection'] - math.pi / 4),
                                centerY + d.conf['botRadius'] * (30.0 / 24.0)
                                * math.sin(-bot['currentDirection'] - math.pi / 4),
                                d.conf['botRadius'] * (30.0 / 24.0) * math.cos(-bot['currentDirection']
                                                                                         - (3 * math.pi) / 4) + centerX,
                                d.conf['botRadius'] * (30.0 / 24.0) * math.sin(-bot['currentDirection']
                                                                                         - (3 * math.pi) / 4) + centerY)
                d.canvas.coords(d.botTrackRight[src],
                                centerX + d.conf['botRadius'] * (30.0 / 24.0)
                                * math.cos(-bot['currentDirection'] - (5 * math.pi) / 4),
                                centerY + d.conf['botRadius'] * (30.0 / 24.0)
                                * math.sin(-bot['currentDirection'] - (5 * math.pi) / 4),
                                d.conf['botRadius'] * (30.0 / 24.0)
                                * math.cos(-bot['currentDirection'] - (7 * math.pi) / 4) + centerX,
                                d.conf['botRadius'] * (30.0 / 24.0)
                                * math.sin(-bot['currentDirection'] - (7 * math.pi) / 4) + centerY)

                x2, y2 = nbmath.project(centerX, 0, bot['last']['fireCanonRequest']['direction'], 
                    d.conf['botRadius'] * 1.35)
                y2 = centerY - y2
                d.canvas.coords(d.botCanon[src], centerX, centerY, x2, y2)

                d.canvas.coords(d.botScan[src],
                                centerX - d.conf['botRadius'] * 1.5,
                                centerY - d.conf['botRadius'] * 1.5,
                                centerX + d.conf['botRadius'] * 1.5,
                                centerY + d.conf['botRadius'] * 1.5)
                d.canvas.itemconfigure(d.botScan[src], start=math.degrees(bot['last']['scanRequest']['startRadians']))
                extent = bot['last']['scanRequest']['endRadians'] - bot['last']['scanRequest']['startRadians']
                if extent < 0:
                    extent += math.pi*2
                d.canvas.itemconfigure(d.botScan[src], extent=math.degrees(extent))

                d.canvas.itemconfigure(d.botRequestedDirection[src], state='normal')
                d.canvas.itemconfigure(d.botCurrentDirection[src], state='normal')
                d.canvas.itemconfigure(d.botWidgets[src], state='normal')
                d.canvas.itemconfigure(d.botTrackLeft[src], state='normal')
                d.canvas.itemconfigure(d.botTrackRight[src], state='normal')
                d.canvas.itemconfigure(d.botScan[src], state='normal')
                d.canvas.itemconfigure(d.botCanon[src], state='normal')

        # remove shell widgets veiwer has but are not on server.
        for src in list(d.shellWidgets.keys()):
            if not src in msg['shells']:
                d.canvas.delete(d.shellWidgets[src][1])
                d.canvas.delete(d.shellWidgets[src][0])
                del d.shellWidgets[src]

        # add shell widgets server has that viewer doesn't
        for src in msg['shells']:
            if not src in d.shellWidgets:
                c = d.canvas.itemcget(d.botWidgets[src], 'fill')
                d.shellWidgets[src] = [
                    d.canvas.create_line(0, 0, 0, 0, width=2, arrow=t.LAST, fill=c),
                    d.canvas.create_line(0, 0, 0, 0, width=2, fill=c)
                    ]

        # update location of shell widgets
        for src in d.shellWidgets:
            centerX = msg['shells'][src]['x'] * d.scale + d.borderSize
            centerY = d.conf['arenaSize'] - msg['shells'][src]['y'] * d.scale + d.borderSize
            shellDir = msg['shells'][src]['direction']
            shell_item_1 = d.shellWidgets[src][0]
            d.canvas.coords(shell_item_1, centerX, centerY,
                            d.scale * 1 * math.cos(-shellDir) + centerX,
                            d.scale * 1 * math.sin(-shellDir) + centerY)
            shell_item_2 = d.shellWidgets[src][1]
            d.canvas.coords(shell_item_2, centerX, centerY,
                            d.scale * 10 * math.cos(-shellDir) + centerX,
                            d.scale * 10 * math.sin(-shellDir) + centerY)

        # remove explosion widgets viewer has but are not on server.
        for k in list(d.explWidgets.keys()):
            if not k in msg['explosions']:
                d.canvas.delete(d.explWidgets[k])
                del d.explWidgets[k]

        # reduce existing explosion size by 30% and turn off fill
        for k in d.explWidgets:
            bbox = d.canvas.bbox(d.explWidgets[k])
            d.canvas.coords(d.explWidgets[k],
                            bbox[0] + (bbox[2] - bbox[0]) * 0.85,
                            bbox[1] + (bbox[3] - bbox[1]) * 0.85,
                            bbox[2] - (bbox[2] - bbox[0]) * 0.85,
                            bbox[3] - (bbox[3] - bbox[1]) * 0.85)
            d.canvas.itemconfig(d.explWidgets[k], fill='')

        # add explosion widgets server has that viewer doesn't
        for k, expl in msg['explosions'].items():
            if not k in d.explWidgets:
                c = d.canvas.itemcget(d.botWidgets[expl['src']], 'fill')
                centerX = expl['x'] * d.scale + d.borderSize
                centerY = d.conf['arenaSize'] - expl['y'] * d.scale + d.borderSize
                explRadius = SrvData.getClassValue(d, 'explRadius', msg['bots'][expl['src']]['class'])
                d.explWidgets[k] = d.canvas.create_oval(centerX - explRadius,
                                                        centerY - explRadius,
                                                        centerX + explRadius,
                                                        centerY + explRadius,
                                                        fill=c, width=3, outline=c)

        # update game status widget
        d.statusWidget.config(text=d.conf['serverName'] +
                              "\n\nGame: " + str(msg['state']['gameNumber']) + " / " + str(d.conf['gamesToPlay']) +
                              "\nStep: " + str(msg['state']['gameStep']) + " / " + str(d.conf['stepMax']))

        # record the last time we got good view data from server.
        d.lastViewData = time.time()

    # server needs 1 every 10 seconds to keep us alive. Send every 2 secs to be sure.
    if time.time() > d.nextKeepAlive:
        d.viewerSocket.sendMessage({'type': 'viewKeepAlive'}, d.srvIP, d.srvPort)
        d.nextKeepAlive += 1

    # wait during instant replay
    if d.isReplaying:
        # Wait two steps before updating screen.
        wakeat = int(d.replayStepSec * d.replaySaveEveryNth * 1000)

    # normal wait
    else:
        # Wait two steps before updating screen.
        wakeat = int(d.conf['stepSec'] * 1000)

    d.window.after(wakeat, checkForUpdates, d)


def openWindow(d):
    d.window = t.Tk()
    d.window.title("NetBots")
    
    d.window.bind_all("<KeyPress>", keyPressHandler)

    if d.window.winfo_screenheight() < d.conf['arenaSize'] + 100 + d.borderSize * 2:
        d.scale = d.window.winfo_screenheight() / float(d.conf['arenaSize'] + 100 + d.borderSize * 2)
        d.conf['arenaSize'] *= d.scale
        d.conf['botRadius'] *= d.scale
        d.conf['explRadius'] *= d.scale
        log("Window scale set to : " + str(d.scale))

    d.canvas = t.Canvas(d.window, width=d.conf['arenaSize'], height=d.conf['arenaSize'], bg='#ddd')
    d.canvas.config(highlightbackground='#000')
    d.canvas.config(highlightthickness=d.borderSize)
    d.canvas.pack(side=t.LEFT)

    lineAt = d.borderSize + d.conf['arenaSize'] / 40
    while lineAt < d.conf['arenaSize'] + d.borderSize:
        d.canvas.create_line(d.borderSize, lineAt, d.conf['arenaSize'] + d.borderSize, lineAt, width=1, fill="#cecece")
        d.canvas.create_line(lineAt, d.borderSize, lineAt, d.conf['arenaSize'] + d.borderSize, width=1, fill="#cecece")
        lineAt += d.conf['arenaSize'] / 40

    lineAt = d.borderSize + d.conf['arenaSize'] / 10
    while lineAt < d.conf['arenaSize'] + d.borderSize:
        d.canvas.create_line(d.borderSize, lineAt, d.conf['arenaSize'] + d.borderSize, lineAt, width=2, fill="#c0c0c0")
        d.canvas.create_line(lineAt, d.borderSize, lineAt, d.conf['arenaSize'] + d.borderSize, width=2, fill="#c0c0c0")
        lineAt += d.conf['arenaSize'] / 10

    for o in d.conf['jamZones']:
        centerX = o['x'] * d.scale + d.borderSize
        centerY = d.conf['arenaSize'] - o['y'] * d.scale + d.borderSize
        radius = o['radius'] * d.scale
        d.canvas.create_oval(centerX - radius,
                             centerY - radius,
                             centerX + radius,
                             centerY + radius,
                             fill='#ddd', outline='#c0c0c0', width=2)

    for o in d.conf['obstacles']:
        centerX = o['x'] * d.scale + d.borderSize
        centerY = d.conf['arenaSize'] - o['y'] * d.scale + d.borderSize
        radius = o['radius'] * d.scale
        d.canvas.create_oval(centerX - radius,
                             centerY - radius,
                             centerX + radius,
                             centerY + radius,
                             fill='black')

    d.bigMsg = canvasText = d.canvas.create_text(d.conf['arenaSize'] / 2 + d.borderSize,
                                                 d.conf['arenaSize'] / 2 + d.borderSize,
                                                 fill="darkblue",
                                                 font="Times 20 italic bold",
                                                 text="")

    d.frame = t.Frame(d.window, width=200, height=1020, bg='#888')
    d.frame.pack(side=t.RIGHT)

    d.statusWidget = t.Message(d.frame, width=200, justify='center')
    d.statusWidget.config(highlightbackground='#000')
    d.statusWidget.config(highlightthickness=d.borderSize)
    d.statusWidget.pack(fill=t.X)

    d.lastViewData = time.time()
    checkForUpdates(d)
    t.mainloop()

    
def keyPressHandler(event):
    global d

    sym = event.keysym

    if sym == "space":
        d.toggleReplaying = True

def quit(signal=None, frame=None):
    log("Quiting", "INFO")
    exit()


def main():
    global d
    
    d = ViewerData()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                    epilog="Note: pressing the space bar activates a 7 second long instant replay at the default step speed. "
                                     + "Live action will resume after the replay completes.")
    parser.add_argument('-ip', metavar='My IP', dest='myIP', type=nbipc.argParseCheckIPFormat, nargs='?',
                        default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='My Port', dest='myPort', type=int, nargs='?',
                        default=20010, help='My port number')
    parser.add_argument('-sip', metavar='Server IP', dest='serverIP', type=nbipc.argParseCheckIPFormat, nargs='?',
                        default='127.0.0.1', help='Server IP Address')
    parser.add_argument('-sp', metavar='Server Port', dest='serverPort', type=int, nargs='?',
                        default=20000, help='Server port number')
    parser.add_argument('-randcolors', dest='randomColors', action='store_true',
                        default=False, help='Randomizes bot colors in viewer')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    args = parser.parse_args()
    setLogLevel(args.debug, args.verbose)
    d.srvIP = args.serverIP
    d.srvPort = args.serverPort

    log("Registering with Server: " + d.srvIP + ":" + str(d.srvPort))

    try:
        d.viewerSocket = nbipc.NetBotSocket(args.myIP, args.myPort, d.srvIP, d.srvPort)
        reply = d.viewerSocket.sendRecvMessage({'type': 'addViewerRequest'}, retries=60, delay=1, delayMultiplier=1)
        d.conf = reply['conf']
        log("Server Configuration: " + str(d.conf), "VERBOSE")
    except Exception as e:
        log(str(e), "FAILURE")
        quit()

    log("Server registration successful. Opening Window.")
    
    if args.randomColors:
        random.shuffle(d.colors)
        
    openWindow(d)


if __name__ == "__main__":
    # execute only if run as a script
    signal.signal(signal.SIGINT, quit)
    main()
