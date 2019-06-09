# Proposed Learning Goals

1. Understand NetBots demo robots:
    * Download and run the demo and examine the code for the demo robots. 
    * What is the strengths and weaknesses of each demo robot?
    * Understand how robots communicate with the server.
    * Run the server with the '-h' option to learn how the server behavior can be changed.
    * What useful information is in the server conf?
    * Understand netbots_log module's use of logging level. Try -debug and -verbose.
    * Run netbots on over several computers.
    * Read the entire NetBots README to learn more.

2. Learn to program for a real-time environment with limited information.
    * Make a robot that can beat all the demo robots.
    * How can each demo robot's basic strategy be be improved? e.g. faster locating of enemies, avoiding hit damage.
    * Can the strategies of multiple demo robots be combined into a single robot? Does this result is a better outcome?
    * What information is available that none of the demo robots use? How an that information be used effectively?
    * Look for other strategies that win faster with less health lost.

3. Understand how computer and network resources affect the game.
    * Run a tournament with all processes on one computer and then run the same tournament with all processes on different computers. Watch the network and CPU use.
    * What's the difference in resource use and game outcome?
    * How do the server and robot stat differ? Why do they differ?
    * What if you speed up the server by using the -stepsec server option or change the -droprate server option?
    * Understand IP and port number: Why can only one program use a port number at a time? Why can a different computer use the same port number?
    * Remove the need to specify robot port (-p) by having the robot find an available port. Can you remove the need to specify IP?

4. Learn how having access to more or less information can improve program logic.
    * Do some robots perform better if message drop rate is turned off (dropRate = 0). Do some perform worse? Why?
    * Make one program that acts as two robots and have them share information. Can this combined robot perform better?

5. Learn to work with multiple sockets and custom message formats.
    * Make two programs, each acting as one robot, that work together by sending messages to each other. 
    * Use of the netbots_ipc asynchronous methods for communication between robots.
    * Add message types to netbots_ipc for your own use.

6. Learn to communicate asynchronously with server.
    * Inspect and understand how BotSocket.sendrecvMessage() works.
    * Stop using synchronous BotSocket.sendrecvMessage() in your robot. Use asynchronous BotSocket.sendMessage() and BotSocket.recvMessage() instead. 
    * Send more than 1 message to the server per step. The server processes up to 4 messages from each robot per step (discards more than 4). This offers 4 times the information per step than sendrecvMessage() can provide.

7. Miscellaneous:
    * Learn GIT and how to contribute to an open source project on GitHub. Add some functionality to NetBots or fix a bug.
    * Learn TK GUI. Make improvements to the NetBots viewer.
