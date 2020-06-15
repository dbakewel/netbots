import sys
import subprocess
import time
import os
import random
import signal
import argparse
import platform
import json
import re
import threading

#include the netbot src directory in sys.path so we can import modules from it.
filepath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(os.path.dirname(filepath),"src") 
sys.path.insert(0,srcpath)

from netbots_log import log
from netbots_log import setLogLevel
from netbots_log import setLogFile

serverMax = 2  # Max number of netbots servers to run at once.
botsMax = 64
botsInDivision = 4  # This cannot be changed without significant changes to the code below.

def rundivision(bots, divisionDir, robotsDir, botkeys, serverPort):
    pythoncmd = ['python3']
    srvoptions = [
        os.path.join('src','netbots_server.py'),
        '-p',serverPort,
        '-bots', str(botsInDivision), 
        '-games', '1000',
        '-stepsec', '0.001',
        '-stepmax','5000',
        '-maxsecstojoin', '10',
        '-startperms',
        '-noviewers',
        '-onlylastsb',
        '-jsonsb'
        ]

    fd = []

    log("Running Division: " + divisionDir)
    os.mkdir(divisionDir)

    f = open(os.path.join(divisionDir,"server.output.txt"), "w")
    fd.append(f)
    cmdline = pythoncmd + srvoptions + [os.path.join(divisionDir,"results.json")]
    log(cmdline, "VERBOSE")
    srvProc = subprocess.Popen(cmdline, stdout=f, stderr=subprocess.STDOUT)

    botProcs = []
    for botkey in botkeys:
        bot = bots[botkey]
        f = open(os.path.join(divisionDir, bot['file'] + ".output.txt"), "w")
        fd.append(f)
        cmdline = pythoncmd + [os.path.join(robotsDir, bot['file']), '-p', str(bot['port']),'-sp','20000']
        log(cmdline, "VERBOSE")
        p = subprocess.Popen(cmdline, stdout=f, stderr=subprocess.STDOUT)
        botProcs.append(p)

    time.sleep(2)

    #ensure all botProcs still running (make sure we did not have a startup problem.)
    botDead = False
    for bot in botProcs:
        if bot.poll() != None:
            log("A bot crashed shortly after being run. {}".format(bot.args), "ERROR")

    # wait for server to quit, either because all games are done or not enough robots joined to start playing
    srvProc.wait()

    #try to kill bots nicely, some bots will already have quit because they detected that server quit.
    for bot in botProcs:
        if bot.poll() == None:
            os.kill(bot.pid, signal.SIGINT)

    time.sleep(2)

    #kill all robots
    for bot in botProcs:
        if bot.poll() == None:
            log("Needed to terminate bot.", "WARNING")
            bot.terminate()

    time.sleep(2)

    for f in fd:
        f.flush()
        f.close()
    fd = []

    # if results.json has been created then load results else log error.
    jsonFile = os.path.join(divisionDir,"results.json")
    if os.path.isfile(jsonFile):
        with open(jsonFile) as json_file:
            results = json.load(json_file)

        #find any bots that did not join the game
        missing = []
        for botkey in botkeys:
            if botkey not in results['bots']:
                log("Bot missing from results probably because it did not join game: " + botkey, "WARNING")
                missing.append(botkey)

        if len(results['bots']) + len(missing) != len(botkeys):
            log("Results and Missing bots do not equal bots in game.", "FAILURE")
            quit()

        #Add robots to resutls in order of points, missing at end.
        botSort = sorted(results['bots'], key=lambda b: results['bots'][b]['points'], reverse=True)
        for i in range(len(botSort)):
            botkeys[i] = botSort[i]
        for i in range(i+1, len(botkeys)): # loop will not run if i+1 == len(botkeys)
            botkeys[i] = missing.pop()
    else:
        log("Server did not produce json file: " + jsonFile + ". Can't update results!", "ERROR")


def quit(signal=None, frame=None):
    log("Quiting","INFO")
    exit()


