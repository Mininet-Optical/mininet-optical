# Installation and Walkthrough

Welcome to the Mininet-Optical walkthrough. After finishing this walkthrough, you should be able
to use the basic Mininet-Optical commands and execute a basic Mininet-Optical topology
python script. You will also get acquainted with control plane configuration using `curl(1)`
commands to create forwarding rules and launch your signals.

## Setting up Mininet-Optical

Since Mininet-Optical is built on top of Mininet, you need to install and successfully test
Mininet before proceeding to work with Mininet-Optical. In this section, you will find the
procedure to install the base Mininet network emulator as well as Mininet-Optical.

### Prerequisites

This walkthrough is designed for Ubuntu/Debian, but may be adjusted for other Linux distributions.

On Ubuntu/Debian, run the following commands before installing Mininet and Mininet-Optical:

    $ sudo apt-get update
    $ sudo apt-get install python3 python3-pip git

### Installing Mininet

To install natively from source, clone the source code repository:

    $ git clone https://github.com/mininet/mininet

Note that the `git` command above will check out the latest and greatest Mininet (which we
recommend!) If you want to run the last tagged/released version of Mininet - or any other
version - you may check that version out explicitly:

    $ cd mininet
    $ git tag  # list available versions
    $ git checkout -b mininet-2.3.0 2.3.0  # Mininet-Optical requires Mininet 2.3.0 or later
    $ cd ..

Once you have the source tree, the command to install Mininet is:

    $ ./mininet/util/install.sh -nv

To test the Mininet functionality, run:

    $ sudo mn --switch ovsbr --test pingall

