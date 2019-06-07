import socket
import umsgpack
import random
import time
import re
import math
import argparse

from netbots_log import log

"""
**About Messages**

Every message is a python dict type with at least a type attribute (i.e. field) and a 
string value.

For example: { 'type': 'getInfoRequest'}

MsgDef below defines valid types and additional fields that must be included and 
can optionally be included based on type.

Optional fields end in '_o' which marks the fields as optional. The '_o' should not 
appear in the actual message, it is just a marker that the field is optional.
For example, a joinRequest message with optional class field would be:

{'type': 'joinRequest', 'name': 'SuperRobot', 'class': 'heavy'}

All fields have a defined type in the form of <type> or [<type>,min,max].
<type> can be expressed as multiple acceptable types as (<type>,<type>,...)

For fields types of 'str' min and max are the min length and max length of the string.

All Request messages have a corresponding Reply message. The Request is sent to the
server and the server returns the reply message or an Error message.
"""
MsgDef = {
    # msg type              other required msg fields
    'joinRequest': {'name': ['str', 1, 16], 'class_o': ['str', 1, 16]},
    'joinReply': {'conf': 'dict'},

    'getInfoRequest': {},
    'getInfoReply': {'gameNumber': 'int', 'gameStep': 'int', 'health': ['(int,float)', 0, 100], 'points': 'int'},

    'getLocationRequest': {},
    'getLocationReply': {'x': ['(int,float)', 0, 32767], 'y': ['(int,float)', 0, 32767]},

    'getSpeedRequest': {},
    'getSpeedReply': {'requestedSpeed': ['(int,float)', 0, 100], 'currentSpeed': ['(int,float)', 0, 100]},

    'setSpeedRequest': {'requestedSpeed': ['(int,float)', 0, 100]},
    'setSpeedReply': {},

    'getDirectionRequest': {},
    'getDirectionReply': {'requestedDirection': ['(int,float)', 0, math.pi * 2], 'currentDirection': ['(int,float)', 0, math.pi * 2]},

    'setDirectionRequest': {'requestedDirection': ['(int,float)', 0, math.pi * 2]},
    'setDirectionReply': {},

    'getCanonRequest': {},
    'getCanonReply': {'shellInProgress': 'bool'},

    'fireCanonRequest': {'direction': ['(int,float)', 0, math.pi * 2], 'distance': ['(int,float)', 10, 32767]},
    'fireCanonReply': {},

    'scanRequest': {'startRadians': ['(int,float)', 0, math.pi * 2], 'endRadians': ['(int,float)', 0, math.pi * 2]},
    'scanReply': {'distance': ['(int,float)', 0, 32767]},

    'addViewerRequest': {},
    'addViewerReply': {'conf': 'dict'},

    # The msg types below do not have, nor expect, a matching reply
    'viewData': {'state': 'dict', 'bots': 'dict', 'shells': 'dict', 'explosions': 'dict'},
    'viewKeepAlive': {},
    'Error': {'result': 'str'}
}


