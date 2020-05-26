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

#include the netbot src directory in sys.path so we can import modules from it.
filepath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(os.path.dirname(filepath),"src") 
sys.path.insert(0,srcpath)

from netbots_log import log
from netbots_log import setLogLevel
from netbots_log import setLogFile

maxRound = 4  # first round is 0 so "maxRound = 7" would run 8 rounds.

pythoncmd = ['python3']
srvoptions = [
    os.path.join('src','netbots_server.py'),
    '-p','20000',
    '-bots', '4', 
    '-games', '1000',
    '-stepsec', '0.001',
    '-stepmax','5000',
    '-startperms',
    '-noviewers',
    '-onlylastsb',
    '-jsonsb'
    ]


fd = []
def closeFiles():
    global fd
    for f in fd:
        f.flush()
        f.close()
    fd = []


def startserver(divisionDir):
    global fd
    f = open(os.path.join(divisionDir,"server.output.txt"), "w")
    fd.append(f)
    cmdline = pythoncmd + srvoptions + [os.path.join(divisionDir,"results.json")]
    log(cmdline, "DEBUG")
    p = subprocess.Popen(cmdline, stdout=f, stderr=sys.stdout.buffer)
    return p


def startbot(divisionDir, botkey):
    global fd, robotsDir, bots
    bot = bots[botkey]
    f = open(os.path.join(divisionDir, bot['file'] + ".output.txt"), "w")
    fd.append(f)
    cmdline = pythoncmd + [os.path.join(robotsDir, bot['file']), '-p', str(bot['port']),'-sp','20000']
    log(cmdline, "DEBUG")
    p = subprocess.Popen(cmdline, stdout=f, stderr=sys.stdout.buffer)
    return p


def botsToString(divisions):
    global bots
    output = "\n\nCurrent Rankings\n"
    div = 0
    for keys in divisions:
        output += "\nDivision " + str(div) + "\n"
        for k in keys:
            output += str(bots[k]['port']) + " " + bots[k]['file'] + "\n"
        div += 1
    return(output)


def rundivision(divisionDir, divisionBots):
    global bots

    log("Running Division: " + divisionDir)
    os.mkdir(divisionDir)

    srvProc = startserver(divisionDir)

    botProcs = []
    for botkey in divisionBots:
        botProcs.append(startbot(divisionDir, botkey))

    time.sleep(2)

    #ensure all botProcs still running (make sure we did not have a startup problem.)
    botDead = False
    for bot in botProcs:
        if bot.poll() != None:
            botDead = True

    if botDead == False:
        #wait for server to quit
        srvProc.wait()
    else:
        log("BOT DIED EARLY!!!", "ERROR")
        if srvProc.poll() == None:
            os.kill(srvProc.pid, signal.SIGINT)
        time.sleep(1)
        if srvProc.poll() == None:
            log("Needed to terminate server.", "WARNING")
            srvProc.terminate()

    #try to kill bots nicely
    for bot in botProcs:
        if bot.poll() == None:
            os.kill(bot.pid, signal.SIGINT)

    time.sleep(2)

    #kill all robots
    for bot in botProcs:
        if bot.poll() == None:
            log("Needed to terminate bot.", "WARNIGN")
            bot.terminate()

    time.sleep(2)

    closeFiles()

    # if results.json has been created then load results else log error.
    jsonFile = os.path.join(divisionDir,"results.json")
    if os.path.isfile(jsonFile):
        with open(jsonFile) as json_file:
            results = json.load(json_file)
        botSort = sorted(results['bots'], key=lambda b: results['bots'][b]['points'], reverse=True)
        divisionBots[0] = botSort[0]
        divisionBots[1] = botSort[1]
        divisionBots[2] = botSort[2]
        divisionBots[3] = botSort[3]

    else:
        log("Server did not produce json file: " + jsonFile, "FAILURE")
        quit()


def quit(signal=None, frame=None):
    log("Quiting","INFO")
    exit()


