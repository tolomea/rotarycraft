# Disclaimers:
I enjoy Rotarycraft and I think it's one of the best industry mods. What follows shouldn't be taken as criticism but rather as a humble suggestion on how an already great mod could maybe be made even better.
It's worth noting that I'm still on my first play through however I have all the bedrock toys, an automated extractor setup and am starting to tinker with Reactorcraft so I feel I'm reasonably familiar with the mod. Also currently I have no other industrial mods in the mix, it's a mostly Reika build.

# Overview:
The basic suggestion here is to treat an entire network of engines and machines connected by shafts and gearboxes as a single entity and calculate the power transferred at the speed where the torque produced by the engines is equal to the torque consumed by the machines. This is backed with proof of concept code on how to do the math relatively efficiently and explanatory text on how to maintain the existing balance.

# Motivation:
A couple things in Rotarycraft bug me, little things that don't feel quite right.
Having input and output ends on shafts, gearboxes and junctions etc is a bit weird, in reality these are inherently reversible objects. Likewise with the torque ratio on shaft junctions.
Somewhere in the docs it says "the "load" on a shaft has no effect on its power consumption - a disconnected shaft still draws any and all power given to it, but simply wastes it".
In reality if you have an engine connected to a machine with a shaft and insert a junction with another shaft coming off the side but going nowhere then aside from adding a little friction the new shaft would have no effect. Currently in Rotarycraft that dangling shaft will waste a significant portion of the total power.
This also has the effect of making clutches less useful, they can turn off machines, but they can't divert the power the machine was using elsewhere.
And finally the handling of junctions in general makes line shaft (http://en.wikipedia.org/wiki/Line_shaft) setups impractical.
I have dozens of DC motors powering pumps, item pumps and autocrafters. It'd be nice to replace the whole lot with a couple of steam engines. But balancing the shaft junctions to distribute it all is prohibitively fiddly especially as new steam engines are added to cope with increasing load.
It'd be even nicer still to have all the heavy machinery hanging off one line shaft via clutches, so I can turn them on and off as needed letting the power redistribute to the ones currently in use.
I understand the power buses and multidirectional clutches are supposed to help with these use cases, but it feels like pasting over the real problems with additional complexity.
The rest of this article is about addressing these issues and doing so without impacting balance and with minimal performance cost.

# Principles:
0: Power = Torque * Speed, the Rotarycraft fundamental law.
1: Engine torque produced generally decreases as speed increases (and eventually hits 0).
2: Machine torque consumed generally increases as speed increases (and eventually goes to infinity).
note: due to 0 the power (produced / consumed) curves do not follow these torque curves, power can actually increase and decrease across the speed range.
3: These torque curves may change over time or depending on fuel etc.
4: Gears simply apply a multiplicative transformation to the torque curves, multiplying and dividing the axis.
5: Equilibrium speeds exist where the total torque produced and consumed curves cross (n.b. due to 0 this is also where the power curves cross). When generated torque > consumed torque speed increases and vice versa bringing the system back to an equilibrium speed.
6: Engines may have an additional function mapping speed to fuel use.
7: Machines may have an additional function mapping speed to cycle time.

# Additional simplifying restrictions (I'll address these later):
2b: Engine torque is restricted to strictly decreasing and at speed 0 all engines are at max torque.
3b: Machine torque is restricted to strictly increasing and at speed 0 all machines are at zero torque.
4b: These restrictions mean any setup has exactly 1 equilibrium speed.

<4 theory diagrams>

# Changes from Rotarycraft:
No input and output sides.
No need for torque ratios on shaft junctions.
No speed / torque mode on gearboxes you just turn it around.
A dangling shaft consumes no power.

# How do you calculate the equilibrium:
Calculating the current equilibrium can be done in a single pass, there is no need to iteratively seek the solution. That pass consists of 3 steps:
1: Gather the total torque produced and consumed curves from the whole network.
2: Calculate the equilibrium speed.
3: Distribute the actual torque and speed back through the network so load limits and cycle times can be calculated.
The attached code implements gather and distribute as recursive depth first searches and can proceed from any point in the network (the origin) applying gearing transformations as it proceeds.
Gather passes around and combines Lines, these are chains of straight line segments. Dealing only in straight segments makes all the math much easier and I haven't found a compelling need for curves yet (n.b. straight segments in torque curves produces parabolic segments in the power curves).
Gather ultimately produces the total torque produced and consumed lines for the whole network. Calc intersects these to produce the equilibrium speed at the origin.
Distribute then spreads this speed back through the network (again applying gearing transformations) so that we can calculate the actual speed and transferred torque at every point.

If the recursive traversal is an issue then it could of course be made iterative, but that would be a lot more fiddly.
You could also cache a bunch of stuff, every block would need a quick way to find the origin of it's network. Then at the origin you would need a list of every engine and machine and their gear differences with respect to the origin. That would let you skip gather for non topology changes, and work out the speed at each engine and machine. However to get the true transmitted torque I think you still have to run distribute, but that could be done less frequently as it's only needed for user info and load limit checks.
I need to think some more to see if I can concoct a way of doing the calculation as block to block updates like redstone, I'm not optimistic about the chances of that being possible.

# Replicating Current Balance
For the simpler devices you can draw the torque produced and consumed curves to replicate the existing output / minimum input. The generic statement I have above as principle 7 lets you independently control things like decreasing cycle times with increasing speed and minimum speed cutoffs. These curves also need to be redrawn from current ones but these two mechanics let you get many simple setups working with a close approximation of current balance. For example here's the theory diagrams from above redrawn for a DC engine and a pump:

<DC pump diagrams>

You'll note that I changed the shape of the engine curve, this isn't strictly necessary but reduces the chance of accidentally introducing balance breaking behavior.
I mentioned above that gears transform the curves, here's an example of that:

<Wind grinder diagrams>

Principle 3 covers off the rest of the interesting engine behavior. Microturbine windup, wind turbine altitude, hydrokinetic fall height etc are all covered by that. Also the curves in the diagrams are quite boring and focused on preserving current gameplay, they could be redrawn to give more personality to the various engines, for example giving electric engines a wide speed range over which they produce near peak power.
That brings us to the machines, most of these are already dealt with by the above, however there are some problems. The extractor is an interesting example both of those problems and advanced balance mechanics. The heart of the issue is that speed and torque inputs to a machine are now coupled, so you can't use the ratio between them as a mechanism for controlling the behavior of the machine.
For the extractor I've only found one way around this issue that preserves it's very unusual balance mechanism. That is to give each stage an enable switch in the GUI and have separate torque curves for all 15 combinations, choosing those torque curves to replicate the current minimum requirements to run just the associated stages. Unfortunately for the friction heater the only option seems to be to drop the efficiency mechanic entirely.
Flywheels are another interesting case, these essentially have an internal speed and act as engines below that speed and machines above it, with very steep torque curves that constrain the whole network to remain near the speed of the flywheel. I haven't done a proof of concept of these yet but I'm confident it can be managed.

# Dynamic variant:
I another variant on this system, the one detailed above I call static it is simpler, has better compatibility with existing Rotarycraft and handles chunk loading smoother, the other I call dynamic.
We remove the "additional simplifying restrictions", which allows for some interesting additional behavior.
A setup may have multiple equilibrium speeds and manipulating the system in real time can bump it from one equilibrium to another.
This allows for engine that can stall out and machines that require extra torque to get them started. It can even allow for engines that require starter motors.
In practice this is only fractionally harder to calculate. However in game play terms it makes things a lot more temperamental and fiddly and brings in problems like chunk unloading and reloading causing your whole system to stall out requiring a manual restart process.
Ultimately I'm not convinced that these behaviors are worth the extra complexity.

# An example of the difference:
We have a steam engine driving some machines, the system is turning and at equilibrium.
We add a new machine to the line (perhaps by engaging a clutch) overloading the steam engine, the setup winds down to a halt, technically we've lifted the consumed torque curve so the only equilibrium speed is at 0.
We remove the new machine returning the setup to it's previous state.
In the static system the steam engine has max torque at 0 speed so it spins up to it's old speed and the setup returns to the old (and only) equilibrium speed.
In the dynamic system the steam engine might have no torque at low speed, so it can't restart the existing machines, it's effectively stalled, technically speaking the setup actually has two equilibrium speeds the second being at 0 speed, before we messed with it it was operating at the higher equilibrium speed, now we've bumped it to the lower one.
To restart the steam engine we have to remove all the load so it is free to spin up to full speed, then we can reattach the load and it will settle into the original equilibrium.

# Fin
