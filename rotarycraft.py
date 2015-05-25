from __future__ import division

from collections import defaultdict, OrderedDict

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
        points = [(s/abs(i), t*i, g*i*abs(i)) for (s, t, g) in self.points]
        return Line(*points)

    def __truediv__(self, i):
        return self * (1 / i)

    def __str__(self):
        return "Line(" + ", ".join(str(p) for p in self.points) + ")"

    def __eq__(self, other):
        return self.points == other.points

    def get_zero_intersect(self):
        for p, op in pairs(self.points):
            if op[1] <= 0:
                break
        else:
            p = self.points[-1]
        if p[2]:
            return p[0] - p[1] / p[2]
        else:
            return p[0]


assert Line.make((0,0), (10,10)) == Line((0,0,1))
assert Line.make((0,0), (10,10)) * 2 == Line((0, 0, 4))
assert Line.make((0,0), (10,10)) / 2 == Line((0, 0, 0.25))
assert Line.make((0,0), (10,10), (20, 10)) == Line((0, 0, 1), (10, 10, 0))
assert Line.make((0,0), (10,10), (20, 10)) * 2 == Line((0, 0, 4), (5, 20, 0))
assert Line.make((0,0), (10,10), (20, 10)) / 2 == Line((0, 0, 0.25), (20, 5, 0))
assert Line.make((0,10), (10,10), (20, 0)) == Line((0, 10, 0), (10, 10, -1), (20, 0, 0))
assert Line.make((0,10), (10,10), (20, 0)) * 2 == Line((0, 20, 0), (5, 20, -4), (10, 0, 0))
assert Line.make((0,10), (10,10), (20, 0)) / 2 == Line((0, 5, 0), (20, 5, -0.25), (40, 0, 0))

assert Line.make((0,0), (10,10)) + Line.make((0,0), (10,10)) == Line((0, 0.0, 2.0))
assert Line.make((0,0), (10,10), (20,20)) + Line.make((0,0), (10,10), (20,20)) == Line((0, 0, 2.0), (10, 20.0, 2.0))
assert Line.make((0,0), (10,10), (20,20)) + Line.make((0,0), (10,10)) == Line((0, 0, 2.0), (10, 20.0, 2.0))
assert Line.make((0,0), (10,10)) + Line.make((0,10), (5,10), (15,0)) == Line((0, 10, 1.0), (5, 15.0, 0.0), (15, 15.0, 1.0))
assert Line.make((0,10), (5,10), (15,0)) + Line.make((0,0), (10,10)) == Line((0, 10, 1.0), (5, 15.0, 0.0), (15, 15.0, 1.0))


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


class Shaft(Node):
    pass


class GearBox(Node):
    pass


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


class WindTurbine(BasicEngine):
    # 4nm * 1024rad/s = 4096w
    speed = 1024
    torque = 4


class SteamEngine(BasicEngine):
    # 32nm * 512rad/s = 16384w
    speed = 512
    torque = 32


class Fan(BasicMachine):
    # 1nm * 1024rad/s = 1024w
    speed = 1024
    torque = 1


class Grinder(BasicMachine):
    # 128nm * 32rad/s = 4096w
    speed = 32
    torque = 128


class ItemPump(BasicMachine):
    # 4nm * 256rad/s = 1024w
    speed = 256
    torque = 4


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
    torque = supplied.get_torque(speed)
    print "{:{}}    speed   torque    power".format(name, TITLE_WIDTH)

    supplied, consumed = distribute(root, speed)
    print
    assert abs(supplied - consumed) < .1
    return speed, supplied


