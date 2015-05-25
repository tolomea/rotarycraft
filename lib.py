from __future__ import division

from collections import OrderedDict

TITLE_WIDTH = 15


def pairs(seq):
    for x in zip(seq[:-1], seq[1:]):
        yield x


class Line(object):
    def __init__(self, *points):
        """ points are (speed, torque, gradient) """
        self.points = points

    @classmethod
    def make(cls, *points):
        """ points are (speed, torque) """

        # first point must be speed 0
        assert points[0][0] == 0

        # points must proceed in increasing speed order
        for op, p in pairs(points):
            assert p[0] > op[0]

        # if last segment is negative going then it must finish on 0 torque
        if points[-2][1] > points[-1][1]:
            assert points[-1][1] == 0

        res = []
        for op, p in pairs(points):
            gradient = (p[1] - op[1]) / (p[0] - op[0])
            res.append((op[0], op[1], gradient))
        # zero intersect for downward lines
        if p[1] == 0:
            res.append((p[0], p[1], 0))

        return cls(*res)

    @classmethod
    def zero(cls):
        return cls((0, 0, 0))

    def get_torque(self, speed):
        op = self.points[0]
        for p in self.points[1:]:
            if p[0] > speed:
                break
            op = p
        return (speed - op[0]) * op[2] + op[1]

    def __add__(self, other):
        # get (speed, gradient) pairs for the start and end of each segment
        x = [(p[0], p[2]) for p in (self.points + other.points)]
        for op, p in pairs(self.points):
            x.append((p[0], -op[2]))
        for op, p in pairs(other.points):
            x.append((p[0], -op[2]))

        t = self.points[0][1] + other.points[0][1]
        g = 0
        s = 0
        points = []
        for p in sorted(x):
            if p[0] != s:
                points.append((s, t, g))
                t += (p[0] - s) * g
                s = p[0]
            g += p[1]
        t += (p[0] - s) * g
        points.append((s, t, g))
        return Line(*points)

    def __sub__(self, other):
        return self + (other * -1)

    def __mul__(self, i):
        points = [(s / abs(i), t * i, g * i * abs(i)) for (s, t, g) in self.points]
        return Line(*points)

    def __truediv__(self, i):
        return self * (1 / i)

    def __str__(self):
        return "Line(" + ", ".join(str(p) for p in self.points) + ")"

    def __eq__(self, other):
        return self.points == other.points

    def get_zero_intersect(self):
        for op, p in pairs(self.points):
            if p[1] <= 0:
                break
        else:
            op = self.points[-1]
        if op[2]:
            return op[0] - op[1] / op[2]
        else:
            return op[0]


assert Line.make((0, 0), (10, 10)) == Line((0, 0, 1))
assert Line.make((0, 0), (10, 10)) * 2 == Line((0, 0, 4))
assert Line.make((0, 0), (10, 10)) / 2 == Line((0, 0, 0.25))
assert Line.make((0, 0), (10, 10), (20, 10)) == Line((0, 0, 1), (10, 10, 0))
assert Line.make((0, 0), (10, 10), (20, 10)) * 2 == Line((0, 0, 4), (5, 20, 0))
assert Line.make((0, 0), (10, 10), (20, 10)) / 2 == Line((0, 0, 0.25), (20, 5, 0))
assert Line.make((0, 10), (10, 10), (20, 0)) == Line((0, 10, 0), (10, 10, -1), (20, 0, 0))
assert Line.make((0, 10), (10, 10), (20, 0)) * 2 == Line((0, 20, 0), (5, 20, -4), (10, 0, 0))
assert Line.make((0, 10), (10, 10), (20, 0)) / 2 == Line((0, 5, 0), (20, 5, -0.25), (40, 0, 0))

