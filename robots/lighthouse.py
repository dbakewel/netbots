import os
import sys
import argparse
import time
import signal
import math
import random

# include the netbot src directory in sys.path so we can import modules from it.
robotpath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(os.path.dirname(robotpath),"src") 
sys.path.insert(0,srcpath)

from netbots_log import log
from netbots_log import setLogLevel
import netbots_ipc as nbipc
import netbots_math as nbmath

robotName = "Lighthouse v1"


def play(botSocket, srvConf):
    gameNumber = 0  # The last game number bot got from the server (0 == no game has been started)

    while True:
        try:
            # Get information to determine if bot is alive (health > 0) and if a new game has started.
            getInfoReply = botSocket.sendRecvMessage({'type': 'getInfoRequest'})
        except nbipc.NetBotSocketException as e:
            # We are always allowed to make getInfoRequests, even if our health == 0. Something serious has gone wrong.
            log(str(e), "FAILURE")
            log("Is netbot server still running?")
            quit()

        if getInfoReply['health'] == 0:
            # we are dead, there is nothing we can do until we are alive again.
            continue

        if getInfoReply['gameNumber'] != gameNumber:
            # A new game has started. Record new gameNumber and reset any variables back to their initial state
            gameNumber = getInfoReply['gameNumber']
            log("Game " + str(gameNumber) + " has started. Points so far = " + str(getInfoReply['points']))

            # start every new game in scan mode. No point waiting if we know we have not fired our canon yet.
            currentMode = "scan"

            # lighthouse will scan the area in this many slices (think pizza slices with this bot in the middle)
            scanSlices = 32

            # This is the radians of where the next scan will be
            nextScanSlice = 0

            # Each scan will be this wide in radians (note, math.pi*2 radians is the same as 360 Degrees)
            scanSliceWidth = math.pi * 2 / scanSlices

        try:
            if currentMode == "wait":
                # find out if we already have a shell in the air. We need to wait for it to explode before
                # we fire another shell. If we don't then the first shell will never explode!
                getCanonReply = botSocket.sendRecvMessage({'type': 'getCanonRequest'})
                if not getCanonReply['shellInProgress']:
                    # we are ready to shoot again!
                    currentMode = "scan"

            if currentMode == "scan":
                scanRadStart = nextScanSlice * scanSliceWidth
                scanRadEnd = min(scanRadStart + scanSliceWidth, math.pi * 2)
                scanReply = botSocket.sendRecvMessage(
                    {'type': 'scanRequest', 'startRadians': scanRadStart, 'endRadians': scanRadEnd})

                # if we found an enemy robot with our scan
                if scanReply['distance'] != 0:
                    # fire down the center of the slice we just scanned.
                    fireDirection = scanRadStart + scanSliceWidth / 2
                    botSocket.sendRecvMessage(
                        {'type': 'fireCanonRequest', 'direction': fireDirection, 'distance': scanReply['distance']})
                    # make sure don't try and shoot again until this shell has exploded.
                    currentMode = "wait"

                nextScanSlice += 1
                if nextScanSlice == scanSlices:
                    nextScanSlice = 0

        except nbipc.NetBotSocketException as e:
            # Consider this a warning here. It may simply be that a request returned
            # an Error reply because our health == 0 since we last checked. We can
            # continue until the next game starts.
            log(str(e), "WARNING")
            continue

##################################################################
# Standard stuff below.
##################################################################


def quit(signal=None, frame=None):
    global botSocket
    log(botSocket.getStats())
    log("Quiting", "INFO")
    exit()


def main():
    global botSocket  # This is global so quit() can print stats in botSocket
    global robotName

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-ip', metavar='My IP', dest='myIP', type=nbipc.argParseCheckIPFormat, nargs='?',
                        default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='My Port', dest='myPort', type=int, nargs='?',
                        default=20010, help='My port number')
    parser.add_argument('-sip', metavar='Server IP', dest='serverIP', type=nbipc.argParseCheckIPFormat, nargs='?',
                        default='127.0.0.1', help='Server IP Address')
    parser.add_argument('-sp', metavar='Server Port', dest='serverPort', type=int, nargs='?',
                        default=20000, help='Server port number')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    args = parser.parse_args()
    setLogLevel(args.debug, args.verbose)

    try:
        botSocket = nbipc.NetBotSocket(args.myIP, args.myPort, args.serverIP, args.serverPort)
        joinReply = botSocket.sendRecvMessage({'type': 'joinRequest', 'name': robotName}, retries=300, delay=1, delayMultiplier=1)
    except nbipc.NetBotSocketException as e:
        log("Is netbot server running at" + args.serverIP + ":" + str(args.serverPort) + "?")
        log(str(e), "FAILURE")
        quit()

    log("Join server was successful. We are ready to play!")

    # the server configuration tells us all about how big the arena is and other useful stuff.
    srvConf = joinReply['conf']
    log(str(srvConf), "VERBOSE")

    # Now we can play, but we may have to wait for a game to start.
    play(botSocket, srvConf)


if __name__ == "__main__":
    # execute only if run as a script
    signal.signal(signal.SIGINT, quit)
    main()
