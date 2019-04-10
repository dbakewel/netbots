import argparse
import time
import signal
import time
import random
import math

from netbots_log import log
from netbots_log import setLogLevel
import netbots_ipc as nbipc
import netbots_srvmsghl as nbmsghl
import netbots_math as nbmath

########################################################
### Server Data
########################################################

class SrvData():
    srvSocket = None

    conf = {
        #Static vars (some are settable at start up by server command line switches and then do not change after that.)
        'serverName': "NetBot Server",

        #Game and Tournament
        'botsInGame': 4, #Number of bots required to join before game can start.
        'gamesToPlay': 10, #Number of games to play before server quits.
        'stepMax' : 1000, #After this many steps in a game all bots will be killed
        'stepSec': 0.1, #Amount of time server targets for each step. Server will sleep if game is running faster than this.

        #Messaging
        'dropRate': 10, #Drop a messages every N messages
        'botMsgsPerStep': 4, #Number of msgs from a bot that server will respond to each step. Others in Q will be dropped.
        'allowRejoin' : True, #Allows crashed bots to rejoin game in progress.

        #Sizes
        'arenaSize' : 1000, #Area is a square with each side = arenaSize units (0,0 is bottom left, positive x is to right and positive y is up.)
        'botRadius': 25, #bots are circles with radius botRadius
        'explRadius': 75, #Radius of shell explosion. Beyond this radius bots will not take any damage.

        #Speeds and Rates of Change
        'botMaxSpeed': 5, #bots distance traveled per step at 100% speed
        'botAccRate': 5, #Amount in % bot can accelerate (or decelerate) per step
        'shellSpeed': 50, #distance traveled by shell per step
        'botMinTurnRate': math.pi/200, #Amount bot can rotate per turn in radians at 100% speed
        'botMaxTurnRate': math.pi/20, #Amount bot can rotate per turn in radians at 0% speed
        
        #Damage
        'hitDamage': 2, #Damage a bot takes from hitting wall or another bot
        'explDamage': 20, #Damage bot takes from direct hit from shell. The further from shell explosion will result in less damage.

        #Misc
        'keepExplotionSteps': 10, #Number of steps to keep old explosions in explosion dict (only useful to viewers).
    }

    state = {
        #Dynamic vars
        'gameNumber': 0,
        'gameStep' : 0,
        'dropNext': 10, #Drop the next message in N (count down)
        'dropCount' : 0, #How many messages have been dropped since start up.
        'serverSteps' : 0, #Number of steps server has processed.
        'stepTime' : 0, #Total time spent process steps
        'msgTime' : 0, #Total time spent processing messages
        'startTime' : time.time(),
        'explIndex' : 0,
        'sleepTime' : 0,
        'sleepCount' : 0,
        'longStepCount': 0,
        'tourStartTime' : False
    }

    bots = {}
    botTemplate = {
        'name': "template",
        'health': 0,
        'x': 500,
        'y': 500,
        'currentSpeed': 0,
        'requestedSpeed': 0,
        'currentDirection': 0,
        'requestedDirection': 0,
        'points': 0,
        'firedCount': 0,
        'shellDamage': 0
    }

    shells = {}
    shellTemplate = {
        'x': 500,
        'y': 500,
        'direction': 0,
        'distanceRemaining': 100
    }

    explotions = {}
    explotionTemplate = {
        'x': 500,
        'y': 500,
        'stepsAgo': 0,
        'src': "" #this is neede by viewer to color this explotion
    }

    viewers = {}
    viewerTemplate = {
        'lastKeepAlive': time.time(),
        'ip': "0.0.0.0",
        'port': 20011
    }

########################################################
### Bot Message Processing
########################################################

