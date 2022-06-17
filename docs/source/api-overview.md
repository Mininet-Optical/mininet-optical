### API Overview

This section provides an overview of the Python API and the
REST control API used in Mininet-Optical. We will discuss the
generation of a simple linear topology and its controller logic.

#### Python API

Mininet-Optical's Python API extends the API from regular (packet)
Mininet. If you are unfamiliar with Mininet's API, you may wish to
read the Introduction to Mininet at
[docs.mininet.org](http://docs.mininet.org).

#### Specifying a Topology

The Python API is used to define the network topology. On completion of
the following sets of commands, we will have a network that is ready
to be configured. We take the example of a simple topology that
looks like the following:

	h1 - t1 - (boost->) --25km-- (<-boost) - t2 - h2

Let's look at `examples/simplelink.py` to see how this is done.

Since Python follows an object-oriented programming approach, we need
to define a class named `SimpleLinkTopo` using the
statement. `SimpleLinkTopo` extends Mininet's `Topo` class.

	class SimpleLinkTopo(Topo):

It is important to remember that we are creating a topology
template class. Instantiating this class will create a
topology template which we will pass to the `Mininet()`
constructor which will use it to build an emulated network
with the desired topology.

We need to define a function for building the topology.

	def build(self):
	
In the `build` function, we need to first define the hosts (h1 and
h2). We use the `addHost()` for this purpose.

	# Packet network elements
	h1, h2 = self.addHost('h1'), self.addHost('h2')
	
Thereafter, we need to build the optical elements. The terminals (`t1`
and `t2`) provide the interface between the Ethernet hosts (`h1` and `h2`) and
the optical network. Further, we need optical transceivers placed in
the terminals for transmitting and receiving the optical
signals. Therefore, first we define the transceivers as `params` and
then we place the transceivers in the terminals.

	# Optical network elements
	params = {'transceivers': [('tx1', 0*dBm,'C')] }
	t1 = self.addSwitch('t1', cls=Terminal, **params)
	t2 = self.addSwitch('t2', cls=Terminal, **params)

Note that parameters are just data values that will be used later to
create the actual network emulator and simulator objects. In this
case, `params` specifies a `transceivers` parameter that consists
of a list of a single transceiver, `tx1`, with a default transmit
power of 0dBm (and on the `C` band though this parameter is optional
and currently ignored.) Note we are reusing the same set of parameters
for `t1` and `t2`, but this is OK since separate objects will be
created for them.

At this point, the network nodes are defined. All we need to do now is
to connect them together to form a working network. We connect
the hosts to the terminals using Ethernet links. We also connect the
terminals using a WDM link. This concludes the topology specification
in the `build()` method.

	# Ethernet links
	self.addLink(h1, t1, port2=1)
	self.addLink(h2, t2, port2=1)
	# WDM links
	self.addLink(t1, t2, cls=OpticalLink, port1=2, port2=2,
			boost=('boost', {'target_gain':17*dB}),
			spans=[25*km])

#### Starting Mininet-Optical

Defining the topology isn't enough to create the network itself.
In `examples/simplelink.py` this is handled in the `__main__`
section:

    if __name__ == '__main__':

        cleanup()  # Just in case!
        setLogLevel('info')

This cleans up any stale state and tells the logging system
to show informational messages as the emulation progresses.

Next, we instantiate our topology template and pass it as
the `topo` parameter to the `Mininet()` constructor.

    topo = SimpleLinkTopo()
    net = Mininet(topo=topo)

Since we're going to be using the REST control API, we start
a server for it.

    restServer = RestServer(net)

Next, we start up the emulated network as well as the REST server:

    net.start()
    restServer.start()

For informational purposes, we print out the docstring from the
header of `simplelink.py`

    info(__doc__)

In this example we either run a test function (if the script is
invoked with the `test` parameter) or otherwise start the Mininet-
Optical CLI:

    test(net) if 'test' in argv else CLI(net)

After the test is completed or the CLI exits, we halt the REST
server and shut down the emulated network:

    restServer.stop()
    net.stop()

#### REST SDN Control API

After learning about the Python API and designing the simple linear
network in the process, we will now look into the control API. Once
the following set of commands are executed, the hosts (`h1` and `h2`)
in our linear topology will be able to communicate.

Note: For this tutorial we will use Mininet-Optical's simple REST
control API. This is a simple control API created for Mininet-Optical
that can be used from the command line as well as from software.

We use the `curl` command for configuration of the network nodes. curl
is a command-line utility for transferring data from or to a server
using URL syntax.

First, we will set a base URL, which is the address of the local
machine. We need to identify this address as all the nodes defined are
built in the local host machine. The base URL is set as
`localhost:8080`:

	url="localhost:8080"; t1=$url; t2=$url; t3=$url; r1=$url
	
Next, we need to configure the terminals. Essectially, we set
the channels on which the terminal is set to operate. We also
`connect` the Ethernet and the WDM ports of the terminal as per our
routing requirements.

	Configure Terminals:
		curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=1"
		curl "$t2/connect?node=t1&ethPort=1&wdmPort=2&channel=1"

Note that the parameters are passed as URLs, where a command such as
`connect` is followed by `?` and a list of parameters of the form
`param=x` separated by `&` signs.

The next step is to turn on the terminals.

	Turning Terminals on:
		curl "$t1/turn_on?node=t1"
		curl "$t2/turn_on?node=t2"
	
(Not for this network, but in general:) If a ROADM is present in the
network topology, we need to first reset the ROADM and then install
the switching logic. The rest is done to ensure that any previous
switching rule is removed.

	Reset a ROADM:
		curl "$r1/reset?node=r1"
                
	Add a ROADM switching rule:
		curl "$r1/connect?node=r1&port1=1&port2=2&channels=1"

(Not for this network, but in general:) If desired, we set the
monitors. The monitors do not aid in the routing of the
network. However, they are useful for analysis and debugging
purposes, and they allow network controllers to monitor signals
in the network.

	Monitor a signal:
		curl "$t1/monitor?monitor=t1-monitor"
	
We hope this overview of the REST API has been useful.
Please check the `rest.py` module for the complete API.

