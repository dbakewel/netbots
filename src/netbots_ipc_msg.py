import math

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
                    if fldspec[0] == 'str':
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