def processMsg(d, msg, src):
    if msg['type'] == 'joinRequest':
        reply = nbmsghl.joinRequest(d, msg, src)
    elif msg['type'] == 'addViewerRequest':
        reply = nbmsghl.addViewerRequest(d, msg, src)
    elif msg['type'] == 'viewKeepAlive':
        reply = nbmsghl.viewKeepAlive(d, msg, src)
    elif src in d.bots: #all other messages are only allowed from bots that have joined the game
        #if this is a message type suppored by server
        if hasattr(nbmsghl, msg['type']):
            reply = getattr(nbmsghl, msg['type'])(d, msg, src)
        else:
            reply = {'type': 'Error', 'result': "Msg type '"+msg['type']+"' should not be sent to server."}
    else:
        reply = {'type': 'Error', 'result': "Bots that have not joined game may only send joinRequest Msg."}

    #if the msg carried a msgId or replyData then copy it to the reply
    if reply:
        if 'msgID' in msg:
            reply['msgID'] = msg['msgID']
        if 'replyData' in msg:
            reply['replyData'] = msg['replyData']

    return reply

def dropMessage(d):
    """Returns True is the server should drop the next message"""
    if d.conf['dropRate'] != 0:
        if d.state['dropNext'] == 0:
            d.state['dropNext'] = d.conf['dropRate']
            d.state['dropCount'] += 1
            return True

        d.state['dropNext'] -= 1
    return False

def recvReplyMsgs(d):
    #process all messages in socket recv buffer
    startTime = time.perf_counter()
    msgQ = []
    more = True
    while more:
        try:
            msgQ.append(d.srvSocket.recvMessage())
        except nbipc.NetBotSocketException as e:
            more = False
        except Exception as e:
            log(str(type(e)) + " " + str(e),"ERROR")
            more = False
    
    botMsgCount = {}
    for msg, ip, port in msgQ:
        if dropMessage(d):
            continue

        src = nbipc.formatIpPort(ip,port)

        #Track src counter and drop msg if we have already proccessed the max msgs for this src this step
        if src in botMsgCount:
            botMsgCount[src] += 1
        else:
            botMsgCount[src] = 1
        if botMsgCount[src] >= d.conf['botMsgsPerStep']:
            continue

        reply = processMsg(d, msg, src)
        if reply:
            if dropMessage(d):
                continue
            try:
                d.srvSocket.sendMessage(reply, ip, port)
            except Exception as e:
                log(str(e),"ERROR")

    d.state['msgTime'] += time.perf_counter() - startTime
    log("Msgs Processed per Bot this step: " + str(botMsgCount),"DEBUG")

def sendToViwers(d):
    now = time.time()
    for src in list(d.viewers.keys()): #we need a list of keys so we can del from the viewers dict below
        v = d.viewers[src]
        if v['lastKeepAlive'] + 10 < now:
            del d.viewers[src]
            log("Viewer " + src + " didn't send keep alive in last 10 secs and was removed.")
        else:
            try:
                d.srvSocket.sendMessage( 
                    {
                     'type': 'viewData',
                     'state': d.state,
                     'bots': d.bots,
                     'shells': d.shells, 
                     'explotions': d.explotions
                    },
                    v['ip'], v['port'])
            except Exception as e:
                log(str(e),"ERROR")

########################################################
### Game Logic
########################################################

def findOverlapingBots(d):
    """Return any pair (src,src) of bots that overlap, else return False"""
    keys = list(d.bots.keys())

    for i in range(0,len(keys)-1):
        boti = d.bots[keys[i]]
        for j in range(i+1,len(keys)):
            botj = d.bots[keys[j]]
            if nbmath.distance(boti['x'],boti['y'],botj['x'],botj['y']) <= d.conf['botRadius']*2:
                return [keys[i],keys[j]]

    return False

def initGame(d):
    log("Starting New Game")
    """
    reset game state
    """
    d.state['gameNumber'] += 1
    d.state['gameStep'] = 0

    """
    for each bot
        reset health 100
        randomly place bot at least 10% of play area size away from any wall. Ensure no bots overlap.
        reset speed and direction values to 0
    """
    botsOverlap = True #loop must run at least once.
    while botsOverlap:
        for src, bot in d.bots.items():
            bot['health'] = 100
            bot['x'] = random.random() * (d.conf['arenaSize'] * 0.8) + (d.conf['arenaSize'] * 0.1)
            bot['y'] = random.random() * (d.conf['arenaSize'] * 0.8) + (d.conf['arenaSize'] * 0.1)
            bot['currentSpeed'] = 0
            bot['requestedSpeed'] = 0
            bot['currentDirection'] = 0
            bot['requestedDirection'] = 0
        botsOverlap = findOverlapingBots(d)
        if botsOverlap:
            log("Bots overlaped during random layout, trying again.","VERBOSE")

    """
    delete all shells and explotions.
    """
    d.shells = {}
    d.explotions = {}
    

