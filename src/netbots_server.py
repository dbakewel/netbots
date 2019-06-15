import argparse
import sys
import signal
import time
import random
import math
import itertools

from netbots_log import log
from netbots_log import setLogLevel
import netbots_ipc as nbipc
import netbots_srvmsghl as nbmsghl
import netbots_math as nbmath

########################################################
# Server Data
########################################################


class SrvData:
    srvSocket = None

    conf = {
        # Static vars (some are settable at start up by server command line switches and then do not change after that.)
        'serverName': "NetBot Server",
        'serverVersion': "2.0.0",

        # Game and Tournament
        'botsInGame': 4,  # Number of bots required to join before game can start.
        'gamesToPlay': 10,  # Number of games to play before server quits.
        'stepMax': 1000,  # After this many steps in a game all bots will be killed
        # Amount of time server targets for each step. Server will sleep if game is running faster than this.
        'stepSec': 0.05,
        'startPermutations':  False,  # Use all permutations of each set of random start locations.
        'simpleCollisions': False,  # Use simple collision system, affected by -hitdamage
        'scanMaxDistance': 1415,  # Maximum distance a scan can detect a robot.

        # Messaging
        'dropRate': 11,  # Drop a messages every N messages. Best to use primes.
        # Number of msgs from a bot that server will respond to each step. Others in Q will be dropped.
        'botMsgsPerStep': 4,
        'allowRejoin': True,  # Allows crashed bots to rejoin game in progress.
        'noViewers': False,  # if True addViewerRequest messages will be rejected. 

        # Sizes
        # Area is a square with each side = arenaSize units (0,0 is bottom left,
        # positive x is to right and positive y is up.)
        'arenaSize': 1000,
        'botRadius': 25,  # bots are circles with radius botRadius
        'explRadius': 75,  # Radius of shell explosion. Beyond this radius bots will not take any damage.

        # Speeds and Rates of Change
        'botMaxSpeed': 5,  # bots distance traveled per step at 100% speed
        'botAccRate': 2.0,  # Amount in % bot can accelerate (or decelerate) per step
        'shellSpeed': 40,  # distance traveled by shell per step
        'botMinTurnRate': math.pi / 6000,  # Amount bot can rotate per turn in radians at 100% speed
        'botMaxTurnRate': math.pi / 50,  # Amount bot can rotate per turn in radians at 0% speed

        # Damage
        'hitDamage': 10,  # Damage a bot takes from hitting wall or another bot
        # Damage bot takes from direct hit from shell. The further from shell explosion will result in less damage.
        'explDamage': 10,
        'botArmor': 1.0,  # Damage multiplier

        # Obstacles (robots and shells are stopped by obstacles but obstacles are transparent to scan)
        'obstacles': [],  # Obstacles of form [{'x':float,'y':float,'radius':float},...]
        'obstacleRadius': 5,  # Radius of obstacles as % of arenaSize

        # Jam Zones (robots fully inside jam zone are not detected by scan)
        'jamZones': [],  # Jam Zones of form [{'x':float,'y':float,'radius':float},...]

        # Misc
        'keepExplosionSteps': 10,  # Number of steps to keep old explosions in explosion dict (only useful to viewers).
        
        #Robot Classes (values below override what's above for robots in that class)
        'allowClasses': False,
        #Only fields listed in classFields are allowed to be overwritten by classes.
        'classFields': ('botMaxSpeed', 'botAccRate', 'botMinTurnRate', 'botMaxTurnRate', 'botArmor', 'shellSpeed', 'explDamage', 'explRadius'),
        'classes': {
            'default': {
                # Default class should have no changes.
                },
                
            'heavy': {
                # Speeds and Rates of Change
                'botMaxSpeed': 0.7,  # multiplier for bot max speed
                'botAccRate': 0.55,  # multiplier for bot acceleration rate
                'botMinTurnRate': 0.923076923,  # multiplier for bot turning rate at 100% speed
                'botMaxTurnRate': 0.333333333,  # multiplier for bot turning rate at 0% speed
                'botArmor': 0.862  # multiplier of robot damage taken
                },
            
            'light': {
                # Speeds and Rates of Change
                'botMaxSpeed': 2.8,  # multiplier for bot max speed
                'botAccRate': 1.6,  # multiplier for bot acceleration rate
                'botMinTurnRate': 1.4,  # multiplier for bot turning rate at 100% speed
                'botMaxTurnRate': 1.75,  # multiplier for bot turning rate at 0% speed
                'botArmor': 1.25  # multiplier of robot damage taken
                },
                
            'machinegun': {
                # Speeds and Rates of Change
                'botMaxSpeed': 1.4,  # multiplier for bot max speed
                'botAccRate': 1.2,  # multiplier for bot acceleration rate
                'botMinTurnRate': 1.2,  # multiplier for bot turning rate at 100% speed
                'botMaxTurnRate': 1.6,  # multiplier for bot turning rate at 0% speed
                'botArmor': 0.93,  # multiplier of robot damage taken
                'shellSpeed': 30,  # multiplier of distance traveled by shell per step
                'explDamage': 0.237,
                'explRadius': 1.1
                },
                
            'sniper': {
                # Speeds and Rates of Change
                'botMaxSpeed': 1,  # multiplier for bot max speed
                'botAccRate': 0.7,  # multiplier for bot acceleration rate
                'botMinTurnRate': 1,  # multiplier for bot turning rate at 100% speed
                'botMaxTurnRate': 0.8,  # multiplier for bot turning rate at 0% speed
                'botArmor': 1.1,  # multiplier of robot damage taken
                'shellSpeed': 3,  # multiplier of distance traveled by shell per step
                'explDamage': 2.85,
                'explRadius': 0.4
                },
                
            'turtle': {
                # Speeds and Rates of Change
                'botMaxSpeed': 0.5,  # multiplier for bot max speed
                'botAccRate': 0.15,  # multiplier for bot acceleration rate
                'botMinTurnRate': 0.6,  # multiplier for bot turning rate at 100% speed
                'botMaxTurnRate': 0.5,  # multiplier for bot turning rate at 0% speed
                'botArmor': 0.83,  # multiplier of robot damage taken
                'shellSpeed': 0.38,  # multiplier of distance traveled by shell per step
                'explDamage': 2.8,
                'explRadius': 1.6
                }
            }
        }

    state = {
        # Dynamic vars
        'gameNumber': 0,
        'gameStep': 0,
        'dropNext': 10,  # Drop the next message in N (count down)
        'dropCount': 0,  # How many messages have been dropped since start up.
        'serverSteps': 0,  # Number of steps server has processed.
        'stepTime': 0,  # Total time spent process steps
        'msgTime': 0,  # Total time spent processing messages
        'viewerMsgTime': 0,  # Total time spend sending information to the viewer
        'startTime': time.time(),
        'explIndex': 0,
        'sleepTime': 0,
        'sleepCount': 0,
        'longStepCount': 0,
        'tourStartTime': False
        }

    starts = []  # [ [locIndex, locIndex, ...], [locIndex, locIndex, ...], ...]
    startLocs = []  # [{'x': x, 'y' y},{'x': x, 'y' y},...]
    startBots = []  # [src, src, ...]

    bots = {}
    botTemplate = {
        'name': "template",
        'class': "default",
        'health': 0,
        'x': 500,
        'y': 500,
        'currentSpeed': 0,
        'requestedSpeed': 0,
        'currentDirection': 0,
        'requestedDirection': 0,
        'points': 0,
        'firedCount': 0,
        'shellDamage': 0,
        'winHealth': 0,
        'winCount': 0,
        'last': {
            # Copies of last fire and scan requests. This data is not stored elsewhere
            # and is useful for viewer to display.
            'fireCanonRequest': {'direction': 0, 'distance': 10},
            'scanRequest': {'startRadians': 0, 'endRadians': 0},
            }
        }

    shells = {}
    shellTemplate = {
        'x': 500,
        'y': 500,
        'direction': 0,
        'distanceRemaining': 100
        }

    explosions = {}
    explosionTemplate = {
        'x': 500,
        'y': 500,
        'stepsAgo': 0,
        'src': ""  # this is needed by viewer to color this explosion
        }

    viewers = {}
    viewerTemplate = {
        'lastKeepAlive': time.time(),
        'ip': "0.0.0.0",
        'port': 20011
        }

    def getClassValue(self, fld, c="default"):
        """
        Use this function to get values from SrvData.conf that respect robot class. 
        It ensures that the correct default or class value is returned. Only certain fields
        in SrvData.conf are allowed to be overwritten with class values.
        """
        if fld not in self.conf['classFields']:
            raise Exception("ERROR, " + str(fld) + " not allowed in robot class.")

        value = self.conf[fld]  # default value
        if 'classes' in self.conf and c in self.conf['classes'] and fld in self.conf['classes'][c]:
            if isinstance(value, (int, float)):
                value *= self.conf['classes'][c][fld]  # class specific multiplier
            else:
                value = self.conf['classes'][c][fld]  # class specific value
        
        return value

