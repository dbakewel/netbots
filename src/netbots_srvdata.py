class SrvData:
    srvSocket = None

    conf = {
        # Static vars (some are settable at start up by server command line switches and then do not change after that.)
        'serverName': "NetBot Server",
        'serverVersion': "1.3.0+ (develop)",

        # Game and Tournament
        'botsInGame': 4,  # Number of bots required to join before game can start.
        'gamesToPlay': 10,  # Number of games to play before server quits.
        'stepMax': 1000,  # After this many steps in a game all bots will be killed
        # Amount of time server targets for each step. Server will sleep if game is running faster than this.
        'stepSec': 0.05,
        'startPermutations':  False,  # Use all permutations of each set of random start locations.
        'advancedCollisions': False,  # Use advanced collision, affected by -hitdamage
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
        'hitDamage': 1,  # Damage a bot takes from hitting wall or another bot
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
        'classFields': ('botMaxSpeed', 'botAccRate', 'botMinTurnRate', 'botMaxTurnRate', 'botArmor'),
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
                'botArmor': 0.77  # multiplier of robot damage taken
                },
            
            'light': {
                # Speeds and Rates of Change
                'botMaxSpeed': 1.4,  # multiplier for bot max speed
                'botAccRate': 1.25,  # multiplier for bot acceleration rate
                'botMinTurnRate': 1.2,  # multiplier for bot turning rate at 100% speed
                'botMaxTurnRate': 1.6666666666,  # multiplier for bot turning rate at 0% speed
                'botArmor': 1.33  # multiplier of robot damage taken
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
        'winCount': 0
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