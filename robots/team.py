import os
import sys
import argparse
import time
import signal
import math
import random
import threading

# include the netbot src directory in sys.path so we can import modules from it.
robotpath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(os.path.dirname(robotpath), "src")
sys.path.insert(0, srcpath)

import netbots_math as nbmath
import netbots_ipc as nbipc
from netbots_log import setLogLevel
from netbots_log import log

class sharedData():
    x = -1000
    y = -1000


class Robot(threading.Thread):
    def __init__(self, name, ip, port, serverip, serverport, mydata, friendsData):

        threading.Thread.__init__(self)

        self.name = name
        self.mydata = mydata
        self.friendsData = friendsData

        log(name + ": Running!")

        try:
            botSocket = nbipc.NetBotSocket(ip, port, serverip, serverport)
            self.botSocket = botSocket

            joinReply = botSocket.sendRecvMessage(
                {'type': 'joinRequest', 'name': name}, retries=300, delay=1, delayMultiplier=1)
            self.srvConf = joinReply['conf']

        except nbipc.NetBotSocketException as e:
            log(name + ": Is netbot server running at" + args.serverIP + ":" + str(args.serverPort) + "?")
            log(str(e), name + ": FAILURE")
            quit()

        log(name + ": Join server was successful. We are ready to play!")
        log(name + ": " + str(self.srvConf), "VERBOSE")


class Leader(Robot):
    def run(self):
        name = self.name
        botSocket = self.botSocket
        srvConf = self.srvConf
        mydata = self.mydata
        friendsData = self.friendsData

        log(name + ": Running!")

        self.stop = False  # when this becomes True the run method must return.
        while not self.stop:
            try:
                # Store my location in mydata so friend can see it.
                getLocationReply = botSocket.sendRecvMessage({'type': 'getLocationRequest'})
                mydata.x = getLocationReply['x']
                mydata.y = getLocationReply['y']

                # Compute distance to friend.
                distanceToFriend = nbmath.distance(mydata.x, mydata.y, friendsData.x, friendsData.y)
                log(f"{name}: Distance to friend == {distanceToFriend:>4.2f}", "INFO")

                if distanceToFriend > 300:
                    # wait for friend to catch up.
                    botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': 0})
                    log(name + ": Waiting for friend to get closer.", "INFO")
                else:
                    getSpeedReply = botSocket.sendRecvMessage({'type': 'getSpeedRequest'})
                    if getSpeedReply['requestedSpeed'] == 0:
                        radians = random.random() * 2 * math.pi
                        botSocket.sendRecvMessage({'type': 'setDirectionRequest', 'requestedDirection': radians})
                        botSocket.sendRecvMessage({'type': 'setSpeedRequest', 'requestedSpeed': 100})
                        log(f"{name}: Requested to go {radians:>4.2f} radians at max speed.", "INFO")

            except nbipc.NetBotSocketException as e:
                log(name + ": " + str(e), "WARNING")
                continue


class Follower(Robot):
    def run(self):
        name = self.name
        botSocket = self.botSocket
        srvConf = self.srvConf
        mydata = self.mydata
        friendsData = self.friendsData

        log(name + ": Running!")

        self.stop = False  # when this becomes True the run method must return.
        while not self.stop:
            try:
                # Store my location in mydata so friend can see it.
                getLocationReply = botSocket.sendRecvMessage({'type': 'getLocationRequest'})
                mydata.x = getLocationReply['x']
                mydata.y = getLocationReply['y']

                # Compute distance to friend and set speed based on distance (slower as we get closer).
                distanceToFriend = nbmath.distance(mydata.x, mydata.y, friendsData.x, friendsData.y)
                botSocket.sendRecvMessage({'type': 'setSpeedRequest',
                                           'requestedSpeed': min(100, distanceToFriend / 1000 * 100)})

                # Compute angle to friend and go in that direction.
                angleToFriend = nbmath.angle(mydata.x, mydata.y, friendsData.x, friendsData.y)
                botSocket.sendRecvMessage({'type': 'setDirectionRequest', 'requestedDirection': angleToFriend})

                log(f"{name}: Distance to friend == {distanceToFriend:>4.2f}, Angle to friend == {angleToFriend:>4.2f},", "INFO")

            except nbipc.NetBotSocketException as e:
                log(name + ": " + str(e), "WARNING")
                continue


def quit(signal=None, frame=None):
    global leader, follower

    # tell bots to return (stop thread)
    for bot in (leader, follower):
        if bot.isAlive():
            bot.stop = True

    log("Quiting", "INFO")


def main():
    global leader, follower  # This is global so quit() can access them.

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

    # Create shared data.
    leaderData = sharedData()
    followerData = sharedData()

    # Create robot thread objects, each need to use a different port number since they both will open a socket.
    robotPort = args.myPort
    leader = Leader("Team Leader", args.myIP, robotPort, args.serverIP, args.serverPort, leaderData, followerData)
    robotPort += 1
    follower = Follower("Team Follower", args.myIP, robotPort, args.serverIP, args.serverPort, followerData, leaderData)

    # Start threads. This will call the run() method.
    leader.start()
    follower.start()

    # Wait for leader and follower to both end
    while leader.isAlive() or follower.isAlive():
        time.sleep(1)

    # Both threads have returned. Print stats and exit.
    for bot in (leader, follower):
        log("=====================================")
        log("=== " + bot.name)
        log("=====================================")
        log(bot.botSocket.getStats())
    exit()


if __name__ == "__main__":
    # execute only if run as a script
    signal.signal(signal.SIGINT, quit)
    main()