########################################################
# Bot Message Processing
########################################################


def processMsg(d, msg, src):
    if msg['type'] == 'joinRequest':
        reply = nbmsghl.joinRequest(d, msg, src)
    elif msg['type'] == 'addViewerRequest':
        reply = nbmsghl.addViewerRequest(d, msg, src)
    elif msg['type'] == 'viewKeepAlive':
        reply = nbmsghl.viewKeepAlive(d, msg, src)
    elif src in d.bots:  # all other messages are only allowed from bots that have joined the game
        # if this is a message type suppored by server
        if hasattr(nbmsghl, msg['type']):
            reply = getattr(nbmsghl, msg['type'])(d, msg, src)
        else:
            reply = {'type': 'Error', 'result': "Msg type '" + msg['type'] + "' should not be sent to server."}
    else:
        reply = {'type': 'Error', 'result': "Bots that have not joined game may only send joinRequest Msg."}

    # if the msg carried a msgId or replyData then copy it to the reply
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
    # process all messages in socket recv buffer
    startTime = time.perf_counter()
    msgQ = []
    more = True
    while more:
        try:
            msgQ.append(d.srvSocket.recvMessage())
        except nbipc.NetBotSocketException as e:
            more = False
        except Exception as e:
            log(str(type(e)) + " " + str(e), "ERROR")
            more = False

    botMsgCount = {}
    for msg, ip, port in msgQ:
        if dropMessage(d):
            continue

        src = nbipc.formatIpPort(ip, port)

        # Track src counter and drop msg if we have already proccessed the max msgs for this src this step
        if src in botMsgCount:
            botMsgCount[src] += 1
        else:
            botMsgCount[src] = 1
        if botMsgCount[src] > d.conf['botMsgsPerStep']:
            continue

        reply = processMsg(d, msg, src)
        if reply:
            if dropMessage(d):
                continue
            try:
                d.srvSocket.sendMessage(reply, ip, port)
            except Exception as e:
                log(str(e), "ERROR")

    d.state['msgTime'] += time.perf_counter() - startTime
    log("Msgs Processed per Bot this step: " + str(botMsgCount), "DEBUG")


