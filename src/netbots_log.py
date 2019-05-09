
import inspect
import os
from datetime import datetime

# global printing of debug and info log level messages on/off
logDebug = False
logVerbose = False


def setLogLevel(debug=False, verbose=False):
    """
    Turn DEBUG and VERBOSE printing on or off. Both are off by default.
    Note, debug = True will set verbose = True.
    """

    global logDebug, logVerbose

    logDebug = debug
    if logDebug == True:
        verbose = True
    logVerbose = verbose
    log("DEBUG logging = " + str(logDebug) + ". VERBOSE logging = " + str(logVerbose), "INFO")


def log(msg, level="INFO"):
    """
    Print msg to standard output in the format: LogLevel Time Function: msg

    level should be one of DEBUG, VERBOSE, INFO, WARNING, ERROR, or FAILURE.
    Use log level as follows:
            DEBUG: Very detailed information, such as network messages.
            VERBOSE: Detailed information about normal function of program.
            INFO: Information about the normal functioning of the program. (default log level).
            WARNING: Something unexpected happened but normal program flow can continue.
            ERROR: Can not continue as planned.
            FAILURE: program will need to quit or initialize.

    """

    global logDebug, logVerbose

    if level == "DEBUG" and logDebug == False:
        return

    if level == "VERBOSE" and logVerbose == False:
        return

    try:
        # Get the execution frame of the calling function and use it to determine the calling filename and function name
        # This will fail if called from a python interactive shell.
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        filename = os.path.basename(module.__file__)
        modulename = module.__name__
        function = frame[0].f_code.co_name
        if function != '<module>':
            function = function + '()'
    except Exception as e:
        modulename = '-'
        filename = '-'
        function = '-'

    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    print(level + ' ' + str(time) + ' ' + str(modulename) + '.' + str(function) + ': ' + str(msg))