def step(d):
    startTime = time.perf_counter()

    d.state['gameStep'] += 1
    d.state['serverSteps'] += 1

    #for each bot that is alive, copy health to so we know what it was at the start of the step.
    aliveBots = {}
    for src, bot in d.bots.items():
        if bot['health'] != 0:
            aliveBots[src] = bot['health']

    #for all bots that are alive
    for src, bot in d.bots.items():
        if src in aliveBots:
            #change speed if needed
            if bot['currentSpeed'] > bot['requestedSpeed']:
                bot['currentSpeed'] -= d.conf['botAccRate']
                if bot['currentSpeed'] < bot['requestedSpeed']:
                    bot['currentSpeed'] = bot['requestedSpeed']
            elif bot['currentSpeed'] < bot['requestedSpeed']:
                bot['currentSpeed'] += d.conf['botAccRate']
                if bot['currentSpeed'] > bot['requestedSpeed']:
                    bot['currentSpeed'] = bot['requestedSpeed']

            #change direction if needed
            if bot['currentDirection'] != bot['requestedDirection']:
                if bot['currentDirection'] != bot['requestedDirection'] and bot['currentSpeed'] == 0:
                    #turn instanly if bot is not moving
                    bot['currentDirection'] = bot['requestedDirection']
                else:
                    #how much can we turn at the speed we are going?
                    turnRate = d.conf['botMinTurnRate'] + (d.conf['botMaxTurnRate']-d.conf['botMinTurnRate'])*(1-bot['currentSpeed']/100)
                    
                    #if turn is negative and does not pass over 0 radians
                    if bot['currentDirection'] > bot['requestedDirection'] and \
                            bot['currentDirection'] - bot['requestedDirection'] <= math.pi:
                        bot['currentDirection'] -= turnRate
                        if bot['currentDirection'] <= bot['requestedDirection']:
                            bot['currentDirection'] = bot['requestedDirection']

                    #if turn is negative and passes over 0 radians, so we may need to normalize angle
                    elif bot['requestedDirection'] > bot['currentDirection'] and \
                            bot['requestedDirection'] - bot['currentDirection'] >= math.pi:
                        bot['currentDirection'] = nbmath.normalizeAngle(bot['currentDirection'] - turnRate)
                        if bot['currentDirection'] <= bot['requestedDirection'] and bot['currentDirection'] >= bot['requestedDirection'] - math.pi:
                            bot['currentDirection'] = bot['requestedDirection']

                    #if turn is positive and does not pass over 0 radians
                    elif bot['requestedDirection'] > bot['currentDirection'] and \
                            bot['requestedDirection'] - bot['currentDirection'] <= math.pi:
                        bot['currentDirection'] += turnRate
                        if bot['requestedDirection'] <= bot['currentDirection']:
                            bot['currentDirection'] = bot['requestedDirection']

                    #if turn is positive and passes over 0 radians
                    elif bot['currentDirection'] > bot['requestedDirection'] and \
                            bot['currentDirection'] - bot['requestedDirection'] >= math.pi:
                        bot['currentDirection'] = nbmath.normalizeAngle(bot['currentDirection'] + turnRate)
                        if bot['currentDirection'] >= bot['requestedDirection'] and bot['currentDirection'] <= bot['requestedDirection'] + math.pi:
                            bot['currentDirection'] = bot['requestedDirection']
            #move bot
            if bot['currentSpeed'] != 0:
                bot['x'],bot['y'] = nbmath.project(bot['x'],bot['y'],bot['currentDirection'],bot['currentSpeed']/100.0*d.conf['botMaxSpeed'])

    #do until we get one clean pass where no bot hitting wall or other bot.
    foundOverlap = True
    while foundOverlap:
        foundOverlap = False

        #detect if bots hit walls. if they, did move them so they are just barly not touching,
        for src, bot in d.bots.items():
            if bot['x'] - d.conf['botRadius'] < 0:
                bot['x'] = d.conf['botRadius'] + 1
                bot['hitDamage'] = True
                foundOverlap = True
            if bot['x'] + d.conf['botRadius'] > d.conf['arenaSize']:
                bot['x'] = d.conf['arenaSize'] - d.conf['botRadius'] - 1
                bot['hitDamage'] = True
                foundOverlap = True
            if bot['y'] - d.conf['botRadius'] < 0:
                bot['y'] = d.conf['botRadius'] + 1
                bot['hitDamage'] = True
                foundOverlap = True
            if bot['y'] + d.conf['botRadius'] > d.conf['arenaSize']:
                bot['y'] = d.conf['arenaSize'] - d.conf['botRadius'] - 1
                bot['hitDamage'] = True
                foundOverlap = True
        
        #detect if bots hit other bots, if the did move them so they are just barly not touching,
        overlap = findOverlapingBots(d)
        while overlap:
            foundOverlap = True
            b1 = d.bots[overlap[0]]
            b2 = d.bots[overlap[1]]
            #find angle to move bot directly away from each other
            a = nbmath.angle(b1['x'],b1['y'],b2['x'],b2['y'])
            #find min distance to move each bot so they don't touch (plus 0.5 for saftly).
            between = nbmath.distance(b1['x'],b1['y'],b2['x'],b2['y'])
            distance = between/2 - (between-d.conf['botRadius']) + 0.5
            #move bots
            b1['x'], b1['y'] = nbmath.project(b1['x'], b1['y'], a + math.pi, distance)
            b2['x'], b2['y'] = nbmath.project(b2['x'], b2['y'], a, distance)
            #record damage and check for more bots overlapping
            b1['hitDamage'] = True
            b2['hitDamage'] = True
            overlap = findOverlapingBots(d)

    #give damage (only once this step) to bots that hit things. Also stop them.
    for src, bot in d.bots.items():
        if 'hitDamage' in bot:
            del bot['hitDamage']
            bot['health'] = max(0,bot['health']-d.conf['hitDamage'])
            bot['currentSpeed'] = 0
            bot['requestedSpeed'] = 0

    #for all shells
    for src in list(d.shells.keys()):
        shell = d.shells[src]

        #move shell
        distance = min(d.conf['shellSpeed'], shell['distanceRemaining'])
        shell['x'],shell['y'] = nbmath.project(shell['x'],shell['y'],shell['direction'],distance)
        shell['distanceRemaining'] -= distance

        #if shell's explotion would touch inside of arena
        if shell['x'] > d.conf['explRadius']*-1 and shell['x'] < d.conf['arenaSize']+d.conf['explRadius'] and \
           shell['y'] > d.conf['explRadius']*-1 and shell['y'] < d.conf['arenaSize']+d.conf['explRadius']:

            #if shell has reached it destination then explode.
            if shell['distanceRemaining'] <= 0:
                #apply damage to bots.
                for k, bot in d.bots.items():
                    if bot['health'] > 0:
                        distance = nbmath.distance(bot['x'],bot['y'],shell['x'],shell['y'])
                        if distance < d.conf['explRadius']:
                            damage = d.conf['explDamage'] * (1 - distance/d.conf['explRadius'])
                            bot['health'] = max(0,bot['health']-damage)
                            #allow recording of inflicting damage that is greater than health of hit robot.
                            #also record damage to oneself.
                            d.bots[src]['shellDamage'] += damage

                #store the explotion so viewers can display it. we cannont use src as index becuase it is possible for two explotions
                #from same bot to exist (but not likly).
                d.explotions[d.state['explIndex']] = {
                    'x': shell['x'],
                    'y': shell['y'],
                    'stepsAgo': 0,
                    'src': src #this is needed by viewer to color this explotion based on the bot who fired it.
                }
                d.state['explIndex'] += 1
                if d.state['explIndex'] > 65000:
                    d.state['explIndex'] = 0

                #this shell exploed so remove it
                del d.shells[src]
        else:
            #shell left arena so remove it without exploding
            del d.shells[src]

    #Remove old explotions and add 1 to other explotions stepsAgo.
    #Note, We only keep these around so the viewer can do a nice animation over a number of steps before they are removed.
    for key in list(d.explotions.keys()):
        expl = d.explotions[key]
        if expl['stepsAgo'] == d.conf['keepExplotionSteps']:
            del d.explotions[key]
        else:
            expl['stepsAgo'] += 1

    #find how many points bots that died this step will get. (Based on how many bots have died previouly)
    if len(aliveBots) == d.conf['botsInGame']:
        points = 0 #first to die
    elif len(aliveBots) > d.conf['botsInGame']/2:
        points = 2 #died in first half
    else:
        points = 5 #died in second half

    #Kill all bots if we have reached the max steps and there is still more than one bot alive.
    if d.state['gameStep'] == d.conf['stepMax'] and len(aliveBots) != 1:
        log("Game reached stepMax with more than one bot alive. Killing all bots.")
        for src in aliveBots:
            d.bots[src]['health'] = 0

    #Assign points to bots that died this turn
    for src in list(aliveBots.keys()):
        if d.bots[src]['health'] == 0:
            d.bots[src]['points'] += points
            del aliveBots[src]

    #If only one bot is left then end game.
    if len(aliveBots) == 1:
        src = list(aliveBots.keys())[0]
        d.bots[src]['health'] = 0
        d.bots[src]['points'] += 10 #last robot (winner)
        del aliveBots[src]

    if len(aliveBots) == 0:
        #Game ended.
        logScoreBoard(d)

    d.state['stepTime'] += time.perf_counter() - startTime