def main():
    global bots, botsMax, botsInDivision, serverMax

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-robots', metavar='dir', dest='robotsDir', type=str,
                        required=True, help='Directory containing only robots to use in tournaments. Must be exactly one level under netbots base dir and given relative to netbots base dir (eg. myrobots).')
    parser.add_argument('-output', metavar='dir', dest='outputDir', type=str,
                        required=True, help='Full directory path to send output. Directory should exist and be empty. (eg. /tmp/tournament.2020-50-02-11:37:23)')
    parser.add_argument('-copy', dest='copy', action='store_true', default=False, help='Copy robots dir to output dir.')
    parser.add_argument('-md5sum', dest='md5sum', action='store_true', default=False, help='Print MD5sum for each robot.')
    parser.add_argument('-debug', dest='debug', action='store_true', default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true', default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    
    args = parser.parse_args()
    outputDir = args.outputDir
    robotsDir = args.robotsDir
    setLogLevel(args.debug, args.verbose)

    if os.path.isdir(outputDir):
        log("Using existing output directory: " + outputDir)
    else:
        os.mkdir(outputDir)
        log("Created output directory: " + outputDir)
    
    setLogFile(os.path.join(outputDir,"output.txt"))
    resultsfilename = os.path.join(outputDir,"results.txt")

    # pick random ports for robots. These port numbers will be assigned to a robot for the entire tournament.
    ports = random.sample(range(20100,20199), botsMax)

    # Read robot filenames and assign port.
    bots = {}
    for file in os.listdir(robotsDir):
        if os.path.isfile(os.path.join(robotsDir, file)) and not file.startswith('.'):
            try:
                port = ports.pop()
            except:
                log("Only " + botsMax + " robots can be in robots dir.","FAILURE")
                quit()
            log("Adding bot " + file + " at port " + str(port))
            bots['127.0.0.1:' + str(port)] = {'port': port, 'file': file}
        if args.md5sum:
            p = subprocess.Popen(["md5sum",os.path.join(robotsDir, file)], stdout=subprocess.PIPE, stderr=sys.stdout.buffer)
            log("md5sum " + p.stdout.read().decode("utf-8").rstrip())

    if len(bots) % botsInDivision != 0:
        log("Number of bots does not divide evenly into divisions, len(bots) % botsInDivision must equal 0: " + \
           f" {len(bots)} % {botsInDivision} == {len(bots) % botsInDivision}","FAILURE")
        quit()

    if args.copy:
        p = subprocess.Popen(["cp", "-r", robotsDir, os.path.join(outputDir, "robots")], stdout=subprocess.PIPE, stderr=sys.stdout.buffer)
        log("Robots copied to " + os.path.join(outputDir, "robots") + p.stdout.read().decode("utf-8").rstrip())

    divisionsTotal = int(len(bots) / botsInDivision)
    log(f"Creating {divisionsTotal} divisions with {botsInDivision} bots in each.")

    # Put robots randomly into divisionsTotal divisions, botsInDivision robots in each.
    # divisions contains only keys to the bots dict. 
    divisions = []
    for i in range(divisionsTotal):
        divisions.append([])

    next = 0
    for k in bots.keys():
        divisions[next % divisionsTotal].append(k)
        next += 1

    maxRound = divisionsTotal*2-1  # first round is 0 so "maxRound = 7" would run 8 rounds.
    log(f"Max rounds set to {maxRound+1}.")

    round = -1
    lastRoundResult = ""
    while round < maxRound and lastRoundResult != str(divisions):
        round += 1
        lastRoundResult = str(divisions)

        roundDir = os.path.join(outputDir,"round-" + str(round))
        os.mkdir(roundDir)
        
        # Run Cross Divisions if there is more than one division
        # and this is not the first round (0).
        # This is how robots move between divisions.
        if divisionsTotal > 1 and round != 0:
            # top 2 robots in first division and last 2 robots in last division do not move
            # Put remaining bots into cross divisions to see if they move between divisions
            # !!! ASSUMES botsInDivition == 4
            crossDivisions = []
            for divisionNumber in range(divisionsTotal-1):
                crossDivisions.append([
                    divisions[divisionNumber][2],
                    divisions[divisionNumber][3],
                    divisions[divisionNumber+1][0],
                    divisions[divisionNumber+1][1]
                   ])

            serverPort = 20000
            for divisionNumber in range(divisionsTotal-1):
                # if serverMax server threads are already running then wait for one to finish
                while threading.active_count() - 1 == serverMax:
                    sleep(1)
                # Start running a new division
                divisionDir = os.path.join(roundDir, "crossdivision-" + str(divisionNumber) + "x" + str(divisionNumber+1))
                t = threading.Thread(target=rundivision, 
                    args=(bots, divisionDir, robotsDir, crossDivisions[divisionNumber], serverPort), 
                    daemon=True)
                t.start()
                serverPort += 1
            # Wait for all threads to finish.
            while threading.active_count() > 1:
                sleep(1)

            for b in range(divisionsTotal-1):
                # !!! ASSUMES botsInDivition == 4
                # Put top 2 robots from second chance divisions into upper divisions
                divisions[b][2] = crossDivisions[b][0]
                divisions[b][3] = crossDivisions[b][1]
                # Put bottom 2 robots from second chance divisions into lower divisions
                divisions[b+1][0] = crossDivisions[b][2]
                divisions[b+1][1] = crossDivisions[b][3]

        # Run each division and put robots in division in order of points.
        serverPort = 20000
        for divisionNumber in range(divisionsTotal):
            # if serverMax server threads are already running then wait for one to finish
            while threading.active_count() - 1 == serverMax:
                sleep(1)
            # Start running a new division
            divisionDir = os.path.join(roundDir, "division-" + str(divisionNumber))
            t = threading.Thread(target=rundivision, 
                args=(bots, divisionDir, robotsDir, divisions[divisionNumber], serverPort), 
                daemon=True)
            t.start()
            serverPort += 1
        # Wait for all threads to finish.
        while threading.active_count() > 1:
            sleep(1)

        # Output Results
        output = "\n" + \
                 "                                           RESULTS AFTER " + str(round+1) + " ROUNDS" + \
                 "\n\n" + \
                 "                    ---- Score -----  ------ Wins -------  --------- CanonFired ----------\n" + \
                 "              Name      Points     %    Count   AvgHealth    Count   AvgDamage   TotDamage   MS%  IP:Port\n" + \
                 " ------------------------------------------------------------------------------------------------------------------\n"

        for divisionNumber in range(divisionsTotal):
            output += "DIVISION " + str(divisionNumber)
            roundoutput = os.path.join(roundDir, "division-" + str(divisionNumber), "server.output.txt")
            p = subprocess.Popen(["grep", "-m1", "-A", str(botsInDivision), "\------------------", roundoutput], stdout=subprocess.PIPE, stderr=sys.stdout.buffer)
            tmp = p.stdout.read().decode("utf-8")
            output += re.sub(r'---*','',tmp)
            output += "\n"

        with open(resultsfilename,"a+") as f: 
            f.write(output)
        log("Results written to " + resultsfilename)

    if round == maxRound:
        log(f"Quiting because max rounds ({maxRound + 1}) completed.")

    if lastRoundResult == str(divisions):
        log("Quiting because no change in results of last two rounds.")

    quit()

if __name__ == "__main__":
    if platform.system() == 'Windows':
        log("Cannot run on Windows because SIGINT not supported.", "ERROR")
        exit()

    # execute only if run as a script
    signal.signal(signal.SIGINT, quit)
    main()