def isValidMsg(msg):
    """ Returns True if msg is a valid message, otherwise returns false. """

    global MsgDef

    if not isinstance(msg, dict):
        log("Msg is type " + str(type(msg)) + " but must be dict type: " + str(msg), "ERROR")
        return False
    if not 'type' in msg:
        log("Msg does not contain 'type' key: " + str(msg), "ERROR")
        return False

    unvalidedFields = list(msg.keys())
    # type is validated below as part of loop so does not need specific validation.
    unvalidedFields.remove('type')
    # msgId and replyData are always optional and have no specific format. So they are always valid if present.
    if 'msgID' in unvalidedFields:
        unvalidedFields.remove('msgID')
    if 'replyData' in unvalidedFields:
        unvalidedFields.remove('replyData')

    for msgtype, msgspec in MsgDef.items():
        if msgtype == msg['type']:
            for fld, fldspec in msgspec.items():
                if fld.endswith('_o'):
                    # remove magic suffix marking field as optional
                    fld = fld.rstrip('_o')
                    if fld not in msg:
                        # optional field is not present, which is valid.
                        continue
                elif fld not in msg:
                    log("Msg does not contain required '" + fld + "' key: " + str(msg), "ERROR")
                    return False
                if isinstance(fldspec, list):
                    if not isinstance(msg[fld], eval(fldspec[0])):
                        log("Msg '" + fld + "' key has value of type " + str(type(msg[fld])) +
                            " but expected " + fldspec[0] + ": " + str(msg), "ERROR")
                        return False
                    if fldspec[0] is 'str':
                        if len(msg[fld]) < fldspec[1] or len(msg[fld]) > fldspec[2]:
                            log("Msg '" + fld + "' key has a string value " + str(msg[fld]) +
                                " with length out of range [" + str(fldspec[1]) + "," +
                                str(fldspec[2]) + "] : " + str(msg), "ERROR")
                            return False
                    elif msg[fld] < fldspec[1] or msg[fld] > fldspec[2]:
                        log("Msg '" + fld + "' key has a value " + str(msg[fld]) +
                            " which is out of range [" + str(fldspec[1]) + "," +
                            str(fldspec[2]) + "] : " + str(msg), "ERROR")
                        return False
                else:
                    if not isinstance(msg[fld], eval(fldspec)):
                        log("Msg '" + fld + "' key has value of type " + str(type(msg[fld])) +
                            " but expected " + fldspec + ": " + str(msg), "ERROR")
                        return False
                unvalidedFields.remove(fld)
            # All fields defined for message type have now been examined and are valid
            if len(unvalidedFields):
                # message has fields it should not have.
                log("Msg contains field(s) " + str(unvalidedFields) + " which is not defined for message type " + msg['type'] + ": " + str(msg), "ERROR")
                for fld in unvalidedFields:
                    if fld.endswith('_o'):
                        log("Optional message fields should not include '_o' suffix in field name.", "WARNING")
                        break
                return False
            else:
                # message is valid and has no extra fields.
                return True
    log("Msg 'type' key has value '" + str(msg['type']) + "' which is not known: " + str(msg), "ERROR")
    return False


