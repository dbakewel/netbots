import math

from netbots_log import log

############################################################
# Note, all angles below are in radians. You can convert
# between degrees and radians in your code as follows:
#
# import math
# r = math.radians(d)
# d = math.degrees(r)
#
#############################################################


def normalizeAngle(a):
    """ Return a in range 0 - 2pi. a must be in radians. """
    while a < 0:
        a += math.pi * 2
    while a >= math.pi * 2:
        a -= math.pi * 2
    return a


def angle(x1, y1, x2, y2):
    """ Return angle from (x1,y1) and (x2,y2) in radians. """
    delta_x = x2 - x1
    delta_y = y2 - y1
    a = math.atan2(delta_y, delta_x)

    # atan2 return between -pi and pi. We want between 0 and 2pi with 0 degrees at 3 oclock
    return normalizeAngle(a)


def distance(x1, y1, x2, y2):
    """ Return distance between (x1,y1) and (x2,y2) """
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def contains(x1, y1, startRad, endRad, x2, y2):
    """
    Return distance between points only if point falls inside a specific range of angles.
    Otherwise return 0.

    if angle from (x1,y1) to (x2,y2) is between startRad and counter clockwise to endRad then
        return distance from (x1,y1) to (x2,y2)
    else
        return 0
    """
    dist = 0

    a = angle(x1, y1, x2, y2)
    if(startRad >= endRad):  # if we are scanning clockwise over 0 radians.
        if startRad <= a or a <= endRad:
            dist = distance(x1, y1, x2, y2)
    elif startRad <= a and a <= endRad:
        dist = distance(x1, y1, x2, y2)

    return dist


def project(x, y, rad, dis):
    """
    Return point (x',y') where angle from (x,y) to (x',y')
    is rad and distance from (x,y) to (x',y') dis.
    """

    xp = x + dis * math.cos(rad)
    yp = y + dis * math.sin(rad)

    return xp, yp


def sgn(x):
    if x < 0:
        return -1
    return 1


def intersectLineCircle(x1, y1, x2, y2, cx, cy, cradius):
    """
    Return True if line segment between (x1,y1) and (x2,y2) intersects circle
    centered at (cx,cy) with radius cradius, or if line segment is entirely
    inside circle.
    """

    # move points so circle is at origin (0,0)
    x1 -= cx
    y1 -= cy
    x2 -= cx
    y2 -= cy

    # easy way first. Just see if one of the points is inside the circle
    d1 = math.sqrt(x1**2 + y1**2)
    d2 = math.sqrt(x2**2 + y2**2)
    if d1 <= cradius or d2 <= cradius:
        return True

    # Find out if infinite line intersect circle
    # From http://mathworld.wolfram.com/Circle-LineIntersection.html
    dx = x2 - x1
    dy = y2 - y1
    dr = math.sqrt(dx**2 + dy**2)
    D = x1 * y2 - x2 * y1
    delta = (cradius * cradius) * dr**2 - D**2
    if delta < 0:
        return False

    # now we know that the line to infinity intersects the circle.
    # but we need to figure out if the line segment touches or not.
    # really only need to test x or y, if one is true so will the other be.
    ix = (D * dy + sgn(dy) * dx * math.sqrt(delta)) / dr**2
    iy = (-1 * D * dx + abs(dy) * math.sqrt(delta)) / dr**2
    if (x1 < ix and ix < x2) or (x1 > ix and ix > x2) or \
       (y1 < ix and ix < y2) or (y1 > ix and ix > y2):
        return True

    return False


def main():
    """ Tests """
    log(intersectLineCircle(56 - 50, -11 - 5, 105 - 50, -16 - 5, 0, 0, 50))


if __name__ == "__main__":
    main()
