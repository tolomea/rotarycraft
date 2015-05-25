from __future__ import division

from lib import calc, Node, BasicEngine, BasicMachine


class Shaft(Node):
    pass


class GearBox(Node):
    pass


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
        fans = Shaft(
            Shaft(
                Shaft(Fan(), Fan()),
                Shaft(Fan(), Fan()),
            ), Shaft(
                Shaft(Fan(), Fan()),
                Shaft(Fan(), Fan()),
            )
        )
        root = Shaft(turbines, fans)
        calc("Tree", root)

        turbines = Shaft(WindTurbine(), WindTurbine())
        fans = Shaft(
            Fan(),
            Shaft(
                Fan(),
                Shaft(
                    Fan(),
                    Shaft(
                        Fan(),
                        Shaft(
                            Fan(),
                            Shaft(
                                Fan(),
                                Shaft(
                                    Fan(),
                                    Fan(),
                                )
                            )
                        )
                    )
                )
            )
        )
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

        root = Shaft(
            GearBox((32, WindTurbine()), Grinder()),
            GearBox((32, WindTurbine()), Grinder()),
        )
        calc("Link", root)