def isValidIP(ip):
    """ Returns True if ip is valid IP address, otherwise returns false. """
    if not isinstance(ip, str):
        log("IP is type " + str(type(ip)) + " but must be type str.", "ERROR")
        return False
    if not re.match(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$', ip):
        log("IP address has bad format, expected something like 'int.int.int.int' but got " + ip, "ERROR")
        return False
    return True

# Check IP address format as needed by argparse module.


def argParseCheckIPFormat(ip):
    """ Returns ip if ip is a valid IP address, otherwise raises argparse.ArgumentTypeError exception. """

    if not isValidIP(ip):
        raise argparse.ArgumentTypeError(ip)
    return ip


def isValidPort(p):
    """ Returns True if p is valid port number, otherwise returns false. """

    if not isinstance(p, int):
        log("Port is type " + str(type(p)) + " but must be type int.", "ERROR")
        return False
    if p < 1 or p > 65000:
        log("Port is out of valid range 0-65000: " + str(p), "ERROR")
        return False
    return True


def formatIpPort(ip, port):
    """ Formats ip and port into a single string. eg. 127.168.32.11:20012 """
    return str(ip) + ":" + str(port)


class NetBotSocketException(Exception):
    """Raised by the NetBotSocket class."""
    pass


class NetBotSocket:
    """NetBot Msg filtering and basic reliable send/recv for UDP soket. """

    def __init__(self, sourceIP, sourcePort, destinationIP='127.0.0.1', destinationPort=20000):
        """
        Create and bind UDP socket and bind it to listen on sourceIP and sourcePort.

        sourceIP: IP the socket will listen on. This must be 127.0.0.1 (locahost), 0.0.0.0 (all interfaces), or a valid IP address on the computer.
        sourcePort: port to listen on. This is an integer number.
        destinationIP and destinationPort are stored with setDestinationAddress()


        Returns NetBotSocket object.

        Raises socket related exceptions.
        """

        self.sent = 0  # Number of messages sent to OS socket
        self.recv = 0  # Number of messages recv from OS socket
        self.sendRecvMessageCalls = 0  # Number of calls to sendRecvMessage
        self.sendRecvMessageResends = 0  # Number of resends made by sendRecvMessage
        self.sendRecvMessageTime = 0  # Total time in sendRecvMessage
        self.sendTypes = {}
        self.recvTypes = {}

        self.sendrecvDelay = 0.1

        self.sourceIP = sourceIP
        self.sourcePort = sourcePort
        log("Creating socket with sourceIP=" + sourceIP + ", sourcePort=" + str(sourcePort), "VERBOSE")
        self.s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        try:
            self.s.bind((sourceIP, sourcePort))
            log("Source Socket Binding Successful. Listening on " + formatIpPort(sourceIP, sourcePort))
        except Exception as e:
            self.s.close()
            self.s = None
            log("Source Socket Binding Failed. The source port may already be in use. Try another port.", "FAILURE")
            raise
        self.s.settimeout(0)
        self.destinationIP = destinationIP
        self.destinationPort = destinationPort
        self.bufferSize = 4096
        random.seed()
        self.msgID = random.randrange(0, 65000, 1)

    def settimeout(self, t):
        self.s.settimeout(t)

    def setDelay(self, delay):
        self.sendrecvDelay = delay

    def getStats(self):
        """ Return str of NetBotSocket stats. """
        output = "\n\n                 ====== Stats ======" +\
            "\n\n               Messages Sent: " + str(self.sent) +\
            "\n              Messages Recv: " + str(self.recv)

        if self.sendRecvMessageCalls:
            output += \
                "\n     sendRecvMessage Calls: " + str(self.sendRecvMessageCalls) + \
                "\n   sendRecvMessage Resends: " + str(self.sendRecvMessageResends) + \
                "\n  Avg sendRecvMessage Time: " + \
                '%.6f' % (self.sendRecvMessageTime / self.sendRecvMessageCalls) + " secs."

        output += "\n\n                Messages Sent by Type"
        for t, c in sorted(self.sendTypes.items(), key=lambda x: x[0]):
            output += "\n" + '%26s' % (t) + ": " + str(c)

        output += "\n\n                Messages Recv by Type"
        for t, c in sorted(self.recvTypes.items(), key=lambda x: x[0]):
            output += "\n" + '%26s' % (t) + ": " + str(c)

        output += "\n\n"

        return output

    def setDestinationAddress(self, destinationIP, destinationPort):
        """
        Set default destination used by NetBotSocket send and recv functions when
        destination is not provided.

        Returns no value

        Raises NetBotSocketException exception.
        """

        if not isValidIP(destinationIP) or not isValidPort(destinationPort):
            raise NetBotSocketException("Bad IP or Port Provided.")

        self.destinationIP = destinationIP
        self.destinationPort = destinationPort

    def serialize(self, msg):
        return umsgpack.packb(msg)

    def deserialize(self, b):
        return umsgpack.unpackb(b)

    def sendMessage(self, msg, destinationIP=None, destinationPort=None, packedAndChecked=False):
        """
        Sends msg to destinationIP:destinationPort and then returns immediately.
        sendMessage is considered asynchronous because it does not wait for a
        reply message and returns no value. Therefore there is no indication if
        msg will be received by the destination.

        msg must be a valid message (see Messages below). Raises
        NetBotSocketException exception if the msg does not have a valid format.

        If destinationIP or destinationPort is not provided then the default will
        be used (see setDestinationAddress()).

        If packedAndChecked is True then msg is assumed to already be serialized
        and no other checks will be done.

        """

        if destinationIP is None:
            destinationIP = self.destinationIP

        if destinationPort is None:
            destinationPort = self.destinationPort

        if not packedAndChecked:
            if not isValidMsg(msg):
                raise NetBotSocketException("Could not send because msg is not valid format.")
            if not isValidIP(destinationIP):
                raise NetBotSocketException("Could not send because destinationIP is not valid format.")
            if not isValidPort(destinationPort):
                raise NetBotSocketException("Could not send because destinationPort is not valid format.")

            # Convert data from python objects to network binary format
            networkbytes = self.serialize(msg)
        else:
            networkbytes = msg

        log("Sending msg to " + destinationIP + ":" + str(destinationPort) +
            " len=" + str(len(networkbytes)) + " bytes " + str(msg), "DEBUG")
        self.s.sendto(networkbytes, (destinationIP, destinationPort))
        self.sent = self.sent + 1

        if not packedAndChecked:
            msgtype = msg['type']
        else:
            msgtype = "Serialized"

        if msgtype in self.sendTypes:
            self.sendTypes[msgtype] += 1
        else:
            self.sendTypes[msgtype] = 1

    def recvMessage(self):
        """
        Check the socket receive buffer and returns message, ip, and port only
        if a valid message is immediately ready to receive. recvMessage is
        considered asynchronous because it will not wait for a message to arrive
        before raising an exception.

        Returns msg, ip, port.
              msg: valid message (see Messages below)
              ip: IP address of the sender
              port: port of the sender

        If the reply is an “Error” message then it will be returned just like
        any other message. No exception will be raised.

        If msg is not a valid message (see Messages below) then raises
        NetBotSocketException.

        Immediately raises NetBotSocketException if the receive buffer is empty.

        Note, the text above assumes the socket timeout is set to 0
        (non-blocking), which is the default in NetBotSocket.

        """
        try:
            bytesAddressPair = self.s.recvfrom(self.bufferSize)
            # Convert data from network binary format to python objects
            msg = self.deserialize(bytesAddressPair[0])
            ip = bytesAddressPair[1][0]
            port = bytesAddressPair[1][1]
            log("Received msg from " + ip + ":" + str(port) + " len=" +
                str(len(bytesAddressPair[0])) + " bytes " + str(msg), "DEBUG")

            self.recv = self.recv + 1
            if msg['type'] in self.recvTypes:
                self.recvTypes[msg['type']] += 1
            else:
                self.recvTypes[msg['type']] = 1
        except (BlockingIOError, socket.timeout):
            # There was no data in the receive buffer.
            raise NetBotSocketException("Receive buffer empty.")
        except (ConnectionResetError):
            # Windows raises this when it gets back an ICMP destination unreachable packet
            log("The destination ip:port returned ICMP destination unreachable. Is the destination running?", "WARNING")
            raise NetBotSocketException(
                "The destination ip:port returned ICMP destination unreachable. Is the destination running?")

        if not isValidMsg(msg):
            raise NetBotSocketException("Received message invalid format.")

        # If we get a joinReply then use the server conf to tune our send delay in sendRecvMessage()
        if msg['type'] == 'joinReply':
            self.setDelay(msg['conf']['stepSec'] * 2)

        return msg, ip, port

    def sendRecvMessage(self, msg, destinationIP=None, destinationPort=None,
                        retries=10, delay=None, delayMultiplier=1.2):
        """
        Sends msg to destinationIP:destinationPort and then returns the reply.
        sendRecvMessage is considered synchronous because it will not return
        until and unless a reply is received. Programmers can this of this much
        like a normal function call.

        msg must be a valid message (see Messages below)

        If destinationIP or destinationPort is not provided then the default will
        be used (see setDestinationAddress()).

        If the reply is an “Error” message then a NetBotSocketException exception
        will be raised.

        If no reply is received then the message will be sent again (retried) in
        case it was dropped by the network. If the maximum number of retries is
        reached then a NetBotSocketException exception will be raised.

        Raises NetBotSocketException exception if the msg does not hae a valid format.
        """

        startTime = time.perf_counter()
        self.sendRecvMessageCalls += 1

        if destinationIP is None:
            destinationIP = self.destinationIP

        if destinationPort is None:
            destinationPort = self.destinationPort

        if delay:
            nextDelay = delay
        else:
            nextDelay = self.sendrecvDelay

        remaining = retries

        self.msgID = self.msgID + 1
        if self.msgID > 65000:
            self.msgID = 0

        msg['msgID'] = self.msgID

        gotReply = False
        sendMessage = True
        while remaining != 0 and gotReply == False:
            if sendMessage:
                remaining = remaining - 1
                self.sendMessage(msg, destinationIP, destinationPort)
                self.s.settimeout(nextDelay)
                nextDelay = nextDelay * delayMultiplier

            try:
                replyMsg, ip, port = self.recvMessage()
            except NetBotSocketException as e:
                # We didn't get anything from the buffer or it was an invald message.
                ip = None

            if ip is not None:
                # if the message came from the same ip:port we sent it to
                if ip == destinationIP and port == destinationPort and \
                        isinstance(replyMsg, dict) and \
                        'msgID' in replyMsg and replyMsg['msgID'] == msg['msgID']:
                    gotReply = True
                else:
                    # we got a message but it was not the one were were looking for. Try to receive again before sending
                    sendMessage = False
            else:
                # there is noting in the receive buffer after the timeout so try sending message again.
                sendMessage = True
                self.sendRecvMessageResends += 1

        self.s.settimeout(0)

        if not gotReply:
            log("Raising Exception NetBotSocketException because failed to get valid respose after " + str(retries) +
                " retries with delay = " + str(delay) + " and delayMultiplier = " + str(delayMultiplier), "VERBOSE")
            raise NetBotSocketException("Failed to get valid respose.")

        if replyMsg['type'] == "Error":
            log("Raising Exception NetBotSocketException because reply message, with correct msgID was of type Error.",
                "VERBOSE")
            raise NetBotSocketException("Received Error Message: " + replyMsg['result'])

        del replyMsg['msgID']

        self.sendRecvMessageTime += time.perf_counter() - startTime
        return replyMsg