########################################################
### Stats and Points Logging
########################################################

def logStats(d):
    log("\n\n                  ======= Stats ======="+\
        "\n\n                    Run Time: " + '%.3f'%(time.time() - d.state['startTime']) + " secs." +\
          "\n    Time Processing Messages: " + '%.3f'%(d.state['msgTime']) + " secs." +\
          "\n                 Messages In: " + str(d.srvSocket.recv) +\
          "\n                Messages Out: " + str(d.srvSocket.sent) +\
          "\n            Messages Dropped: " + str(d.state['dropCount']) +\
          "\n       Time Processing Steps: " + '%.3f'%(d.state['stepTime']) + " secs." +\
          "\n               Time Sleeping: " + '%.3f'%(float(d.state['sleepTime'])) + " secs." +\
          "\n          Average Sleep Time: " + '%.3f'%(float(d.state['sleepTime'])/max(1,d.state['sleepCount'])) + " secs." +\
          "\n   Steps Slower Than stepSec: " + str(d.state['longStepCount']) +\
        "\n\n")

def logScoreBoard(d):
    if d.state['tourStartTime'] and d.state['gameNumber']:
        now = time.time()
        output = "\n\n                ====== Score Board ======" +\
                   "\n               Tournament Time: " + '%.3f'%(now - d.state['tourStartTime']) + " secs." +\
                   "\n                         Games: " + str(d.state['gameNumber']) +\
                   "\n             Average Game Time: " + '%.3f'%((now - d.state['tourStartTime'])/d.state['gameNumber']) + " secs." +\
                   "\n                         Steps: " + str(d.state['serverSteps']) +\
                   "\n          Average Steps / Game: " + '%.3f'%(d.state['serverSteps']/d.state['gameNumber']) +\
                 "\n\n                      Points   Name"

        for src, bot in d.bots.items():
            output += "\n                    " + '{0:8}'.format(bot['points']) + "   " + bot['name'] + " (" + src +")"

        output += "\n\n"

        log(output)

