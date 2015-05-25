from __future__ import division


# making things up
ITERATIONS = 1000
MULTIPLIER = .5

class Node(object):
    def __init__(self, *neighbours):
        self.neighbours = set()
        for node in neighbours:
            self.attach(node)

    def attach(self, node):
        if node not in self.neighbours:
            self.neighbours.add(node)
            node.attach(self)

    def gear_shift_torque_in(self, torque, node):
        return torque

    def gear_shift_torque_out(self, torque, node):
        return torque

    def gear_shift_speed_in(self, speed, node):
        return speed

    def gear_shift_speed_out(self, speed, node):
        return speed

    def check_load_limits(self, torque, speed):
        pass

    def supplied_torque(self, speed):
        return 0

    def consumed_torque(self, speed):
        return 0


class Shaft(Node):
    pass


class GearBox(Node):
    def __init__(self, *neighbours):
        self.neighbours = dict()
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

    def gear_shift_torque_in(self, torque, node):
        return torque * self.neighbours.get(node, 1)

    def gear_shift_torque_out(self, torque, node):
        return torque / self.neighbours.get(node, 1)

    def gear_shift_speed_in(self, speed, node):
        return speed / self.neighbours.get(node, 1)

    def gear_shift_speed_out(self, speed, node):
        return speed * self.neighbours.get(node, 1)

    def check_load_limits(self, torque, speed):
        # adjust for the true torque load on the gears
        torque /= min(self.neighbours.values())


class BasicEngine(Node):
    # subclass defines speed and torque for peak power
    # torque is flat below that speed and fades out toward that speed * 2
    def supplied_torque(self, speed):
        if speed < self.speed:
            return self.torque
        return max(0, self.speed * 2 - speed) / self.speed * self.torque


class WindTurbine(BasicEngine):
    # 4nm * 1024rad/s = 4096w
    speed = 1024
    torque = 4


class SteamEngine(BasicEngine):
    # 32nm * 512rad/s = 16384w
    speed = 512
    torque = 32


class Fan(Node):
    # 2nm * 512rad/s = 1024w
    # 1nm * 1024rad/s = 1024w
    def consumed_torque(self, speed):
        return speed / 1024


class Grinder(Node):
    # 128nm * 32rad/s = 4096w
    def consumed_torque(self, speed):
        return speed * 4


class Utility(Node):
    # 4nm * 256rad/s = 1024w
    def consumed_torque(self, speed):
        return speed / 64


def calc_torque(node, speed, origin=None):
    speed = node.gear_shift_speed_in(speed, origin)
    total_supplied = node.supplied_torque(speed)
    total_consumed = node.consumed_torque(speed)
    for n in node.neighbours:
        if n != origin:
            s = node.gear_shift_speed_out(speed, n)
            supplied, consumed = calc_torque(n, s, node)
            supplied = node.gear_shift_torque_in(supplied, n)
            consumed = node.gear_shift_torque_in(consumed, n)
            total_supplied += supplied
            total_consumed += consumed
    total_supplied = node.gear_shift_torque_out(total_supplied, origin)
    total_consumed = node.gear_shift_torque_out(total_consumed, origin)
    return total_supplied, total_consumed


def check_limits(node, speed, scale, origin=None):
    speed = node.gear_shift_speed_in(speed, origin)
    total_supplied = node.supplied_torque(speed)
    total_consumed = node.consumed_torque(speed)
    if scale > 1:
        total_supplied /= scale
    else:
        total_consumed *= scale
    total_difference = abs(total_supplied - total_consumed)
    for n in node.neighbours:
        if n != origin:
            s = node.gear_shift_speed_out(speed, n)
            supplied, consumed = check_limits(n, s, scale, node)
            supplied = node.gear_shift_torque_in(supplied, n)
            consumed = node.gear_shift_torque_in(consumed, n)
            total_supplied += supplied
            total_consumed += consumed
            total_difference += abs(supplied - consumed)
    # the origin is responsible for any difference in torque
    total_difference += abs(total_supplied - total_consumed)
    # we've double counted all the torque differences
    transmitted_torque = total_difference / 2
    node.check_load_limits(transmitted_torque, speed)
    total_supplied = node.gear_shift_torque_out(total_supplied, origin)
    total_consumed = node.gear_shift_torque_out(total_consumed, origin)
    return total_supplied, total_consumed


def eval(root, cycles):
    speed = 1
    for i in range(cycles):
        supplied, consumed = calc_torque(root, speed)
        scale = supplied / consumed if consumed else 0
        check_limits(root, speed, scale)
        # print "{:2} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f}".format(i, speed, supplied, consumed, speed * consumed, scale)

        if consumed:
            # this code really wants to know the gradient of the consumed torque curve at the current speed
            # currently I cheat by assuming it's linear back to 0
            est_final_torque = (supplied + consumed) / 2
            est_final_speed = speed / consumed * est_final_torque
            difference = est_final_speed - speed
            speed += difference * MULTIPLIER
        else:
            # the cheat doesn't work for supplied torque as it doesn't intersect at 0
            # so for now we're just making stuff up
            speed += (supplied - consumed) * 100

        speed = max(speed, 0)
    print "{:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f}".format(speed, supplied, consumed, supplied - consumed, speed * consumed)