For any issue encountered during the Mininet installation, or to check
the other installation option and commands, we suggest consulting the
[Mininet documentation](http://mininet.org/).

### Installing Mininet-Optical

Once Mininet is up and running, you will need to clone the
Mininet-Optical repository using the following commands:

    $ git clone https://github.com/mininet-optical/mininet-optical
    $ cd mininet-optical
    $ make depend
    $ make install

## Running a simple Mininet-Optical script

In this section, you will learn to create, configure and run a
topology in Mininet-Optical representing the simplest fully emulated
packet-optical network that we can create. The topology used here is
called `SingleLinkTopo` and consists of 2 hosts, 2 switches, 2
terminals separated by 2x25km spans with an EDFA in the middle:

    h1 - s1 - t1 - (boost->,amp2<-) --25km-- amp1 --25km-- (->amp2,<-boost) - t1 - s2 - h2

To run this topology:

    $ cd ~/mininet-optical
    $ sudo python3 examples/singlelink.py

If the execution is successful, you should see the following:

```
*** Creating network
*** Adding controller
*** Adding hosts:
h1 h2
*** Adding switches:
s1 s2 t1 t2
*** Adding links:
(h1, s1) (h2, s2) (s1, t1) (s2, t2)
*** Configuring hosts
h1 h2
*** Starting controller

*** Starting 4 switches
s1 s2 t1 t2 .........

single-link.py: single link between two terminals

This is a slightly more complicated single-link topology.

Some complexity is added by a span consisting of two 25km
fiber segments with boost amplifiers and compensating amplifiers,
as well as monitors for the terminals.

Also the hosts are now connected to an Ethernet switch rather
than directly to the terminals/transceivers.

To configure the optical network using the REST API:

mn=localhost:8080; t1=$mn; t2=$mn
curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=1'
curl "$t2/connect?node=t2&ethPort=1&wdmPort=2&channel=1'
curl "$t1/turn_on?node=t1'
curl "$t2/turn_on?node=t2'
*** Starting CLI:
mininet-optical>
```

At this point the topology is created, but routing from Host `h1`
to Host `h2` is still not possible since no rules have been given to the
devices and no signals have been launched.  However, it is still
possible to run several commands to check the topology and components.

### Mininet-Optical commands

Nodes:
```
mininet-optical> nodes
available nodes are:
h1 h2 s1 s2 t1 t1-monitor t2 t2-monitor
```

Network:
```
mininet-optical> net
h1 h1-eth0:s1-eth1
h2 h2-eth0:s2-eth1
s1 lo:  s1-eth1:h1-eth0 s1-eth2:t1-eth1
s2 lo:  s2-eth1:h2-eth0 s2-eth2:t2-eth1
t1 lo:  t1-eth1:s1-eth2 t1-wdm2:t2-wdm2
t2 lo:  t2-eth1:s2-eth2 t2-wdm2:t1-wdm2
t1-monitor
t2-monitor
```

Node information:
```
mininet-optical> dump
<Host h1: h1-eth0:10.0.0.1 pid=3422>
<Host h2: h2-eth0:10.0.0.2 pid=3424>
<OVSBridge s1: lo:127.0.0.1,s1-eth1:None,s1-eth2:None pid=3429>
<OVSBridge s2: lo:127.0.0.1,s2-eth1:None,s2-eth2:None pid=3432>
<Terminal t1: lo:127.0.0.1,t1-eth1:None,t1-wdm2:None pid=3438>
<Terminal t2: lo:127.0.0.1,t2-eth1:None,t2-wdm2:None pid=3442>
<dataplane.Monitor object at 0x7efe3c561e20>
<dataplane.Monitor object at 0x7efe3c577370>
```

OSNR:
```
mininet-optical> osnr
<name: t1-monitor, component: t1, mode: in>:
<name: t2-monitor, component: t2, mode: in>:
```

Since no signals have been launched and no configuration has been set, the OSNR command doesn't display
anything.

We can try to ping the hosts, but this will not succeed:

```
mininet-optical> pingall
*** Ping: testing ping reachability
h1 -> X
h2 -> X
*** Results: 100% dropped (0/2 received)
```

All the Mininet-Optical commands can be found in the [`OpticalCLI` class][1].

Mininet's regular CLI commands are also supported.

### Setting up routes

To create the routes and activate the hosts, open another terminal window, and run the following
script:

    $ cd ~/mininet-optical/examples
    $ ./config-singlelink.sh

This script will configure the optial `Terminal`s and launch signals at their transceiver.
The result on the Mininet-Optical window should look like:

```
*** t1.turn_on <ch1:191.35THz> on port 2
*** t2 receiving <ch1:191.35THz> at port 2: Success! gOSNR: 22.708129 dB OSNR: 45.402202 dB
*** t2.turn_on <ch1:191.35THz> on port 2
*** t1 receiving <ch1:191.35THz> at port 2: Success! gOSNR: 22.708129 dB OSNR: 45.402202 dB
```
Now, you can run the `osnr` command again and see:

```
mininet-optical> osnr
<name: t1-monitor, component: t1, mode: in>:
<ch1:191.35THz> OSNR: 45.40 dB gOSNR: 22.71 dB
<name: t2-monitor, component: t2, mode: in>:
<ch1:191.35THz> OSNR: 45.40 dB gOSNR: 22.71 dB
```
The `ping` command should give you:

```
mininet-optical> pingall
*** Ping: testing ping reachability
h1 -> h2
h2 -> h1
*** Results: 0% dropped (2/2 received)
```

At this point, the topology is created and configured.

To reset the configuration of your devices in order to run a different controller or change rules, run:

    mininet-optical> reset

To exit the Mininet-Optical CLI, use the command:

    mininet-optical> exit

## Congratulations!

You have completed the Mininet-Optical walkthrough.

This example has shown a very simple link configuration with two
terminals. Check out the [`examples/` directory][2] for other
examples, including how to create and configure ROADMs and how to
emulate larger topologies using Mininet-Optical.


[1]: https://github.com/mininet-optical/mininet-optical/tree/master/mnoptical/ofcdemo/demolib.py#L35
[2]: https://github.com/mininet-optical/mininet-optical/tree/master/mnoptical/examples
