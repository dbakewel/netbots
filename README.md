# NetBots

NetBots is a python programming game. The game consists of a number of robots, 4 by default, that battle in an arena until only one remains. To play, a python program must be written. The program can control the robot's speed and direction, scan for enemy robots and fire exploding shells from it's canon. Robots suffer damage if they hit the edge of the arena, hit other robots, or are hit by an exploding shell. The game ends when only one robot remains or the maximum number of game steps is reached. Normally, many games are played in a tournament to determine which robot is the overall winner.

NetBots is inspired by [RobotWar](https://en.wikipedia.org/wiki/RobotWar) from the 1970s. RobotWar has been cloned many times, one popular example is [Crobots](https://en.wikipedia.org/wiki/Crobots). 


### How is NetBots different?

NetBots differs from RobotWar, and it's clones by being real-time and network centric. The server and robots each run in separate processes and can run on the same or separate computers. The server runs a specific rate (steps/second) regardless of if robots can keep up. The server will keep playing the game even if robots crash. Additionally, the server emulates an unreliable network where message (packet) loss is common. Writing programs to deal with the real-time nature and network unreliability provides additional programming challenges and advantages to programmers who get it right.


### Netbots as a Learning Tool

NetBots can be used in a learning environment. Students can be challenged in two ways:

1. Learn to write programs that must interact with a constantly changing real-time environment with limited information and limited control.
2. Learn about networking, the impact of unreliable networks, and synchronous vs asynchronous programing.

See Proposed Learning Goals below.


---


# How To Run NetBots


## Prerequisites


### Python 3

NetBots uses Python 3 (tested on python 3.7.3) which can be installed from [https://www.python.org/downloads/](https://www.python.org/downloads/) .

Only the standard python 3 libraries are required.


### NetBots Git Repository

The NetBots code can be cloned with git from: [https://github.com/dbakewel/netbots.git](https://github.com/dbakewel/netbots.git) or downloaded in zip form from: [https://github.com/dbakewel/netbots/archive/master.zip](https://github.com/dbakewel/netbots/archive/master.zip)


### Firewall Settings

If you want to run NetBots across a network then the ports you choose must be open in the firewall for two way UDP traffic. By default, these ports are in the range 20000 - 20020 range but any available UDP ports can be used.


## Running the Demo

On windows, **double click "rundemo.bat"** in the root of the NetBots directory. 

The rundemo script will start 6 processes on the local computer: 1 server, 1 viewer, and 4 robots. A default tournament (10 games) will run and then the server will quit. Each process will send its output to it's own cmd window. The title of the window indicates what is running it in. Each process can be quit by clicking in the window and pressing "Ctrl-C" (cmd window stays open) or clicking the close box (cmd window closes). Use "Close all windows" in the task bar to quickly quit all processes. 


## Running a Tournament

There are two options available on the netbots server that are useful for tournaments. The first lets you change the number of games (**-games**) in the tournament. If robots have similar skills then playing more games will flush out which robot really is best. 

The second option (**-stepsec**) allows you to speed up the NetBots server. Most modern computers can run NetBots 10 times faster (or more) than the default (0.1 sec/step or 10 steps/sec). The server will produce warnings if it can't keep up with the requested speed. If only a few of these warnings appear then it will not affect the game however if many warnings appear you should stop the server and reduce it's target speed.

For example, to run a 1000 game tournament at 10 times faster (0.01 sec/step or 100 steps/sec) use:

```
python netbots_server -games 1000 -stepsec 0.01
```

## Running on Separate Computers

By default NetBots only listens on localhost 127.0.0.1 which does not allow messages to be sent or received between computers. To listen on all network interfaces, and allow messages from other computers, use ```-ip 0.0.0.0```. For example:

Assuming:
*   computer 1 has IP address of 192.168.1.10
*   computer 2 has IP address of 192.168.1.30

The server is run on computer 1 with: 

```
python netbots_server.py -ip 0.0.0.0 -p 20000
```

The server will listen on 127.0.0.1 and 192.168.1.10

A robot can be run on Computer 2 with: 

```
python robot.py -ip 0.0.0.0 -p 20010 -sip 192.168.1.10 -sp 20000
```

A robot can also be run on Computer 1 will the default 127.0.0.01 with: 

```
python robot.py -p 20010 -sp 20000
```

Note that even though the robots on computer 1 and computer 2 use the same port (20010) they are on separate computers so it works. If you try running two robots on the same port on the same computer you will get an error.

## Command Line Help

The server, viewer, and demo robots all allow some customization with command line switches. Run each with the **-h** switch to display help. For example:

```
D:\netbots\src>python src\netbots_server.py -h
usage: netbots_server.py [-h] [-ip Server_IP] [-p Server_Port]
                         [-name Server_Name] [-games int] [-bots int]
                         [-stepsec sec] [-stepmax int] [-droprate int]
                         [-msgperstep int] [-arenasize int] [-botradius int]
                         [-explradius int] [-botmaxspeed int]
                         [-botaccrate int] [-shellspeed int] [-hitdamage int]
                         [-expldamage int] [-obstacles int]
                         [-obstacleradius int] [-jamzones int] [-stats sec]
                         [-debug] [-verbose]

optional arguments:
  -h, --help           show this help message and exit
  -ip Server_IP        My IP Address (default: 127.0.0.1)
  -p Server_Port       My port number (default: 20000)
  -name Server_Name    Name displayed by connected viewers. (default: Netbots
                       Server)
  -games int           Games server will play before quiting. (default: 10)
  -bots int            Number of bots required to join before game can start.
                       (default: 4)
  -stepsec sec         How many seconds between server steps. (default: 0.1)
  -stepmax int         Max steps in one game. (default: 1000)
  -droprate int        Drop over nth message. 0 == no drop. (default: 10)
  -msgperstep int      Number of msgs from a bot that server will respond to
                       each step. (default: 4)
  -arenasize int       Size of arena. (default: 1000)
  -botradius int       Radius of robots. (default: 25)
  -explradius int      Radius of explosions. (default: 75)
  -botmaxspeed int     Robot distance traveled per step at 100% speed
                       (default: 5)
  -botaccrate int      % robot can accelerate (or decelerate) per step
                       (default: 5)
  -shellspeed int      Distance traveled by shell per step. (default: 50)
  -hitdamage int       Damage a robot takes from hitting wall or another bot.
                       (default: 2)
  -expldamage int      Damage bot takes from direct hit from shell. (default:
                       20)
  -obstacles int       How many obstacles does the arena have. (default: 0)
  -obstacleradius int  Radius of obstacles as % of arenaSize. (default: 5)
  -jamzones int        How many jam zones does the arena have. (default: 0)
  -stats sec           How many seconds between printing server stats.
                       (default: 60)
  -debug               Print DEBUG level log messages. (default: False)
  -verbose             Print VERBOSE level log messages. Note, -debug includes
                       -verbose. (default: False)
```

---


# How To Write A Robot


## Python Basics

To write a robot you should have a basic familiarity with python 3. The links below will help:

*   [Python Introductions](https://docs.python-guide.org/intro/learning/)
*   Important Python types used in netbots: [str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str), [int and float](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex), [dict](https://docs.python.org/3/tutorial/datastructures.html#dictionaries).
*   Other important python skills: [default arguments](https://www.geeksforgeeks.org/default-arguments-in-python/) and [exceptions](https://docs.python.org/3/tutorial/errors.html): 


## Robot / Server Communication

Netbots robots use the netbots_ipc module to communicate with the server. All messages that can be sent to the server and what will be returned is documented below in the module reference. The netbots_ipc module supports both synchronous and asynchronous communication. The synchronous method allows only one message to be processed by the server per step while the asynchronous method allows up to 4 messages per step. It's recommended that all programmers start with the synchronous method since it eliminates issues of messages being dropped and works more like a function call.

Robots must start all new communications with a server using a **joinRequest** message. Once a robot has joined, it must keep asking the server if the game has started by using the **getInfoRequest** Message. Once the game has started the robot can use any of the other message types to play the game until either their health is 0 or they win and the game ends. When a game ends the server will immediately start the next game and robots need to detect this event, again using the getInfoRequest. This continues until the server has completed the tournament and quits.

It's important to understand that the server will not wait for robots to send messages. Once a robot joins the server successfully, the server will play the tournament regardless of if the robot continues to send messages or not. It is up to the robot to send request messages to the server, to recognize when new games have started, and to realize that their health is 0 (server will return errors when robot is dead).

See netbots_ipc module reference below for details.

## Coordinates and Angles

The game is played on a square grid. By default the grid is 1000 units on each side with (x=0, y=0) in the bottom left corner. Angles are always in radians with 0 radians in the positive x direction and increasing counter-clockwise.

![Arena Coordinates and Angles](arena.png "Arena Coordinates and Angles")

## Demo Robots

The best way to write your own robot is to start with a demo robot. There are five demo robots in the "robots" folder. They demonstrate most of the netbots message types as well as a standard way to implement a robot. These robots all use the synchronous netbots_ipc method.

**sittingduck.py**: Sitting Duck is a very basic template where the robot does nothing at all. Reviewing this robot will help you understand the minimum requirements of a robot.

**hideincorner.py**: Hide in Corner demonstrates how to compute an angle between two points and move in that direction.

**wallbanger.py**: Wall Banger demonstrates how to use the python random module.

**train.py**: Is a more complex moving robot that monitors its location and avoids hitting walls.

**lighthouse.py**: Lighthouse demonstrates scanning and firing the robot's canon.


---


# Module Reference


## netbots_log (debug output)

The netbots_log module prints output to the console. Best practice is to use the log() rather than print(). log() will include the time and function name which can help with debugging. 

notbots_log allows turning detailed output on/off without having to remove log lines from your code. You can turn DEBUG and VERBOSE output on/off from the command line with -debug and -verbose. Use -h switch to learn more.

For convenience, import just the functions rather then the entire module with:

```
from netbots_log import log
from netbots_log import setLogLevel
```

This allows you to call log() and setLogLevel() without the module prefix.


### Functions

**log(msg, level='INFO')**

Print msg to standard output in the format: ```<level> <time> <function>: <msg>```

level is of type str and should be one of DEBUG, VERBOSE, INFO, WARNING, ERROR, or FAILURE. Use level as follows:


*   DEBUG: Very detailed information, such as network messages.
*   VERBOSE: Detailed information about normal function of program.
*   INFO: Information about the normal functioning of the program. (default level).
*   WARNING: Something unexpected happened but program flow can continue.
*   ERROR: Can not continue as planned but don't need to quit or reinitialize.
*   FAILURE: program will need to quit or reinitialize.


**setLogLevel(debug=False, verbose=False)**

Turn DEBUG and VERBOSE printing on or off. Both are off by default. Note, debug = True will set verbose = True.


## netbots_math

netbots_math is a convenience module with geometry/trigonometry functions. Note, all angles are in radians.

See python [math](https://docs.python.org/3/library/math.html) module for other useful math functions, such as math.degrees() and math.radians(), and constants, such as the value of pi (math.pi).


### Functions

**angle(x1, y1, x2, y2)**

Return angle from (x1,y1) to (x2,y2). i.e.


**contains(x1, y1, startRad, endRad, x2, y2)**

Return distance between points only if point falls inside a specific range of angles, otherwise return 0. startRad and endRad should be in the range 0 to 2pi.

In pseudocode:

```
if angle from (x1,y1) to (x2,y2) is between startRad and 
  counter clockwise to endRad then
    return distance from (x1,y1) to (x2,y2)
else
    return 0
```


**distance(x1, y1, x2, y2)**

Return distance between (x1,y1) and (x2,y2)

**intersectLineCircle(x1,y1,x2,y2,cx,cy,cradius)**

Return True if line segment between (x1,y1) and (x2,y2) intersects circle centered at (cx,cy) with radius cradius, or if line segment is entirely inside circle. 


**normalizeAngle(a)**

Return a in range 0 - 2pi.


**project(x, y, rad, dis)**

Return point (x',y') where angle from (x,y) to (x',y') is rad and distance from (x,y) to (x',y') is dis.


## netbots_ipc (Interprocess Communication)

NetBots communicates using UDP/IP datagrams and messages are serialized with MessagePack, however robot programmers do not need to understand these details. The netbots_ipc module abstracts these details with the NetBotSock class while still leaving open the option for programmers to get into the details if they choose. netbots_ipc also defines the message format (protocol) for communication between robot and server. A few useful validation functions are also provided.


### NetBotSock Class Methods

**__init__(self, sourceIP, sourcePort, destinationIP='127.0.0.1', destinationPort=20000)**

Create UDP socket and bind it to listen on sourceIP and sourcePort.

*   sourceIP: IP the socket will listen on. This must be 127.0.0.1 (localhost), 0.0.0.0 (all interfaces), or a valid IP address on the computer.
*   sourcePort: port to listen on. This is an integer number.
*   destinationIP and destinationPort are passed to setDestinationAddress()

Returns NetBotSocket object.

Raises socket related exceptions.


**getStats(self)**

Return str of NetBotSocket statistics.


**recvMessage(self)**

Checks the socket receive buffer and returns message, ip, and port only if a valid message is immediately ready to receive. recvMessage is considered **asynchronous** because it will not wait for a message to arrive before raising an exception.

Returns msg, ip, port.

*   msg: a valid message
*   ip: IP address of the sender
*   port: port of the sender

If the message is of type "Error" then it will be returned just like any other message. No exception will be raised.

Raises NetBotSocketException if the message is not a valid format.

Immediately raises NetBotSocketException if the receive buffer is empty.

Note, the text above assumes the socket timeout is set to 0 (non-blocking), which is the default in NetBotSocket.


**sendMessage(self, msg, destinationIP=None, destinationPort=None)**

Sends msg to destinationIP:destinationPort and then returns immediately. sendMessage is considered **asynchronous** because it does not wait for a reply message and returns no value. Therefore there is no indication if msg will be received by the destination.

Raises NetBotSocketException exception if the msg is not a valid format. (see Messages below)

If destinationIP or destinationPort is not provided then the default will be used (see setDestinationAddress()).


**sendRecvMessage(self, msg, destinationIP=None, destinationPort=None, retries=10, delay=None, delayMultiplier=1.2)**

Sends msg to destinationIP:destinationPort and then waits and returns the reply. sendRecvMessage is considered **synchronous** because it will not return until a reply is received. Programmers can think of this much like a normal function call.

msg must be a valid message.

If destinationIP or destinationPort is not provided then the default will be used (see setDestinationAddress()).

Raises NetBotSocketException exception if the sent or received msg is not a valid format or if the received message is of type "Error".

If no reply is received then the message will be sent again (retried) in case it was dropped by the network. If the maximum number of retries is reached then a NetBotSocketException exception will be raised.

Note, sendRecvMessage (synchronous) should not be mixed with sendMessage and recvMessage (asynchronous) without careful consideration. When sendRecvMessage is called it will discard all messages that are waiting to be received by the robot that do not match the reply it is looking for.


**setDestinationAddress(self, destinationIP, destinationPort)**

Set default destination used by NetBotSocket methods when destination is not provided in method calls.

Returns no value

Raises NetBotSocketException exception if destinationIP or destinationPort are not valid.



### Functions

**formatIpPort(ip, port)**

Formats ip and port into a single string. eg. 127.168.32.11:20012


**isValidIP(ip)**

Returns True if ip is valid IP address, otherwise returns False.


**isValidMsg(msg)**

Returns True if msg is a valid message, otherwise returns False.


**isValidPort(p)**

Returns True if p is valid port number, otherwise returns False.


### Messages

All messages are python dict type and contain a 'type' key with a value of type str. All message key/value pairs are described below in the format:

```
{ 'type': <str>, '<key>': <type>, '<key>': <type>, ... }
```

All keys are type str and types may include acceptable min and max values. For example, messages of type 'setDirectionRequest' have a str key 'requestedDirection' with value of type float between 0 and 2pi:


```
{ 
    'type': 'setDirectionRequest', 
    'requestedDirection': float (min 0, max 2pi)
}
```


There are two special keys that can optionally be added to any request message. These keys are not used by the server but will be copied to the reply message by the server. This can be very useful to track asynchronous messages:

*   'replyData': any of int, float, str, dict, or list
*   'msgID': int

Note, msgID is used by NetBotSocket.sendrecvMessage() so should not be used by robot code directly.


### Message Reference

Messages described below are grouped by request (sent by robot) and the expected reply (sent by server). All keys listed below are required. 

IMPORTANT: When a robot's health == 0, only joinRequest and getInfoRequest will return the appropriate reply. Other request messages will return a reply of type "Error" when a robot's health == 0.


**Join**

A robot must send a joinRequest before any other message type. The server will return a joinReply if the robot has successfully joined, otherwise a message of type "Error" will be returned. Sending other message types before a join request will return a message of type "Error".


Robot Sends: 

Format: `{ 'type': 'joinRequest', 'name': str }`

Example: `{ 'type': 'joinRequest', 'name': 'Super Robot V3' }`

'name' will be displayed by the server and viewer in game results.


Server Returns: 

Format: `{ 'type': 'joinReply', 'conf': dict } `or Error

Example: 

```
{ 
'type': 'joinReply', 
'conf': 
    { 
        'serverName': 'NetBot Server v1',
        'arenaSize': 1000
        …
        …
        ...
        }
}
```

'conf' is a dict containing the server configuration values. Robots may find this useful in determining the size of the arena among other things. For example:

```
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

        #Obstacles (robots and shells are stopped by obstacles but obstacles are transparent to scan)
        'obstacles': [], #Obstacles of form {x:float,y:float,radius:float}
        'obstacleRadius': 5, #Radius of obstacles as % of arenaSize

        #Jam Zones (robots fully inside jam zone are not detected by scan)
        'jamZones': [], #Jam Zones of form {x:float,y:float,radius:float}

        #Misc
        'keepExplotionSteps': 10, #Number of steps to keep old explosions in explosion dict (only useful to viewers).
    }
```


**getInfo**

Gets information about the current game and robot health. If gameNumber == 0 then the server is still waiting for robots to join before is starts the first game.

Robot Sends: 

Format: `{ 'type': 'getInfoRequest' }`

Example: `{ 'type': 'getInfoRequest' }`


Server Returns: 

Format: `{ 'type': 'getInfoReply', 'gameNumber': int, 'gameStep': int, 'health': float (min 0, max 100), 'points': int }` or Error

Example: `{ 'type': 'getInfoReply', 'gameNumber': 5, 'gameStep': 170, 'health': 80.232, 'points': 44 }`


**getLocation**


Robot Sends: 

Format: `{ 'type': 'getLocationRequest' }`

Example: `{ 'type': 'getLocationRequest' }`


Server Returns: 

Format: `{ 'type': 'getLocationReply', 'x': float (min 0, max 999999), 'y': float (min 0, max 999999) }` or Error

Example: `{ 'type': 'getLocationReply', 'x': 40.343, 'y': 694.323 ) }`


**getSpeed**

Get information about the robots speed. If requestedSpeed != currentSpeed then the robot is accelerating or decelerating to the requestedSpeed. Note, if a robot hits a wall or another robot then currentSpeed and requestedSpeed will be set to 0.

Robot Sends: 

Format: `{ 'type': 'getSpeedRequest' }`

Example: `{ 'type': 'getSpeedRequest' }`


Server Returns: 

Format: `{ 'type': 'getSpeedReply', 'requestedSpeed': float (min 0, max 100) 'currentSpeed': float (min 0, max 100) }` or Error

Example: `{ 'type': 'getSpeedReply', 'requestedSpeed': float (min 0, max 100) 'currentSpeed': float (min 0, max 100) }`


**setSpeed**

Set desired speed of robot from 0% (stop) to 100%. See server configuration for how far a robot travels per step at 100% speed.


Robot Sends: 

Format: `{ 'type': 'setSpeedRequest', 'requestedSpeed': float (min 0, max 100) }`

Example: `{ 'type': 'setSpeedRequest', 'requestedSpeed': 100 }`


Server Returns: 

Format: `{ 'type': 'setSpeedReply' }` or Error

Example: `{ 'type': 'setSpeedReply' }`


**getDirection**

Gets the direction a robot will move if speed is greater than 0. If requestedDirection != currentDirection then the reboot is turning towards requestedDirection. The number of steps required to complete the turn is affected by the current speed. The faster the robot is moving the slower it can turn.

Robot Sends: 

Format: `{ 'type': 'getDirectionRequest' }`

Example: `{ 'type': 'getDirectionRequest' }`


Server Returns: 

Format: `{ 'type': 'getDirectionReply', 'requestedDirection': float (min 0, max 2pi) 'currentDirection': float (min 0, max 2pi) }` or Error

Example: `{ 'type': 'getDirectionReply', 'requestedDirection': 3.282 'currentDirection': 2.473 }`



**setDirection**


Robot Sends: 

Format: `{ 'type': 'setDirectionRequest', 'requestedDirection': float (min 0, max 2pi) }`

Example: `{ 'type': 'setDirectionRequest', 'requestedDirection': 4.823 }`


Server Returns: 

Format: `{ 'type': 'setDirectionReply' }` or Error

Example: `{ 'type': 'setDirectionReply' }`


**getCanon**

Used to determine if the robot has fired a shell that has not exploded yet.


Robot Sends: 

Format: `{ 'type': 'getCanonRequest' }`

Example: `{ 'type': 'getCanonRequest' }`


Server Returns: 

Format: `{ 'type': 'getCanonReply', 'shellInProgress': bool }` or Error

Example: `{ 'type': 'getCanonReply', 'shellInProgress': bool }`



**fireCanon**

Fires a shell in 'direction' angle from robots location and will trigger it to explode once it has traveled 'distance'. If a shell is already in progress (shellInProgress == True) then this will replace the previous shell and the previous shell will not explode.

Robot Sends: 

Format: `{ 'type': 'fireCanonRequest', 'direction': float (min 0, max 2pi) 'distance': float (min 10, max 1415) }`

Example: `{ 'type': 'fireCanonRequest', 'direction': 3.896 'distance': 340.345 }`


Server Returns: 

Format: `{ 'type': 'fireCanonReply' }` or Error

Example: `{ 'type': 'fireCanonReply' }`


**Scan**

Determines the distance to the closet enemy robot that is between startRadians and clockwise to endRadians angle from the robots location. If distance == 0 then the scan did not detect any enemy robots.


Robot Sends: 

Format: `{ 'type': 'scanRequest', 'startRadians': float (min 0, max 2pi,) 'endRadians': float (min 0, max 2pi) }`

Example: `{ 'type': 'scanRequest', 'startRadians': 0 'endRadians': 1.57 }`


Server Returns: 

Format: `{ 'type': 'scanReply', 'distance': float (min 0, max 1415) }` or Error

Example: `{ 'type': 'scanReply', 'distance': 70 }`


**Error**

Server Returns: 

Format:` { 'type': 'Error', 'result': str }`

Example: `{ 'type': 'Error', 'result':  'Can't process setSpeedRequest when health == 0'}`



---



# Proposed Learning Goals

1. Understand NetBots demo robots:
    * Run the demo and examine the code for the demo robots. What is the strengths and weaknesses of each demo robot.
    * Understand how robots communicate with the server.
    * Run the server with the '-h' option to learn how the server behavior can be changed.
    * Read the entire NetBots README to learn more.

2. Learn to program for a real-time environment with limited information. Make a robot that can beat all the demo robots. Some suggested improvements over the demo robots:
    * Have movement, scanning, and firing all happening at the same time.
    * Use binary search to quickly find the best enemy to fire at.
    * Take notice of if your robots health is going down or not. How should the robot behavior change based on this information?
    * Avoid colliding with other robots and walls.
    * If a game is close to ending (gameStep is close to stepMax) can your robot change behavior to win as quickly as possible.
    * Find other strategies that win faster with less health lost.

3. Understand what IP addresses and port numbers are. 
    * Why can only one program use a port number at a time? 
    * Why can a different computer use the same port number? 
    * Remove the need to specify robot port (-p) by having the robot find an available port.

4. Understand how computer resources and network reliability affect a real-time system.
    * Run a tournament with all processes on one computer and then run the same tournament with all processes on different computers. Watch the network and CPU use.
    * What's the difference in outcome? 
    * What if you speed up the server by using the -stepsec server option or change the -droprate server option? 
    * How do the stats differ? Why do they differ?

5. Learn how having access to more information can improve program logic.
    * Make one program that acts as two robots and have them work together and share information.

6. Learn to work with multiple sockets and custom message formats.
    * Make two programs, each acting as one robot, that work together by sending messages to each other.
    * Add message types to netbots_ipc for your own use.

7. Learn to communicate asynchronously with server.
    * Inspect and understand how BotSocket.sendrecvMessage() works.
    * Stop using synchronous BotSocket.sendrecvMessage() in your robot. Use asynchronous BotSocket.sendMessage() and BotSocket.recvMessage() instead. 
    * Send more than 1 message to the server per step. The server processes up to 4 messages from each robot per step (discards more than 4). This offers 4 times the information per step than sendrecvMessage() can provide.
