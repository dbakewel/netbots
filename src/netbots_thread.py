
import sys
import threading
import importlib

from netbots_viewer import main as viewerMain     

from netbots_log import log

def botThread(script, argv):
    log("Importing " + script, "INFO")
    bot = importlib.import_module(script)
    log("Calling main() from " + script + " with argv = " + str(argv), "INFO")
    bot.main(argv)

def startBotThreads(botDir, startBots, serverPort):
    if not startBots:
        return

    log("Adding bot dir (" + botDir + ") to path.", "INFO")
    sys.path.insert(0, botDir)

    threads = list()
    port = 20021
    for script in startBots:
        log("Creating thread for " + script, "INFO")
        t = threading.Thread(target=botThread, name=script + "-" + str(port), 
            args=(script, ['"script"', "-p", str(port), "-sp", str(serverPort)],), daemon=True)
        threads.append(t)
        t.start()
        port += 1
    return threads

def startViewerThread(serverPort):
    port = 20020
    log("Creating thread for viewer.", "INFO")
    t = threading.Thread(target=viewerMain, name="viewer" + "-" + str(port), 
        args=(['"viewer"', "-p", str(port), "-sp", str(serverPort)],), daemon=True)
    t.start()
    return t