def main():
    global outputDir, robotsDir, bots

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-robots', metavar='dir', dest='robotsDir', type=str,
                        required=True, help='Directory containing only robots to use in tournaments. Must be exactly one level under netbots base dir and given relative to netbots base dir (eg. myrobots).')
    parser.add_argument('-output', metavar='dir', dest='outputDir', type=str,
                        required=True, help='Full directory path to send output. Directory should exist and be empty. (eg. /tmp/tournament.2020-50-02-11:37:23)')
    parser.add_argument('-debug', dest='debug', action='store_true', default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true', default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    
    args = parser.parse_args()
    outputDir = args.outputDir
    robotsDir = args.robotsDir
    setLogLevel(args.debug, args.verbose)
    setLogFile(os.path.join(outputDir,"output.txt"))
    resultsfilename = os.path.join(outputDir,"results.txt")

    # pick random ports for robots. These port numbers will be assigned to a robot for the entire tournament.
    ports = random.sample(range(20100,20199),16)

    # Read robot filenames and assign port.
    bots = {}
    for file in os.listdir(robotsDir):
        if os.path.isfile(os.path.join(robotsDir, file)) and not file.startswith('.'):
            try:
                port = ports.pop()
            except:
                log("Only 16 robots can be in robots dir.","ERROR")
                quit()
            log("Adding bot " + file + " at port " + str(port))
            bots['127.0.0.1:' + str(port)] = {'port': port, 'file': file}
    if len(ports) != 0:
        log("Less than 16 robots found in robots dir.","ERROR")
        quit()

    if os.path.isdir(outputDir):
        log("Using existing output directory: " + outputDir)
    else:
        os.mkdir(outputDir)
        log("Created output directory: " + outputDir)

    # Put robots into initial 4 divisions, 4 robots in each. divisions contains only keys to the bots dict. 
    divisions = [[],[],[],[]]
    next = 0
    for k in bots.keys():
        divisions[next % 4].append(k)
        next += 1
    log(botsToString(divisions), "VERBOSE")

    round = -1
    while round < maxRound:
        round += 1

        roundDir = os.path.join(outputDir,"round-" + str(round))
        os.mkdir(roundDir)

        # Run each division and put robots in division in order of points.
        for divisionNumber in range(4):
            divisionDir = os.path.join(roundDir, "division-" + str(divisionNumber))
            rundivision(divisionDir, divisions[divisionNumber])

        log(botsToString(divisions), "VERBOSE")

        # Output Results
        output = "\n" + \
                 "                                           RESULTS AFTER " + str(round+1) + " ROUNDS" + \
                 "\n\n" + \
                 "                    ---- Score -----  ------ Wins -------  --------- CanonFired ----------\n" + \
                 "              Name      Points     %    Count   AvgHealth    Count   AvgDamage   TotDamage    Missteps  IP:Port\n" + \
                 " ----------------------------------------------------------------------------------------------------------------------------\n"

        for divisionNumber in range(4):
            output += "DIVISION " + str(divisionNumber)
            roundoutput = os.path.join(roundDir, "division-" + str(divisionNumber), "server.output.txt")
            p = subprocess.Popen(["grep", "-m1", "-A", "4", "\------------------", roundoutput], stdout=subprocess.PIPE, stderr=sys.stdout.buffer)
            tmp = p.stdout.read().decode("utf-8")
            output += re.sub(r'---*','',tmp)
            output += "\n"

        with open(resultsfilename,"a+") as f: 
            f.write(output)
        log("Results written to " + resultsfilename)

        # Run Cross Divisions if this is not the last round. This is how bots can move between divisions.
        if round < maxRound:
            # top 2 robots in first division and last 2 robots in last division do not move
            # Put remaining bots into cross divisions to see if they move between divisions
            crossDivisions = [[
                    divisions[0][2],
                    divisions[0][3],
                    divisions[1][0],
                    divisions[1][1]],[
                    divisions[1][2],
                    divisions[1][3],
                    divisions[2][0],
                    divisions[2][1]],[
                    divisions[2][2],
                    divisions[2][3],
                    divisions[3][0],
                    divisions[3][1]]]

            for divisionNumber in range(3):
                divisionDir = os.path.join(roundDir, "crossdivision-" + str(divisionNumber))
                rundivision(divisionDir, crossDivisions[divisionNumber])

            for b in range(3):
                # Put top 2 robots from second chance divisions into upper divisions
                divisions[b][2] = crossDivisions[b][0]
                divisions[b][3] = crossDivisions[b][1]
                # Put bottom 2 robots from second chance divisions into lower divisions
                divisions[b+1][0] = crossDivisions[b][2]
                divisions[b+1][1] = crossDivisions[b][3]

            log(botsToString(divisions), "VERBOSE")

    quit()

if __name__ == "__main__":
    if platform.system() == 'Windows':
        log("Cannot run on Windows because SIGINT not supported.", "ERROR")
        exit()

    # execute only if run as a script
    signal.signal(signal.SIGINT, quit)
    main()