if __name__ == "__main__":
    if 1:
        print "-- Disconnected --"

        root = WindTurbine()
        calc("", root)

        root = Fan()
        calc("", root)

        root = Shaft()
        calc("", root)

    if 1:
        print
        print "-- Fans --"

        root = Shaft(WindTurbine())
        calc("0", root)

        root = Shaft(WindTurbine(), Fan())
        calc("1", root)

        root = Shaft(WindTurbine(), Fan(), Fan())
        calc("2", root)

        root = Shaft(WindTurbine(), Fan(), Fan(), Fan())
        calc("3", root)

        root = Shaft(WindTurbine(), Fan(), Fan(), Fan(), Fan())
        calc("4", root)

        root = Shaft(WindTurbine(), Fan(), Fan(), Fan(), Fan(), Fan())
        calc("5", root)

        root = Shaft(WindTurbine(), Fan(), Fan(), Fan(), Fan(), Fan(), Fan())
        calc("6", root)

    if 1:
        print
        print "-- Twin Turbines --"

        turbines = Shaft(WindTurbine(), WindTurbine())
        fans = Shaft(Fan(), Fan(), Fan(), Fan(), Fan(), Fan(), Fan(), Fan())
        root = Shaft(turbines, fans)
        calc("Flat", root)

        turbines = Shaft(WindTurbine(), WindTurbine())
        fans = Shaft(Shaft(Shaft(Fan(), Fan()), Shaft(Fan(), Fan())), Shaft(Shaft(Fan(), Fan()), Shaft(Fan(), Fan())))
        root = Shaft(turbines, fans)
        calc("Tree", root)

        turbines = Shaft(WindTurbine(), WindTurbine())
        fans = Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Fan())))))))
        root = Shaft(turbines, fans)
        calc("Chain", root)

    if 1:
        print
        print "-- Gearing Up --"

        root = Shaft(WindTurbine(), Grinder())
        calc("None", root)

        root = GearBox((1, WindTurbine()), Grinder())
        calc("1:1", root)

        root = GearBox((16, WindTurbine()), Grinder())
        calc("16:1", root)

        root = GearBox((32, WindTurbine()), Grinder())
        calc("32:1", root)

        root = GearBox((64, WindTurbine()), Grinder())
        calc("64:1", root)

    if 1:
        print
        print "-- Gearing Down --"

        root = Shaft(WindTurbine(), Grinder())
        calc("None", root)

        root = GearBox(WindTurbine(), (1/1, Grinder()))
        calc("1:1", root)

        root = GearBox(WindTurbine(), (1/16, Grinder()))
        calc("16:1", root)

        root = GearBox(WindTurbine(), (1/32, Grinder()))
        calc("32:1", root)

        root = GearBox(WindTurbine(), (1/64, Grinder()))
        calc("64:1", root)

    if 1:
        print
        print "-- Gears Different Root --"

        root = Grinder(Shaft(WindTurbine()))
        calc("None", root)

        root = Grinder(GearBox((1, WindTurbine())))
        calc("1:1", root)

        root = Grinder(GearBox((16, WindTurbine())))
        calc("16:1", root)

        root = Grinder(GearBox((32, WindTurbine())))
        calc("32:1", root)

        root = Grinder(GearBox((64, WindTurbine())))
        calc("64:1", root)

    if 1:
        print
        print "-- TNT Machine --"

        root = SteamEngine(GearBox((1/16, Shaft(
            Grinder(),
            Grinder(),
            Grinder(),
            GearBox((8, Shaft(
                ItemPump(),
                ItemPump(),
                ItemPump(),
            )))
        ))))
        calc("Flat", root)

        root = SteamEngine(GearBox((1/16, Shaft(
            Shaft(
                Grinder(),
                Grinder(),
            ),
            Shaft(
                Grinder(),
                GearBox((8, Shaft(
                    ItemPump(),
                    Shaft(
                        ItemPump(),
                        ItemPump(),
                    )
                )))
            )
        ))))
        calc("Real", root)

    if 1:
        print
        print "-- Unloaded --"

        root = Shaft(GearBox((32, WindTurbine()), Grinder()))
        calc("Shaft", root)

        root = GearBox((32, WindTurbine()), Grinder(), Shaft())
        calc("Side", root)

        root = Shaft(GearBox((32, WindTurbine()), Grinder()), GearBox((32, WindTurbine()), Grinder()))
        calc("Link", root)



"""
Extractor
a     128 512 65536
b    2048   8 16384
c    8192   4 32768
d     256 256 65536

ab   2048 512
ac   8192 512
ad    256 512
bc   8192   8
bd   2048 256
cd   8192 256

abc
abd
acd
bcd

abcd 8192 512
"""

def L(s, t):
    return Line.make((0, 0), (s, t))

a = L(128, 512)
b = L(2048, 8)
c = L(8192, 4)
d = L(256, 256)
ab = L(2048, 512)
#assert ab.get_torque(1) >= max(a.get_torque(1), b.get_torque(1))

print "ab", (a + b).get_torque(2048)


print "abcd", (a + b + c + d).get_torque(8192)