if __name__ == "__main__":
    print "name     speed   trq_in  trq_out     diff    power"

    if 1:
        print
        print "fans"

        print "0    ",
        root = Shaft(WindTurbine())
        eval(root, ITERATIONS)

        print "1    ",
        root = Shaft(WindTurbine(), Fan())
        eval(root, ITERATIONS)

        print "2    ",
        root = Shaft(WindTurbine(), Fan(), Fan())
        eval(root, ITERATIONS)

        print "3    ",
        root = Shaft(WindTurbine(), Fan(), Fan(), Fan())
        eval(root, ITERATIONS)

        print "4    ",
        root = Shaft(WindTurbine(), Fan(), Fan(), Fan(), Fan())
        eval(root, ITERATIONS)

        print "5    ",
        root = Shaft(WindTurbine(), Fan(), Fan(), Fan(), Fan(), Fan())
        eval(root, ITERATIONS)

        print "6    ",
        root = Shaft(WindTurbine(), Fan(), Fan(), Fan(), Fan(), Fan(), Fan())
        eval(root, ITERATIONS)

    if 1:
        print
        print "twin turbines"

        print "flat ",
        turbines = Shaft(WindTurbine(), WindTurbine())
        fans = Shaft(Fan(), Fan(), Fan(), Fan(), Fan(), Fan(), Fan(), Fan())
        root = Shaft(turbines, fans)
        eval(root, ITERATIONS)

        print "tree ",
        turbines = Shaft(WindTurbine(), WindTurbine())
        fans = Shaft(Shaft(Shaft(Fan(), Fan()), Shaft(Fan(), Fan())), Shaft(Shaft(Fan(), Fan()), Shaft(Fan(), Fan())))
        root = Shaft(turbines, fans)
        eval(root, ITERATIONS)

        print "chain",
        turbines = Shaft(WindTurbine(), WindTurbine())
        fans = Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Shaft(Fan(), Fan())))))))
        root = Shaft(turbines, fans)
        eval(root, ITERATIONS)

    if 1:
        print
        print "gears"

        print "none ",
        root = Shaft(WindTurbine(), Grinder())
        eval(root, ITERATIONS)

        print "1:1  ",
        root = GearBox((1, WindTurbine()), Grinder())
        eval(root, ITERATIONS)

        print "16:1 ",
        root = GearBox((16, WindTurbine()), Grinder())
        eval(root, ITERATIONS)

        print "32:1 ",
        root = GearBox((32, WindTurbine()), Grinder())
        eval(root, ITERATIONS)

        print "64:1 ",
        root = GearBox((64, WindTurbine()), Grinder())
        eval(root, ITERATIONS)

    if 1:
        print
        print "gears 2"

        print "none ",
        root = Shaft(WindTurbine(), Grinder())
        eval(root, ITERATIONS)

        print "1:1  ",
        root = GearBox(WindTurbine(), (1/1, Grinder()))
        eval(root, ITERATIONS)

        print "16:1 ",
        root = GearBox(WindTurbine(), (1/16, Grinder()))
        eval(root, ITERATIONS)

        print "32:1 ",
        root = GearBox(WindTurbine(), (1/32, Grinder()))
        eval(root, ITERATIONS)

        print "64:1 ",
        root = GearBox(WindTurbine(), (1/64, Grinder()))
        eval(root, ITERATIONS)

    if 1:
        print
        print "gears 3"

        print "none ",
        root = Grinder(Shaft(WindTurbine()))
        eval(root, ITERATIONS)

        print "1:1  ",
        root = Grinder(GearBox((1, WindTurbine())))
        eval(root, ITERATIONS)

        print "16:1 ",
        root = Grinder(GearBox((16, WindTurbine())))
        eval(root, ITERATIONS)

        print "32:1 ",
        root = Grinder(GearBox((32, WindTurbine())))
        eval(root, ITERATIONS)

        print "64:1 ",
        root = Grinder(GearBox((64, WindTurbine())))
        eval(root, ITERATIONS)

    if 1:
        print
        print "tnt machine"

        print "real ",
        root = SteamEngine(GearBox((1/16, Shaft(
            Shaft(
                Grinder(),
                Grinder(),
            ),
            Shaft(
                Grinder(),
                GearBox((8, Shaft(
                    Utility(),
                    Shaft(
                        Utility(),
                        Utility(),
                    )
                )))
            )
        ))))
        eval(root, ITERATIONS)

        print "flat ",
        root = SteamEngine(GearBox((1/16, Shaft(
            Grinder(),
            Grinder(),
            Grinder(),
            GearBox((8, Shaft(
                Utility(),
                Utility(),
                Utility(),
            )))
        ))))
        eval(root, ITERATIONS)