def sendToViwers(d):
    if len(d.viewers) == 0:
        return

    startTime = time.perf_counter()

    now = time.time()
    bmsg = d.srvSocket.serialize({
        'type': 'viewData',
                'state': d.state,
                'bots': d.bots,
                'shells': d.shells,
                'explosions': d.explosions
        })
    for src in list(d.viewers.keys()):  # we need a list of keys so we can del from the viewers dict below
        v = d.viewers[src]
        if v['lastKeepAlive'] + 10 < now:
            del d.viewers[src]
            log("Viewer " + src + " didn't send keep alive in last 10 secs and was removed.")
        else:
            try:
                # sending with a prepacked message makes it faster to send to a lot of viewers.
                d.srvSocket.sendMessage(bmsg, v['ip'], v['port'], packedAndChecked=True)
            except Exception as e:
                log(str(e), "ERROR")
                
    d.state['viewerMsgTime'] += time.perf_counter() - startTime

########################################################
# Game Logic
########################################################

def getHitSeverity(d, b1, a, b2 = None):
    '''
    hitSeverity returns a number in range 0.0 to 1.0 if b2 is None and b1 is in default class.
    hitSeverity returns a number in range 0.0 to 2.0 if b2 is a bot and both are in default class.
    
    'b1' is the bot who collided.
    'a' is the angle from b1 towards the collision.
    'b2' is the other bot that collied if this is a bot on bot collision.
    '''

    hitSeverity = b1['currentSpeed'] / 100.0 * d.getClassValue('botMaxSpeed', b1['class']) / \
                          d.conf['botMaxSpeed'] * math.cos(b1['currentDirection'] - a)
    if b2:
        # This may reduce hitSeverity if b2 is moving away from b1 or
        # increase hitSeverity if b2 moving towards b1.
        hitSeverity += b2['currentSpeed'] / 100.0 * d.getClassValue('botMaxSpeed', b2['class']) / \
                          d.conf['botMaxSpeed'] * math.cos(b2['currentDirection'] - a + math.pi)
    if hitSeverity < 0:
        hitSeverity = 0

    return hitSeverity


def findOverlapingBots(d, bots):
    """
    bots is a dict/list of bot locations: {key:{'x': x,'y': y}, ...}
    bots can also contain health: {key:{'x': x,'y': y, 'health': h}, ...}
    Return any pair (key,key) of bots that overlap, else return False
    """
    try:
        keys = list(bots.keys())
    except AttributeError:
        keys = range(len(bots))

    for i in range(0, len(keys) - 1):
        boti = bots[keys[i]]
        if 'health' not in boti or boti['health'] is not 0:
            for j in range(i + 1, len(keys)):
                botj = bots[keys[j]]
                if 'health' not in botj or botj['health'] is not 0:
                    if nbmath.distance(boti['x'], boti['y'], botj['x'], botj['y']) <= d.conf['botRadius'] * 2:
                        return [keys[i], keys[j]]

    return False


def findOverlapingBotsAndObstacles(d, bots):
    """
    bots is a dict/list of bot locations: {key:{'x': x,'y': y}, ...}
    bots can also contain health: {key:{'x': x,'y': y, 'health': h}, ...}
    Return any pair (key,i) of (key,obstacle) that overlap, else return False
    """

    try:
        keys = list(bots.keys())
    except AttributeError:
        keys = range(len(bots))

    for k in keys:
        bot = bots[k]
        if 'health' not in bot or bot['health'] is not 0:
            for obstacle in d.conf['obstacles']:
                if nbmath.distance(bot['x'], bot['y'], obstacle['x'], obstacle['y']) <= \
                        d.conf['botRadius'] + obstacle['radius']:
                    return [k, obstacle]

    return False


def mkObstacles(d, n):
    '''
    Randomly lay out obstacles with so they are at least 2 and a bit bot diameters away from any wall or other obstacle.
    '''
    obstacles = []
    rad = d.conf['arenaSize'] * d.conf['obstacleRadius'] / 100.0

    for i in range(n):
        overlaps = True
        attempts = 0
        while overlaps:
            attempts += 1
            new = {
                'x': random.random() * (d.conf['arenaSize'] - rad * 8.1) + rad * 4.1,
                'y': random.random() * (d.conf['arenaSize'] - rad * 8.1) + rad * 4.1,
                'radius': rad
                }
            overlaps = False
            for o in obstacles:
                if nbmath.distance(o['x'], o['y'], new['x'], new['y']) < o['radius'] + \
                        new['radius'] + d.conf['botRadius'] * 4.1:
                    overlaps = True
                    break
            if overlaps == False:
                obstacles.append(new)
            else:
                log("Obstacle overlapped during random layout. Trying again.", "VERBOSE")
                if attempts > 999:
                    log("Could not layout obstacles without overlapping.", "FAILURE")
                    quit()

    return obstacles


