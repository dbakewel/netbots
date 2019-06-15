import time
import re
import copy

from netbots_log import log
import netbots_math as nbmath


def joinRequest(d, msg, src):
    if src in d.bots:
        if d.conf['allowRejoin']:
            d.bots[src]['name'] = msg['name']
            result = "OK"
        else:
            result = "Bot at " + src + " is already in game. Can't join twice."
            log("Bot at " + src + " tried to join twice.")
    elif src in d.viewers:
        result = "Viewers are not allowed to be bots."
        log("Viewer from " + src + " tried to join as bot.")
    elif len(d.bots) >= d.conf['botsInGame']:
        result = "Game is full. No more bots can join."
        log("Bot from " + src + " tried to join full game.")
    elif not d.conf['allowClasses'] and 'class' in msg and msg['class'] != "default":
        result = "Message contained class other than 'default' but server is set to only allow 'class' == 'default'"
        log("Bot from " + src + " requested class other than default when only default is allowed.")
    elif d.conf['allowClasses'] and 'class' in msg and msg['class'] not in d.conf['classes']:
        result = "Message contained class that is not known to server."
        log("Bot from " + src + " requested class that is not known to server.")
    else:
        d.bots[src] = copy.deepcopy(d.botTemplate)
        d.bots[src]['name'] = msg['name']
        if 'class' in msg:
            d.bots[src]['class'] = msg['class']
        d.startBots.append(src)
        result = "OK"
        log("Bot joined game: " + d.bots[src]['name'] + " (" + src + ")")

    log("Bots in Game: " + str(d.bots), "VERBOSE")

    if result == "OK":
        return {'type': "joinReply", 'conf': d.conf}
    else:
        return {'type': 'Error', 'result': result}


def getInfoRequest(d, msg, src):
    return {
        'type': "getInfoReply",
        'gameNumber': d.state['gameNumber'],
        'gameStep': d.state['gameStep'],
        'health': d.bots[src]['health'],
        'points': d.bots[src]['points']
    }


def getLocationRequest(d, msg, src):
    if d.bots[src]['health'] == 0:
        return {'type': 'Error', 'result': "Can't process getLocationRequest when health == 0"}
    else:
        return {
            'type': "getLocationReply",
            'x': d.bots[src]['x'],
            'y': d.bots[src]['y']
        }


def getSpeedRequest(d, msg, src):
    if d.bots[src]['health'] == 0:
        return {'type': 'Error', 'result': "Can't process getSpeedRequest when health == 0"}
    else:
        return {
            'type': "getSpeedReply",
            'requestedSpeed': d.bots[src]['requestedSpeed'],
            'currentSpeed': d.bots[src]['currentSpeed']
        }


def setSpeedRequest(d, msg, src):
    if d.bots[src]['health'] == 0:
        return {'type': 'Error', 'result': "Can't process setSpeedRequest when health == 0"}
    else:
        d.bots[src]['requestedSpeed'] = msg['requestedSpeed']
        return {
            'type': "setSpeedReply",
        }


def getDirectionRequest(d, msg, src):
    if d.bots[src]['health'] == 0:
        return {'type': 'Error', 'result': "Can't process getDirectionRequest when health == 0"}
    else:
        return {
            'type': "getDirectionReply",
            'requestedDirection': d.bots[src]['requestedDirection'],
            'currentDirection': d.bots[src]['currentDirection']
        }


def setDirectionRequest(d, msg, src):
    if d.bots[src]['health'] == 0:
        return {'type': 'Error', 'result': "Can't process setDirectionRequest when health == 0"}
    else:
        d.bots[src]['requestedDirection'] = msg['requestedDirection']
        return {
            'type': "setDirectionReply"
        }


def getCanonRequest(d, msg, src):
    if d.bots[src]['health'] == 0:
        return {'type': 'Error', 'result': "Can't process getCanonRequest when health == 0"}
    else:
        return {
            'type': "getCanonReply",
            'shellInProgress': src in d.shells
        }


def fireCanonRequest(d, msg, src):
    if d.bots[src]['health'] == 0:
        return {'type': 'Error', 'result': "Can't process fireCanonRequest when health == 0"}
    else:
        # Note, if shell in progress then this will replace it with new shell without causing any damage.
        # This overwriting is the expected behaviour.

        d.shells[src] = {
            'x': d.bots[src]['x'],
            'y': d.bots[src]['y'],
            'direction': msg['direction'],
            'distanceRemaining': msg['distance']
        }

        d.bots[src]['firedCount'] += 1

        d.bots[src]['last']['fireCanonRequest'] = {'direction': msg['direction'], 'distance': msg['distance']}

        return {
            'type': "fireCanonReply",
        }


def scanRequest(d, msg, src):
    if d.bots[src]['health'] == 0:
        return {'type': 'Error', 'result': "Can't process ScanRequest when health == 0"}
    else:
        distance = 0
        bot = d.bots[src]
        for src2, bot2 in d.bots.items():
            if src != src2 and bot2['health'] != 0:
                # don't detect bot2 if it's fully inside a jam Zone.
                jammed = False
                for jz in d.conf['jamZones']:
                    if nbmath.distance(bot2['x'], bot2['y'], jz['x'], jz['y']) + d.conf['botRadius'] < jz['radius']:
                        jammed = True

                if not jammed:
                    dis = nbmath.contains(bot['x'], bot['y'], msg['startRadians'],
                                          msg['endRadians'], bot2['x'], bot2['y'])
                    
                    if dis <= d.conf['scanMaxDistance'] and dis != 0:
                        if distance == 0:
                            distance = dis
                        elif dis < distance:
                            distance = dis
        
        d.bots[src]['last']['scanRequest'] = {'startRadians': msg['startRadians'], 'endRadians': msg['endRadians']}

        return {
            'type': "scanReply",
            'distance': distance
        }


def addViewerRequest(d, msg, src):
    if d.conf['noViewers']:
        return {'type': 'Error', 'result': "Viewers are not allowed to join."}
        log(src + " tried to join as viewer but viewers are not allowed to join.")
    elif src in d.bots:
        return {'type': 'Error', 'result': "Bots are not allowed to be viewers."}
        log("Bot from " + src + " tried to join as viewer.")
    elif src in d.viewers:
        d.viewers[src]['lastKeepAlive'] = time.time()
    else:
        ipPort = re.split('[-:]', src)  # create [str(ip),str(port)]
        d.viewers[src] = {
            'lastKeepAlive': time.time(),
            'ip': ipPort[0],
            'port': int(ipPort[1])
        }
        log("Viewer started watching game: " + src)

    return {
        'type': "addViewerReply",
        'conf': d.conf
    }


def viewKeepAlive(d, msg, src):
    if src in d.viewers:
        d.viewers[src]['lastKeepAlive'] = time.time()
    return None
