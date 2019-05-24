import argparse
import time
import signal
import tkinter as t
import random
import math

from netbots_log import log
from netbots_log import setLogLevel
import netbots_ipc as nbipc
import netbots_math as nbmath


class ViewerData():
    viewerSocket = None

    window = None
    frame = None
    statusWidget = None
    canvas = None
    botWidgets = {}
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


def checkForUpdates(d):
    msg = {"type": "Error", "result": "We never got any new data from server."}
    try:
        # keep getting messages until we get the last one and then an exception is thrown.
        while True:
            msg, ip, port = d.viewerSocket.recvMessage()
    except nbipc.NetBotSocketException as e:
        # if message type is Error and we have not got good data for 100 steps then quit
        if msg['type'] == 'Error' and d.lastViewData + d.conf['stepSec'] * 100 < time.time():
            # We didn't get anything from the buffer or it was an invalid message.
            d.canvas.itemconfigure(d.bigMsg, text="Server stopped sending data.")
    except Exception as e:
        log(str(e), "ERROR")
        quit()

    if msg['type'] == 'viewData':
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

                # create bot widget
                d.botWidgets[src] = d.canvas.create_oval(0, 0, 0, 0, fill=c)

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
            else:
                centerX = bot['x'] * d.scale + d.borderSize
                centerY = d.conf['arenaSize'] - bot['y'] * d.scale + d.borderSize
                d.canvas.coords(d.botWidgets[src],
                                centerX - d.conf['botRadius'],
                                centerY - d.conf['botRadius'],
                                centerX + d.conf['botRadius'],
                                centerY + d.conf['botRadius'])
                d.canvas.itemconfigure(d.botWidgets[src], state='normal')

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
                d.explWidgets[k] = d.canvas.create_oval(centerX - d.conf['explRadius'],
                                                        centerY - d.conf['explRadius'],
                                                        centerX + d.conf['explRadius'],
                                                        centerY + d.conf['explRadius'],
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

    # Wait two steps before updating screen.
    d.window.after(int(d.conf['stepSec'] * 1000), checkForUpdates, d)


def openWindow(d):
    d.window = t.Tk()
    d.window.title("NetBots")

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


def quit(signal=None, frame=None):
    log("Quiting", "INFO")
    exit()


def main():
    d = ViewerData()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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