def mkJamZones(d, n):
    '''
    Randomly lay out jam zones. There are no rules about overlaps of anything else in arena.
    '''
    jamZones = []
    rad = d.conf['botRadius'] * 2

    for i in range(n):
        jamZones.append({
            'x': random.random() * d.conf['arenaSize'],
            'y': random.random() * d.conf['arenaSize'],
            'radius': rad
            })

    return jamZones


def mkStartLocations(d):
    while len(d.starts) < d.conf['gamesToPlay']:
        botsOverlap = True  # loop must run at least once.
        botsObsOverlap = True
        attempts = 0
        while botsOverlap or botsObsOverlap:
            startLocs = []
            for i in range(d.conf['botsInGame']):
                loc = {}
                loc['x'] = random.random() * (d.conf['arenaSize'] * 0.8) + (d.conf['arenaSize'] * 0.1)
                loc['y'] = random.random() * (d.conf['arenaSize'] * 0.8) + (d.conf['arenaSize'] * 0.1)
                startLocs.append(loc)

            botsOverlap = findOverlapingBots(d, startLocs)
            botsObsOverlap = findOverlapingBotsAndObstacles(d, startLocs)
            if botsOverlap:
                log("Bots overlapped during random layout, trying again.", "VERBOSE")
            elif botsObsOverlap:
                log("Bots overlapped obstacles during random layout, trying again.", "VERBOSE")

            attempts += 1
            if attempts > 999:
                log("Could not layout bots without overlapping.", "FAILURE")
                quit()

        d.startLocs.extend(startLocs)
        locIndexes = range(len(d.startLocs) - d.conf['botsInGame'], len(d.startLocs))
        if d.conf['startPermutations']:
            startLocsPerms = itertools.permutations(locIndexes)
            d.starts.extend(startLocsPerms)
        else:
            d.starts.append(list(locIndexes))

    random.shuffle(d.starts)


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
        reset speed and direction values to 0
    """
    for src, bot in d.bots.items():
        bot['health'] = 100
        bot['currentSpeed'] = 0
        bot['requestedSpeed'] = 0
        bot['currentDirection'] = 0
        bot['requestedDirection'] = 0

    # set starting location
    start = d.starts.pop()
    for i in range(d.conf['botsInGame']):
        src = d.startBots[i]
        d.bots[src]['x'] = d.startLocs[start[i]]['x']
        d.bots[src]['y'] = d.startLocs[start[i]]['y']

    # delete all shells and explosions.
    d.shells = {}
    d.explosions = {}


def step(d):
    startTime = time.perf_counter()

    d.state['gameStep'] += 1
    d.state['serverSteps'] += 1

    # for each bot that is alive, copy health to so we know what it was at the start of the step.
    aliveBots = {}
    for src, bot in d.bots.items():
        if bot['health'] != 0:
            aliveBots[src] = bot['health']

    # for all bots that are alive
    for src, bot in d.bots.items():
        if src in aliveBots:
            # change speed if needed
            if bot['currentSpeed'] > bot['requestedSpeed']:
                bot['currentSpeed'] -= d.getClassValue('botAccRate', bot['class'])
                if bot['currentSpeed'] < bot['requestedSpeed']:
                    bot['currentSpeed'] = bot['requestedSpeed']
            elif bot['currentSpeed'] < bot['requestedSpeed']:
                bot['currentSpeed'] += d.getClassValue('botAccRate', bot['class'])
                if bot['currentSpeed'] > bot['requestedSpeed']:
                    bot['currentSpeed'] = bot['requestedSpeed']

            # change direction if needed
            if bot['currentDirection'] != bot['requestedDirection']:
                if bot['currentDirection'] != bot['requestedDirection'] and bot['currentSpeed'] == 0:
                    # turn instanly if bot is not moving
                    bot['currentDirection'] = bot['requestedDirection']
                else:
                    # how much can we turn at the speed we are going?
                    turnRate = d.getClassValue('botMinTurnRate', bot['class']) \
                        + (d.getClassValue('botMaxTurnRate', bot['class']) -
                           d.getClassValue('botMinTurnRate', bot['class'])) \
                        * (1 - bot['currentSpeed'] / 100)

                    # if turn is negative and does not pass over 0 radians
                    if bot['currentDirection'] > bot['requestedDirection'] and \
                            bot['currentDirection'] - bot['requestedDirection'] <= math.pi:
                        bot['currentDirection'] -= turnRate
                        if bot['currentDirection'] <= bot['requestedDirection']:
                            bot['currentDirection'] = bot['requestedDirection']

                    # if turn is negative and passes over 0 radians, so we may need to normalize angle
                    elif bot['requestedDirection'] > bot['currentDirection'] and \
                            bot['requestedDirection'] - bot['currentDirection'] >= math.pi:
                        bot['currentDirection'] = nbmath.normalizeAngle(bot['currentDirection'] - turnRate)
                        if bot['currentDirection'] <= bot['requestedDirection'] and bot['currentDirection'] >= bot['requestedDirection'] - math.pi:
                            bot['currentDirection'] = bot['requestedDirection']

                    # if turn is positive and does not pass over 0 radians
                    elif bot['requestedDirection'] > bot['currentDirection'] and \
                            bot['requestedDirection'] - bot['currentDirection'] <= math.pi:
                        bot['currentDirection'] += turnRate
                        if bot['requestedDirection'] <= bot['currentDirection']:
                            bot['currentDirection'] = bot['requestedDirection']

                    # if turn is positive and passes over 0 radians
                    elif bot['currentDirection'] > bot['requestedDirection'] and \
                            bot['currentDirection'] - bot['requestedDirection'] >= math.pi:
                        bot['currentDirection'] = nbmath.normalizeAngle(bot['currentDirection'] + turnRate)
                        if bot['currentDirection'] >= bot['requestedDirection'] and bot['currentDirection'] <= bot['requestedDirection'] + math.pi:
                            bot['currentDirection'] = bot['requestedDirection']
            # move bot
            if bot['currentSpeed'] != 0:
                bot['x'], bot['y'] = nbmath.project(bot['x'], bot['y'],
                                        bot['currentDirection'],
                                        bot['currentSpeed'] / 100.0 * d.getClassValue('botMaxSpeed', bot['class']))

    # set starting hitSeverity to 0 for all robots. hitSeverity == 0 means robot did not 
    # hit anything this step.
    for src, bot in d.bots.items():
        bot['hitSeverity'] = 0.0

    # do until we get one clean pass where no bot hitting wall, obstacle or other bot.
    foundOverlap = True
    while foundOverlap:
        foundOverlap = False

        # detect if bots hit walls. if they, did move them so they are just barely not touching,
        for src, bot in d.bots.items():
            hitSeverity = 0
            if bot['x'] - d.conf['botRadius'] < 0:
                # hit left side
                bot['x'] = d.conf['botRadius'] + 1
                hitSeverity = getHitSeverity(d, bot, math.pi)
            if bot['x'] + d.conf['botRadius'] > d.conf['arenaSize']:
                # hit right side
                bot['x'] = d.conf['arenaSize'] - d.conf['botRadius'] - 1
                hitSeverity = getHitSeverity(d, bot, 0)
            if bot['y'] - d.conf['botRadius'] < 0:
                # hit bottom side
                bot['y'] = d.conf['botRadius'] + 1
                hitSeverity = getHitSeverity(d, bot, math.pi * 3 / 2)
            if bot['y'] + d.conf['botRadius'] > d.conf['arenaSize']:
                # hit top side
                bot['y'] = d.conf['arenaSize'] - d.conf['botRadius'] - 1
                hitSeverity = getHitSeverity(d, bot, math.pi/2)
    
            if hitSeverity:
                foundOverlap = True
                bot['hitSeverity'] = max(bot['hitSeverity'], hitSeverity)

        # detect if bots hit obstacles, if the did move them so they are just barely not touching,
        overlap = findOverlapingBotsAndObstacles(d, d.bots)
        while overlap:
            foundOverlap = True
            b = d.bots[overlap[0]]
            o = overlap[1]
            # find angle to move bot directly away from obstacle
            a = nbmath.angle(o['x'], o['y'], b['x'], b['y'])
            # find min distance to move bot so it don't touch (plus 0.5 for safety).
            distance = d.conf['botRadius'] + o['radius'] + 0.5 - nbmath.distance(o['x'], o['y'], b['x'], b['y'])
            # move bot
            b['x'], b['y'] = nbmath.project(b['x'], b['y'], a, distance)
            # record damage
            hitSeverity = getHitSeverity(d, b, a + math.pi)
            b['hitSeverity'] = max(b['hitSeverity'], hitSeverity)
            # check for more bots overlapping
            overlap = findOverlapingBotsAndObstacles(d, d.bots)
                    
        # detect if bots hit other bots, if the did move them so they are just barely not touching,
        overlap = findOverlapingBots(d, d.bots)
        while overlap:
            foundOverlap = True
            b1 = d.bots[overlap[0]]
            b2 = d.bots[overlap[1]]
            # find angle to move bot directly away from each other
            a = nbmath.angle(b1['x'], b1['y'], b2['x'], b2['y'])
            # find min distance to move each bot so they don't touch (plus 0.5 for saftly).
            between = nbmath.distance(b1['x'], b1['y'], b2['x'], b2['y'])
            distance = between / 2 - (between - d.conf['botRadius']) + 0.5
            # move bots
            b1['x'], b1['y'] = nbmath.project(b1['x'], b1['y'], a + math.pi, distance)
            b2['x'], b2['y'] = nbmath.project(b2['x'], b2['y'], a, distance)
            # record damage
            hitSeverity = getHitSeverity(d, b1, a, b2)
            b1['hitSeverity'] = max(b1['hitSeverity'], hitSeverity)
            b2['hitSeverity'] = max(b2['hitSeverity'], hitSeverity)
            # check for more bots overlapping
            overlap = findOverlapingBots(d, d.bots)

    # give damage (only once this step) to bots that hit things. Also stop them.
    for src, bot in d.bots.items():
        if bot['hitSeverity']:
            if d.conf['simpleCollisions']:
                bot['hitSeverity'] = 1
            bot['health'] = max(0, bot['health'] - bot['hitSeverity'] * d.conf['hitDamage'] * d.getClassValue('botArmor', bot['class']))
            bot['currentSpeed'] = 0
            bot['requestedSpeed'] = 0
        del bot['hitSeverity']

    # for all shells
    for src in list(d.shells.keys()):
        shell = d.shells[src]

        # remember shells start point before moving
        oldx = shell['x']
        oldy = shell['y']

        # move shell
        distance = min(d.getClassValue('shellSpeed', d.bots[src]['class']), shell['distanceRemaining'])
        shell['x'], shell['y'] = nbmath.project(shell['x'], shell['y'], shell['direction'], distance)
        shell['distanceRemaining'] -= distance

        # did shell hit an obstacle?
        shellHitObstacle = False
        for o in d.conf['obstacles']:
            if nbmath.intersectLineCircle(oldx, oldy, shell['x'], shell['y'], o['x'], o['y'], o['radius']):
                shellHitObstacle = True

        # if did not hit an obstacle and shell's explosion would touch inside of arena
        if not shellHitObstacle and \
           (shell['x'] > d.getClassValue('explRadius', d.bots[src]['class']) * -1 and shell['x'] < d.conf['arenaSize'] + d.getClassValue('explRadius', d.bots[src]['class']) and
                shell['y'] > d.getClassValue('explRadius', d.bots[src]['class']) * -1 and shell['y'] < d.conf['arenaSize'] + d.getClassValue('explRadius', d.bots[src]['class'])):

            # if shell has reached it destination then explode.
            if shell['distanceRemaining'] <= 0:
                # apply damage to bots.
                for k, bot in d.bots.items():
                    if bot['health'] > 0:
                        distance = nbmath.distance(bot['x'], bot['y'], shell['x'], shell['y'])
                        if distance < d.getClassValue('explRadius', d.bots[src]['class']):
                            damage = d.getClassValue('explDamage', d.bots[src]['class']) * (1 - distance / d.getClassValue('explRadius', d.bots[src]['class']))
                            bot['health'] = max(0, bot['health'] - (damage * d.getClassValue('botArmor', bot['class'])))
                            # allow recording of inflicting damage that is greater than health of hit robot.
                            # also record damage to oneself.
                            d.bots[src]['shellDamage'] += damage

                # store the explosion so viewers can display it. we can't use src as index because it is possible for two explosions
                # from same bot to exist (but not likly).
                d.explosions[d.state['explIndex']] = {
                    'x': shell['x'],
                    'y': shell['y'],
                    'stepsAgo': 0,
                    'src': src  # this is needed by viewer to color this explosion based on the bot who fired it.
                    }
                d.state['explIndex'] += 1
                if d.state['explIndex'] > 65000:
                    d.state['explIndex'] = 0

                # this shell exploed so remove it
                del d.shells[src]
        else:
            # shell hit obstacle or left arena so remove it without exploding
            del d.shells[src]

    # Remove old explosions and add 1 to other explosions stepsAgo.
    # Note, We only keep these around so the viewer can do a nice animation
    # over a number of steps before they are removed.
    for key in list(d.explosions.keys()):
        expl = d.explosions[key]
        if expl['stepsAgo'] == d.conf['keepExplosionSteps']:
            del d.explosions[key]
        else:
            expl['stepsAgo'] += 1

    # find how many points bots that died this step will get. (Based on how many bots have died previouly)
    if len(aliveBots) == d.conf['botsInGame']:
        points = 0  # first to die
    elif len(aliveBots) > d.conf['botsInGame'] / 2:
        points = 2  # died in first half
    else:
        points = 5  # died in second half

    # Kill all bots if we have reached the max steps and there is still more than one bot alive.
    if d.state['gameStep'] == d.conf['stepMax'] and len(aliveBots) != 1:
        log("Game reached stepMax with more than one bot alive. Killing all bots.")
        for src in aliveBots:
            d.bots[src]['health'] = 0

    # Assign points to bots that died this turn
    for src in list(aliveBots.keys()):
        if d.bots[src]['health'] == 0:
            d.bots[src]['points'] += points
            del aliveBots[src]

    # If only one bot is left then end game.
    if len(aliveBots) == 1:
        src = list(aliveBots.keys())[0]
        d.bots[src]['winHealth'] += d.bots[src]['health']
        d.bots[src]['winCount'] += 1
        d.bots[src]['health'] = 0
        d.bots[src]['points'] += 10  # last robot (winner)
        del aliveBots[src]

    d.state['stepTime'] += time.perf_counter() - startTime


########################################################
# Stats and Points Logging
########################################################

def logScoreBoard(d):
    now = time.time()
    totalRecv = sum(d.srvSocket.recv.values())
    totalSent = sum(d.srvSocket.sent.values())
    output = "\n\n                ------ Score Board ------" +\
        "\n               Tournament Time: " + '%.3f' % (now - d.state['tourStartTime']) + " secs." +\
        "\n                         Games: " + str(d.state['gameNumber']) +\
        "\n             Average Game Time: " + '%.3f' % ((now - d.state['tourStartTime']) / max(1, d.state['gameNumber'])) + " secs." +\
        "\n                         Steps: " + str(d.state['serverSteps']) +\
        "\n          Average Steps / Game: " + '%.3f' % (d.state['serverSteps'] / max(1, d.state['gameNumber'])) +\
        "\n                      Run Time: " + '%.3f' % (time.time() - d.state['startTime']) + " secs." +\
        "\nTime Processing Robot Messages: " + '%.3f' % (d.state['msgTime']) + " secs." +\
        "\n  Time Sending Viewer Messages: " + '%.3f' % (d.state['viewerMsgTime']) + " secs." +\
        "\n                   Messages In: " + str(totalRecv) +\
        "\n                  Messages Out: " + str(totalSent) +\
        "\n              Messages Dropped: " + str(d.state['dropCount']) +\
        "\n             Messages / Second: " + '%.3f' % ((totalRecv + totalSent) / float(time.time() - d.state['startTime'])) +\
        "\n         Time Processing Steps: " + '%.3f' % (d.state['stepTime']) + " secs." +\
        "\n                Steps / Second: " + '%.3f' % (d.state['serverSteps'] / float(max(1, time.time() - d.state['tourStartTime']))) +\
        "\n                 Time Sleeping: " + '%.3f' % (float(d.state['sleepTime'])) + " secs." +\
        "\n            Average Sleep Time: " + '%.6f' % (float(d.state['sleepTime']) / max(1, d.state['sleepCount'])) + " secs." +\
        "\n     Steps Slower Than stepSec: " + str(d.state['longStepCount']) + f" ({float(d.state['longStepCount']) / float(max(1,d.state['serverSteps'])) * 100.0:>4.2f}%)" +\
        "\n\n" +\
        f"  {' ':>16}" +\
        f"  {'---- Score -----':>16}" +\
        f"  {'------ Wins -------':>19}" +\
        f"  {'--------- CanonFired ----------':>31}" +\
        f"  {' ':<21}" +\
        "\n" +\
        f"  {'Name':>16}" +\
        f"  {'Points':>10}" +\
        f"  {'%':>4}" +\
        f"  {'Count':>7}" +\
        f"  {'AvgHealth':>10}" +\
        f"  {'Count':>7}" +\
        f"  {'AvgDamage':>10}" +\
        f"  {'TotDamage':>10}" +\
        f"  {'IP:Port':<21}" +\
        "\n ------------------------------------------------------------------------------------------------------------------"

    botSort = sorted(d.bots, key=lambda b: d.bots[b]['points'], reverse=True)

    totalPoints = 0.0
    for src in botSort:
        totalPoints += d.bots[src]['points']
    if totalPoints == 0:
        totalPoints = 1.0

    for src in botSort:
        bot = d.bots[src]
        output += "\n" +\
            f"  {bot['name']:>16}" +\
            f"  {bot['points']:>10}" +\
            f"  {float(bot['points'])/totalPoints*100.0:>4.1f}" +\
            f"  {bot['winCount']:>7}" +\
            f"  {float(bot['winHealth']) / max(1,bot['winCount']):>10.2f}" +\
            f"  {bot['firedCount']:>7}" +\
            f"  {float(bot['shellDamage']) / max(1,bot['firedCount']):>10.2f}" + \
            f"  {float(bot['shellDamage']):>10.2f}" + \
            f"  {src:<21}"

    output += "\n ------------------------------------------------------------------------------------------------------------------\n\n"

    log(output)

########################################################
# Main Loop
########################################################


class Range(argparse.Action):
    def __init__(self, min=None, max=None, *args, **kwargs):
        self.min = min
        self.max = max
        kwargs["metavar"] = "%d-%d" % (self.min, self.max)
        super(Range, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        if not (self.min <= value <= self.max):
            msg = 'invalid choice: %r (choose from [%d-%d])' % \
                (value, self.min, self.max)
            raise argparse.ArgumentError(self, msg)
        setattr(namespace, self.dest, value)
        

def quit(signal=None, frame=None):
    global d
    log(d.srvSocket.getStats())
    logScoreBoard(d)
    log("Quiting", "INFO")
    exit()


def main():
    global d  # d is global so quit() can access it.
    d = SrvData()

    random.seed()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-ip', metavar='Server_IP', dest='serverIP', type=nbipc.argParseCheckIPFormat,
                        default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='Server_Port', dest='serverPort', type=int,
                        default=20000, help='My port number')
    parser.add_argument('-name', metavar='Server_Name', dest='serverName', type=str,
                        default="Netbots Server", help='Name displayed by connected viewers.')
    parser.add_argument('-games', metavar='int', dest='gamesToPlay', type=int,
                        default=10, help='Games server will play before quiting.')
    parser.add_argument('-bots', metavar='int', dest='botsInGame', type=int,
                        default=4, help='Number of bots required to join before game can start.')
    parser.add_argument('-stepsec', metavar='sec', dest='stepSec', type=float,
                        default=0.05, help='How many seconds between server steps.')
    parser.add_argument('-stepmax', metavar='int', dest='stepMax', type=int,
                        default=1000, help='Max steps in one game.')
    parser.add_argument('-droprate', metavar='int', dest='dropRate', type=int,
                        default=11, help='Drop over nth message, best to use primes. 0 == no drop.')
    parser.add_argument('-msgperstep', metavar='int', dest='botMsgsPerStep', type=int,
                        default=4, help='Number of msgs from a bot that server will respond to each step.')
    parser.add_argument('-arenasize', dest='arenaSize', type=int, min=100, max=32767, action=Range,
                        default=1000, help='Size of arena.')
    parser.add_argument('-botradius', metavar='int', dest='botRadius', type=int,
                        default=25, help='Radius of robots.')
    parser.add_argument('-explradius', metavar='int', dest='explRadius', type=int,
                        default=75, help='Radius of explosions.')
    parser.add_argument('-botmaxspeed', metavar='int', dest='botMaxSpeed', type=int,
                        default=5, help="Robot distance traveled per step at 100%% speed")
    parser.add_argument('-botaccrate', metavar='float', dest='botAccRate', type=float,
                        default=2.0, help='%% robot can accelerate (or decelerate) per step')
    parser.add_argument('-shellspeed', metavar='int', dest='shellSpeed', type=int,
                        default=40, help='Distance traveled by shell per step.')
    parser.add_argument('-hitdamage', metavar='int', dest='hitDamage', type=int,
                        default=10, help='Damage a robot takes from hitting wall or another bot.')
    parser.add_argument('-expldamage', metavar='int', dest='explDamage', type=int,
                        default=10, help='Damage bot takes from direct hit from shell.')
    parser.add_argument('-obstacles', metavar='int', dest='obstacles', type=int,
                        default=0, help='How many obstacles does the arena have.')
    parser.add_argument('-obstacleradius', metavar='int', dest='obstacleRadius', type=int,
                        default=5, help='Radius of obstacles as %% of arenaSize.')
    parser.add_argument('-jamzones', metavar='int', dest='jamZones', type=int,
                        default=0, help='How many jam zones does the arena have.')
    parser.add_argument('-allowclasses', dest='allowClasses', action='store_true',
                        default=False, help='Allow robots to specify a class other than default.')
    parser.add_argument('-simplecollisions', dest='simpleCollisions', action='store_true',
                        default=False, help='Uses the simple collision system, damage taken is the same as -hitdamage')
    parser.add_argument('-startperms', dest='startPermutations', action='store_true',
                        default=False, help='Use all permutations of each set of random start locations.')
    parser.add_argument('-scanmaxdistance', metavar='int', dest='scanMaxDistance', type=int,
                        default=1415, help='Maximum distance a scan can detect a robot.')
    parser.add_argument('-noviewers', dest='noViewers', action='store_true',
                        default=False, help='Do not allow viewers.')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    args = parser.parse_args()

    setLogLevel(args.debug, args.verbose)
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
    d.conf['obstacleRadius'] = args.obstacleRadius
    d.conf['obstacles'] = mkObstacles(d, args.obstacles)
    d.conf['jamZones'] = mkJamZones(d, args.jamZones)
    d.conf['allowClasses'] = args.allowClasses
    d.conf['simpleCollisions'] = args.simpleCollisions
    d.conf['startPermutations'] = args.startPermutations
    d.conf['scanMaxDistance'] = args.scanMaxDistance
    d.conf['noViewers'] = args.noViewers

    mkStartLocations(d)

    log("Server Name: " + d.conf['serverName'])
    log("Server Version: " + d.conf['serverVersion'])
    log("Argument List:" + str(sys.argv))

    log("Server Configuration: " + str(d.conf), "VERBOSE")

    try:
        d.srvSocket = nbipc.NetBotSocket(args.serverIP, args.serverPort)
    except Exception as e:
        log(str(e), "FAILURE")
        quit()

    nextStepAt = time.perf_counter() + d.conf['stepSec']
    while True:
        aliveBots = 0
        for src, bot in d.bots.items():
            if bot['health'] != 0:
                aliveBots += 1

        # only count slow steps if we actually process a step this time around.
        countSlowStep = False

        if aliveBots > 0:  # if there is an ongoing game
            countSlowStep = True
            step(d)
        elif len(d.bots) == d.conf['botsInGame']:  # if we have enough bots to start playing
            if not d.state['tourStartTime']:
                d.state['tourStartTime'] = time.time()

            if d.conf['gamesToPlay'] != d.state['gameNumber']:
                logScoreBoard(d)
                initGame(d)
            else:
                log("All games have been played.")
                quit()

        recvReplyMsgs(d)

        sendToViwers(d)

        ptime = time.perf_counter()
        if ptime < nextStepAt:
            d.state['sleepCount'] += 1
            d.state['sleepTime'] += nextStepAt - ptime
            while ptime < nextStepAt:
                ptime = time.perf_counter()
        elif countSlowStep:
            d.state['longStepCount'] += 1
            log("Server running slower than " + str(d.conf['stepSec']) + " sec/step.", "VERBOSE")

        nextStepAt = ptime + d.conf['stepSec']


if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)
    main()
