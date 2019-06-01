import os
import sys
import math

# include the netbot src directory in sys.path so we can import modules from it.
robotpath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(os.path.dirname(robotpath), "src")
sys.path.insert(0, srcpath)

import netbots_server as nbsrv
import netbots_ipc as nbipc
import netbots_math as nbmath
from netbots_log import setLogLevel
from netbots_log import log

def testHitSeverity():
    d = nbsrv.SrvData()

    b1 = {'class': "default", 'currentSpeed': 100, 'currentDirection': 0}
    if round(nbsrv.getHitSeverity(d,b1,0),8) != round(1,8):
        log("test 1 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1,2*math.pi),8) != round(1,8):
        log("test 1.1 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1,math.pi/4),8) != round(0.7071067811865476,8):
        log("test 2 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1,2*math.pi - math.pi/4),8) != round(0.7071067811865476,8):
        log("test 3 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1,math.pi/2),8) != round(0,8):
        log("test 4 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1,2*math.pi - math.pi/2),8) != round(0,8):
        log("test 5 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1,math.pi),8) != round(0,8):
        log("test 6 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1,math.pi/2+0.01),8) != round(0,8):
        log("test 7 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1,2*math.pi - math.pi/2-0.01),8) != round(0,8):
        log("test 8 failed","ERROR")

    b1 = {'class': "default", 'currentSpeed': 50, 'currentDirection': math.pi + math.pi/2}
    if round(nbsrv.getHitSeverity(d,b1, math.pi + math.pi/2),8) != round(0.5,8):
        log("test 9 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1, math.pi + math.pi/2 + math.pi),8) != round(0,8):
        log("test 10 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1, math.pi + math.pi/2 + math.pi/2),8) != round(0,8):
        log("test 11 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1, math.pi + math.pi/2 - math.pi/2),8) != round(0,8):
        log("test 12 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1, math.pi + math.pi/2 - math.pi/4),8) != round(0.7071067811865476*0.5,8):
        log("test 13 failed","ERROR")

    if round(nbsrv.getHitSeverity(d,b1, math.pi + math.pi/2 + math.pi/4),8) != round(0.7071067811865476*0.5,8):
        log("test 14 failed","ERROR")

    b1 = {'class': "default", 'currentSpeed': 100, 'currentDirection': 0}
    b2 = {'class': "default", 'currentSpeed': 100, 'currentDirection': math.pi}
    if round(nbsrv.getHitSeverity(d,b1, 0, b2),8) != round(2,8):
        log("test 15 failed","ERROR")

    b2 = {'class': "default", 'currentSpeed': 100, 'currentDirection': math.pi/2}
    if round(nbsrv.getHitSeverity(d,b1, 0, b2),8) != round(1,8):
        log("test 16 failed","ERROR")

    b2 = {'class': "default", 'currentSpeed': 100, 'currentDirection': math.pi/4}
    if round(nbsrv.getHitSeverity(d,b1, 0, b2),8) != round(1-0.7071067811865476,8):
        log("test 17 failed","ERROR")

    b2 = {'class': "default", 'currentSpeed': 100, 'currentDirection': math.pi-math.pi/4}
    if round(nbsrv.getHitSeverity(d,b1, 0, b2),8) != round(1+0.7071067811865476,8):
        log("test 18 failed","ERROR")

    b2 = {'class': "default", 'currentSpeed': 100, 'currentDirection': math.pi/4}
    if round(nbsrv.getHitSeverity(d,b1, math.pi, b2),8) != round(0,8):
        log("test 19 failed","ERROR")

def main():
    testHitSeverity()

if __name__ == "__main__":
    main()