########################################################
### Main Loop
########################################################

def quit(signal=None, frame=None):
    global d

    logStats(d)
    logScoreBoard(d)

    log("Quiting","INFO")
    exit()

def main():
    global d #give quit access to d

    d = SrvData()

    random.seed()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-ip', metavar='Server IP', dest='serverIP', type=nbipc.argParseCheckIPFormat, nargs='?', default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='Server Port',dest='serverPort', type=int, nargs='?', default=20000, help='My port number')
    parser.add_argument('-name', metavar='Server Name', dest='serverName', type=str, default="Netbots Server", help='Name displayed by connected viewers.')
    parser.add_argument('-games', metavar='N', dest='gamesToPlay', type=int, default=10, help='Games server will play before quiting.')
    parser.add_argument('-bots', metavar='N', dest='botsInGame', type=int, default=4, help='Number of bots required to join before game can start.')
    parser.add_argument('-stepsec', metavar='sec', dest='stepSec', type=float, default=0.1, help='How many seconds between server steps.')
    parser.add_argument('-stepmax', metavar='int', dest='stepMax', type=int, default=1000, help='Max steps in one game.')
    parser.add_argument('-droprate', metavar='int', dest='dropRate', type=int, default=10, help='Drop over nth message. 0 == no drop.')
    parser.add_argument('-msgperstep', metavar='int', dest='botMsgsPerStep', type=int, default=4, help='Number of msgs from a bot that server will respond to each step.')
    parser.add_argument('-arenasize', metavar='int', dest='arenaSize', type=int, default=1000, help='Size of arena.')
    parser.add_argument('-botradius', metavar='int', dest='botRadius', type=int, default=25, help='Radius of robots.')
    parser.add_argument('-explradius', metavar='int', dest='explRadius', type=int, default=75, help='Radius of explosions.')
    parser.add_argument('-botmaxspeed', metavar='int', dest='botMaxSpeed', type=int, default=5, help="Robot distance traveled per step at 100%% speed")
    parser.add_argument('-botaccrate', metavar='int', dest='botAccRate', type=int, default=5, help='%% robot can accelerate (or decelerate) per step')
    parser.add_argument('-shellspeed', metavar='int', dest='shellSpeed', type=int, default=50, help='Distance traveled by shell per step.')
    parser.add_argument('-hitdamage', metavar='int', dest='hitDamage', type=int, default=2, help='Damage a robot takes from hitting wall or another bot.')
    parser.add_argument('-expldamage', metavar='int', dest='explDamage', type=int, default=20, help='Damage bot takes from direct hit from shell.')
    parser.add_argument('-stats', metavar='sec', dest='statsSec', type=int, default=60, help='How many seconds between printing server stats.')
    parser.add_argument('-debug', dest='debug', action='store_true', default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true', default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    args = parser.parse_args()
    
    d.conf['serverName'] = args.serverName
    d.conf['gamesToPlay'] = args.gamesToPlay
    d.conf['botsInGame'] = args.botsInGame
    d.conf['stepSec'] = args.stepSec
    d.conf['stepMax'] = args.stepMax
    d.conf['dropRate'] = args.dropRate
    d.state['dropNext'] = args.dropRate
    d.conf['botMsgsPerStep'] = args.botMsgsPerStep
    d.conf['arenaSize'] = args.arenaSize
    d.conf['botRadius'] = args.botRadius
    d.conf['explRadius'] = args.explRadius
    d.conf['botMaxSpeed'] = args.botMaxSpeed
    d.conf['botAccRate'] = args.botAccRate
    d.conf['shellSpeed'] = args.shellSpeed
    d.conf['hitDamage'] = args.hitDamage
    d.conf['explDamage'] = args.explDamage
    setLogLevel(args.debug, args.verbose)
    
    log("Server Configuration: " + str(d.conf),"VERBOSE")

    try:
        d.srvSocket = nbipc.NetBotSocket(args.serverIP, args.serverPort)
    except Exception as e:
        log(str(e),"FAILURE")
        quit()

    nextStatsTime = time.time() + args.statsSec
    while True:
        loopStartTime = time.time()

        aliveBots = 0
        for src, bot in d.bots.items():
            if bot['health'] != 0:
                aliveBots += 1

        if aliveBots > 0: #if there is an ongoing game
            step(d)
        elif len(d.bots) == d.conf['botsInGame']: #if we have enough bots to start playing
            if not d.state['tourStartTime']:
                d.state['tourStartTime'] = time.time()
            if d.conf['gamesToPlay'] != d.state['gameNumber']:
                initGame(d)
            else:
                log("All games have been played.")
                quit()

        recvReplyMsgs(d)
        
        sendToViwers(d)

        if nextStatsTime < time.time():
            logStats(d)
            nextStatsTime = time.time() + args.statsSec

        nextStepIn = d.conf['stepSec'] - (time.time() - loopStartTime)
        
        if nextStepIn > 0:
            d.state['sleepCount'] += 1
            d.state['sleepTime'] += nextStepIn
            time.sleep(nextStepIn)
        else:
            d.state['longStepCount'] += 1
            log("Server running slower than " + str(d.conf['stepSec']) + " sec/step.", "WARNING")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)
    main()