assert Line.make((0, 0), (10, 10)) + Line.make((0, 0), (10, 10)) == Line((0, 0.0, 2.0))
assert Line.make((0, 0), (10, 10), (20, 20)) + Line.make((0, 0), (10, 10), (20, 20)) == Line((0, 0, 2.0), (10, 20.0, 2.0))
assert Line.make((0, 0), (10, 10), (20, 20)) + Line.make((0, 0), (10, 10)) == Line((0, 0, 2.0), (10, 20.0, 2.0))
assert Line.make((0, 0), (10, 10)) + Line.make((0, 10), (5, 10), (15, 0)) == Line((0, 10, 1.0), (5, 15.0, 0.0), (15, 15.0, 1.0))
assert Line.make((0, 10), (5, 10), (15, 0)) + Line.make((0, 0), (10, 10)) == Line((0, 10, 1.0), (5, 15.0, 0.0), (15, 15.0, 1.0))


class Node(object):
    def __init__(self, *neighbours):
        self.neighbours = OrderedDict()
        for node in neighbours:
            if isinstance(node, tuple):
                ratio, node = node
            else:
                ratio = 1
            self.attach(node, ratio)

    def attach(self, node, ratio=1):
        if node not in self.neighbours:
            self.neighbours[node] = ratio
            node.attach(self)

    def supplied(self):
        return Line.zero()

    def consumed(self):
        return Line.zero()


class BasicEngine(Node):
    # subclass defines speed and torque for peak power
    # torque is flat below that speed and fades out toward that speed * 2
    def supplied(self):
        assert len(self.neighbours) < 2
        return Line.make((0, self.torque), (self.speed, self.torque), (2*self.speed, 0))


class BasicMachine(Node):
    # subclasss defines a speed and torque point
    # torque is a straight increasing line passing through that line
    def consumed(self):
        return Line.make((0, 0), (self.speed, self.torque))


def gather(node, origin=None):
    total_supplied = node.supplied()
    total_consumed = node.consumed()
    for n in node.neighbours:
        if n != origin:
            supplied, consumed = gather(n, node)
            total_supplied += supplied * node.neighbours[n]
            total_consumed += consumed * node.neighbours[n]
    if origin:
        total_supplied /= node.neighbours[origin]
        total_consumed /= node.neighbours[origin]
    return total_supplied, total_consumed


def distribute(node, speed, origin=None, indent=0):
    if origin:
        speed /= node.neighbours[origin]
    total_supplied = node.supplied().get_torque(speed)
    total_consumed = node.consumed().get_torque(speed)
    total_difference = abs(total_supplied - total_consumed)
    for n in node.neighbours:
        if n != origin:
            s = speed * node.neighbours[n]
            supplied, consumed = distribute(n, s, node, indent+1)
            supplied *= node.neighbours[n]
            consumed *= node.neighbours[n]
            total_supplied += supplied
            total_consumed += consumed
            total_difference += abs(supplied - consumed)
    # the origin is responsible for any difference in torque
    total_difference += abs(total_supplied - total_consumed)
    # we've double counted all the torque differences
    transmitted_torque = total_difference / 2
    # and we need to scale it for any gearing
    # this scales it to max torque, for testing break limits we can also scale to max speed
    max_gearing = min(node.neighbours.values() + [1])
    transmitted_torque /= max_gearing
    internal_speed = speed * max_gearing

    print "{:{}} {:8.2f} {:8.2f} {:8.2f}".format(
        " " * indent + node.__class__.__name__,
        TITLE_WIDTH,
        internal_speed,
        transmitted_torque,
        internal_speed * transmitted_torque,
    )

    if origin:
        total_supplied /= node.neighbours[origin]
        total_consumed /= node.neighbours[origin]
    return total_supplied, total_consumed


def calc(name, root):
    supplied, consumed = gather(root)
    total = supplied - consumed
    speed = total.get_zero_intersect()
    print "{:{}}    speed   torque    power".format(name, TITLE_WIDTH)

    supplied, consumed = distribute(root, speed)
    print
    assert abs(supplied - consumed) < .1
