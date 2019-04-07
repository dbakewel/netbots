import math

############################################################
### Note, all angles below are in radians. You can convert 
### between degrees and radians in your code as follows:
###
### import math
### r = math.radians(d)
### d = math.degrees(r)
###
#############################################################

def normalizeAngle(a):
    """ Return a in range 0 - 2pi. a must be in radians. """
    if a < 0:
        a += math.pi*2
    elif a >= math.pi*2:
        a -= math.pi*2
    return a

def angle(x1,y1,x2,y2):
    """ Return angle from (x1,y1) and (x2,y2) in radians. """
    delta_x = x2 - x1
    delta_y = y2 - y1
    a = math.atan2(delta_y, delta_x)

    # atan2 return between -pi and pi. We want between 0 and 2pi with 0 degrees at 3 oclock
    return normalizeAngle(a)

def distance(x1,y1,x2,y2):
    """ Return distance between (x1,y1) and (x2,y2) """
    return math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))

def contains(x1,y1,startRad,endRad,x2,y2):
    """
    Return distance between points only if point falls inside a specific range of angles.
    Otherwise return 0.

    if angle from (x1,y1) to (x2,y2) is between startRad and clockwise to endRad then
        return distance from (x1,y1) to (x2,y2)
    else
        return 0
    """
    dist = 0

    a = angle(x1,y1,x2,y2)
    if(startRad > endRad): #if we are scanning clockwise over 0 radians.
        if startRad <= a or a <= endRad:
            dist = distance(x1,y1,x2,y2)
    elif startRad <= a and a <= endRad:
        dist = distance(x1,y1,x2,y2)

    return dist

def project(x,y,rad,dis):
    """
    Return point (x',y') where angle from (x,y) to (x',y')
    is rad and distance from (x,y) to (x',y') dis.
    """

    xp = x + dis * math.cos(rad)
    yp = y + dis * math.sin(rad)

    return xp, yp