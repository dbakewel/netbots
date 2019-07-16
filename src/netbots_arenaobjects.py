from abc import ABC, abstractmethod


class Shape(ABC):
    def __init__(self):
        super().__init__()
        self.shape = 'abstract'

    @abstractmethod
    def overlap(self, shape):
        pass

class Circle(Shape)
    def __init__(self):
        super().__init__()
        self.shape = 'circle'
        self.x = 0
        self.y = 0
        sefl.r = 1

    def overlap(self, shape):
        pass

class Line(Shape)
    def __init__(self):
        super().__init__()
        self.shape = 'line'
        self.x = 0
        self.y = 0
        self.x2 = 1
        self.y2 = 1

    def overlap(self, shape):
        pass

class Point(Shape)
    def __init__(self):
        super().__init__()
        self.shape = 'point'
        self.x = 0
        self.y = 0

    def overlap(self, shape):
        pass

class ArenaObject(ABC):
 
    def __init__(self,srvConf,shape):
        super().__init__()
        self.srvConf = srvConf
        self.canMove = False
        self.shape = shape
        
    @abstractmethod
    def step(self):
        pass


class Robot(ArenaObject):
    def __init__(self,srvConf):
        super().__init__(srvConf, Circle())
        self.canMove = True
        self.

class Shell(ArenaObject):
    def __init__(self,srvConf):
        super().__init__(srvConf, Point())
        self.srvConf = srvConf
        self.canMove = True

class Explosion(ArenaObject):
    def __init__(self,srvConf):
        super().__init__(srvConf, Circle())
        self.canMove = False


class Obstacle(ArenaObject):
    def __init__(self,srvConf):
        super().__init__(srvConf, Circle())
        self.canMove = False

    def step(self):
        pass

class JamZone(ArenaObject):
    def step(self):
        pass