#!/usr/bin/python

"""
dataplane.py: Simple dataplane emulation for mininet-optical

We repurpose OvS to emulate optical line terminals and ROADMs,
and we use TCLink to emulate delay on optical fiber spans.

For simplicity, we assume that the links and connections are
full-duplex, and that transponders use thes ame tx and rx channels.

Provides the following Mininet classes:

Terminal:  A set of transceivers that can be connected to Ethernet
          downlink ports.

ROADM: A colorless, directionless ROADM.

SimpleROADM: A 2-degree ROADM with two add/drop ports

OpticalLink: a bidirectional optical link consisting of fiber
             spans and amplifiers.

"""

# Physical model
from link import Link as PhyLink, Span as FiberSpan, SpanTuple
from node import ( LineTerminal as PhyTerminal, Amplifier as PhyAmplifier,
                   Roadm as PhyROADM, Monitor as PhyMonitor,
                   SwitchRule as PhySwitchRule)

# Data plane
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSSwitch
from mininet.link import Link, TCIntf
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.clean import sh, Cleanup, cleanup
from mininet.examples.linuxrouter import LinuxRouter
from mininet.util import BaseString

from collections import namedtuple
from functools import partial
from itertools import chain
from operator import attrgetter
from sys import argv

# Unit conversions (probably we should use units.py)
km = 1.0
m = .001
dBm = 1.0
dB = 1.0


### Network Elements

class OpticalNet( Mininet ):
    "Add monitors to network"

    monitors = []

    def __iter__( self ):
        "return iterator over node names"
        for node in chain( self.hosts, self.switches, self.controllers,
                           self.monitors ):
            yield node.name

    def addLinkComponents( self, link ):
        for monitor in link.monitors:
            self.nameToNode[ monitor.name ] = monitor
            self.monitors.append( monitor )

    def addLink( self, *args, **kwargs ):
        "Extends Mininet.addLink() to add Link's amps and monitors to net"
        link = super( OpticalNet, self ).addLink( *args, **kwargs )
        if isinstance( link, OpticalLink ):
            self.addLinkComponents( link )
        return link

Mininet = OpticalNet


class Monitor( PhyMonitor ):
    "A hacked PhyMonitor that can stand in for a node"

    # XXX Hacked node compatibility, should probably fix
    waiting = False
    execed = True
    intfs = {}
    def __init__( self, *args, **kwargs ):
        super( Monitor, self ).__init__( *args, **kwargs )
        self.model = self
    def intfList( self ):
        return []
    def pexec( self, *args, **kwargs ):
        pass

    # SDN monitoring support

    def restMonitor( self ):
        "Return OSNR to REST agent"
        osnr = { signal.index:
                 dict(freq=signal.frequency, osnr=self.get_osnr( signal ),
                      gosnr=self.get_gosnr( signal))
                 for signal in sorted( self.amplifier.output_power,
                                      key=attrgetter( 'index' ) ) }
        return dict( osnr=osnr )


def PhySpan( length, amp=None ):
    "Return a usable span of length km with amplifer amp"
    result = SpanTuple( FiberSpan( length=length*km) , amp )
    return result


class SwitchBase( OVSSwitch ):
    "Base class for optical devices"

    def __init__( self, name, dpid=None, listenPort=None, inNamespace=False,
                  isSwitch=True, batch=False, **phyParams ):
        # No batch initialization for now since we add a flow in start()
        super( SwitchBase, self ).__init__(
            name, dpid=dpid, listenPort=listenPort, inNamespace=inNamespace,
            isSwitch=isSwitch, batch=False )

        self.model = self.modelClass( name, **phyParams )

    def dpctl( self, *args ):
        "Call dpctl and check for error"
        result = OVSSwitch.dpctl( self, *args )
        exitCode = int( self.cmd( 'echo $?' ) )
        if exitCode != 0:
            raise RuntimeError( 'dpctl returned %d: %s' %
                                ( exitCode, result ) )
        return result

    dpidBase = 0x1000

    def defaultDpid( self, dpid=None ):
        "Return a default DPID"
        if dpid is None:
            SwitchBase.dpidBase += 1
            dpid = '%x' % SwitchBase.dpidBase
        return super( OVSSwitch, self ).defaultDpid( dpid )

    @staticmethod
    def restPortsDict( node ):
        "Construct a ports dict for a node"
        return {port: intf.name for port, intf in node.intfs.items() }

    def restResetHandler( self, query ):
        "REST reset handler"
        self.reset()
        return 'OK'



class Terminal( SwitchBase ):
    """
    Simple terminal which is just a bank of transceivers
    and some ethernet ports that can connect to them.
    """

    # Physical model (PhyTerminal)
    model = None
    modelClass = PhyTerminal

    # transceiver -> channel
    txChannel = {}
    txPorts = {}

    def start( self, _controllers ):
        "Override to start without controller"
        super( SwitchBase, self ).start( controllers=[] )
        self.reset()

    def reset( self ):
        "Reset/clear routes"
        self.dpctl( 'del-flows' )
        # Drop IPv6 router solicitations
        self.dpctl( 'add-flow', 'ipv6,actions=drop')
        self.txChannels = {}
        # self.model.reset_signals()

    # Probably obsolete now that we have auto-propagation
    #def propagate( self ):
    #    "Propagate output signals"
    #    outport = self.model.ports_out[0]
    #     for txChannel in self.txChannel.items():
    #        transceiver = self.model.transceivers[ tx ]
    #        self.model.transmit(transceiver, outport, [channel])

    def configTx( self, txNum, channel=None, power=None ):
        """Configure transceiver txNum
           channels: [channel index...]
           power: power in dBm"""
        transceiver = self.model.transceivers[ txNum ]
        if channel is not None:
            self.txChannel[ txNum ] = channel
        if power is not None:
            transceiver.operation_power = db_to_abs(operation_power)

    def txnum( self, wdmPort ):
        "Return tx number for wdmPort number"
        # This is inefficient but could be cached
        txnum = 0
        for port in sorted( self.ports.values() ):
            intf = self.intfs[ port ]
            if isinstance(intf, OpticalIntf ):
                if port == wdmPort:
                    return txnum
                txnum += 1
        raise Exception( '%s could not find tx for port %d' %
                         ( self, wdmPort ) )

    def restConnectHandler( self, query ):
        "REST connect handler"
        ethPort = int( query.ethPort )
        wdmPort = int( query.wdmPort )
        channel = int( query.channel ) if hasattr( query, 'channel' ) else None
        # print("CONNECT", self, "eth", ethPort, "wdm", wdmPort, "channel", channel)
        self.connect( ethPort, wdmPort, channel )
        return 'OK'

    def connect(self, ethPort, wdmPort, channel=None, power=None ):
        """Connect an ethPort to transceiver tx on port wdmPort
           ethPort: ethernet port number
           wdmPort: WDM port number"""

        # Update physical model
        OUT = 100  # Offset for output port
        tx = self.txnum( wdmPort )
        transceiver = self.model.transceivers[ tx ]
        self.configTx( txNum=tx, channel=channel, power=power )
        channel = self.txChannel.get( tx )
        if channel is None:
            raise Exception( 'must set tx channel before connecting' )
        self.model.transmit( transceiver, wdmPort+OUT, [ channel ] )

        # Remove old flows for transponder
        oldEthPort, oldWdmPort = self.txPorts.get( tx, (None, None))
        for port in ethPort, wdmPort, oldEthPort, oldWdmPort:
            if port is not None:
                self.dpctl( 'del-flows', 'in_port=%d' % port )
                self.dpctl( 'del-flows', 'out_port=%d' % port )
        self.txPorts[ tx ] = ( ethPort, wdmPort )

        # Tag outbound packets and untag inbound packets

        outbound = ( 'in_port=%d,' % ethPort +
                     'actions=mod_vlan_vid=%d,' % channel +
                     'output:%d' % wdmPort )

        inbound = ( 'in_port=%d,' % wdmPort +
                    'dl_vlan=%d,' % channel +
                    'actions=strip_vlan,'
                    'output:%d' % ethPort )

        self.dpctl( 'add-flow', outbound )
        self.dpctl( 'add-flow', inbound )

    def dumpStatus( self ):
        "Print out some status information"
        print('***', self.name, 'transceiver status:' )
        print(self.model.transceiver_to_optical_signals)


class ROADM( SwitchBase ):
    """A simple ROADM emulation based on OVSSwitch

       Emulates a colorless, directionless ROADM.

       Currently uses VLAN field for channel/lambda index."""

    model = None
    modelClass = PhyROADM
    ruleIds = {}   # Cache of physical model rule IDs

    def start( self, _controllers ):
        "Override to start without controller"
        super().start( controllers=[] )
        self.phyReset()
        self.dpReset()

    # Physical model operations

    @staticmethod
    def ruleTuple( inport, outport, channels ):
        "Return hashable tuple for rule"
        return PhySwitchRule( inport, outport, tuple( sorted( channels ) ) )

    def phyReset( self ):
        "Reset physical model"
        self.ruleIds = {}
        self.nextRuleId = 1
        self.model.delete_switch_rules()

    def phyInstall( self, inport, outport, channels ):
        "Install switching rules into the physical model"
        OUT = 100  # Offset for model output port
        rule = self.ruleTuple( inport, outport, channels )
        if rule in self.ruleIds:
            return
        self.model.install_switch_rule(
            self.nextRuleId, inport, outport + OUT, channels )
        self.ruleIds[ rule ] = self.nextRuleId
        self.nextRuleId += 1

    def phyRemove( self, inport, outport, channels ):
        rule = ( inport, outport, tuple( sorted( channels ) ) )
        ruleId = self.ruleIds.get( rule )
        if ruleId:
            self.model.delete_switch_rule( ruleId )
            del self.ruleIds[ rule ]
        else:
            raise Exception( 'could not find rule %s' % str( rule ) )

    # Probably obsolete now that we have auto-propagation
    #def propagate( self ):
    #    "Propagate signals"
    #    self.model.propagate()

    def dumpStatus( self ):
        "Print out some stuff for debugging"
        self.model.print_switch_rules()

    def restRulesHandler( self, query ):
        "Handle REST rules request"
        return self.model.switch_table

    # Dataplane operations

    def dpReset( self ):
        "Reset/initialize dataplane"
        # For now, we just rewrite the whole flow table,
        # but we can optimize this later
        self.dpctl( 'del-flows' )
        # Drop IPv6 router soliciations
        self.dpctl( 'add-flow', 'ipv6,actions=drop')

    def dpFlow( self, inport, outport, channel, action='add-flow' ):
        "Return a switching rule for the dataplane"
        # Note: Dataplane currently switches on VLAN
        # We can change this in the future
        return ( ( 'priority=200,' if action == 'add-flow' else '') +
                 'in_port=%d,' % inport +
                 'dl_vlan=%d' % channel +
                 ( ( ',actions=output:%d' % outport )
                   if action == 'add-flow' else '') )

    def dpInstall( self, inport, outport, channels, cmd='add-flow' ):
        "Install a switching rule into the dataplane"
        for channel in channels:
            flow = self.dpFlow( inport, outport, channel, 'add-flow' )
            self.dpctl( cmd, flow )

    def dpRemove( self, inport, outport, channels, cmd='add-flow' ):
        "Remove a switching rule from the dataplane"
        dpInstall( self, inport, outport, channels, cmd='del-flows' )

    # Combined dataplane/phy emulation operations

    def reset( self ):
        "Reset dataplane and physical model"
        self.dpReset()
        self.phyReset()

    def install( self, inport, outport, channels, action='install' ):
        "Install rules into dataplane and physical model"
        if action == 'install':
            self.dpInstall( inport, outport, channels, cmd='add-flow' )
            self.phyInstall( inport, outport, channels )
        elif action == 'remove':
            self.dpInstall( inport, outport, channels  )
            self.phyRemove( inport, outport, channels )
        else:
            raise Exception( 'unknown action <%s>' % action )

    def restDisconnectHandler( self, query ):
        "REST remove handler"
        return restConnectHandler( query, action='remove' )

    def restConnectHandler( self, query ):
        "REST connect handler"
        port1 = int( query.port1 )
        port2 = int( query.port2 )
        channels = [int(channel) for channel in query.channels.split(',')]
        action = getattr( query, 'action', 'install' )
        self.connect( port1, port2, channels, action )
        return 'OK'

    def connect( self, port1, port2, channels, action='install' ):
        "Install bidirectional rule connecting port1 and port2"
        self.install( port1, port2, channels, action=action )
        self.install( port2, port1, channels, action=action )

    def disconnect( self, port1, port2, channels, action='remove' ):
        "Remove bidirectional rule connecting port1 and port2"
        self.connect( port1, port2, channels, action='remove' )


class SimpleROADM( ROADM ):
    """2-degree ROADM with simplified API.

       We assume a 2-degree ROADM with full-duplex
       links and connections. For simplicity, we assume
       the same channel is used in both directions.

       Local channels are bidirectionally added and
       dropped, while other channels are passed through.

       Port 1 is east transit
       Port 2 is west transit
       Port 3 is southeast add/drop
       Port 4 is southwest add/drop
    """

    def update( self, localChannels, passChannels=None):
        """Update flow table to add/drop localChannels
           and pass passChannels"""

        passChannels = passChannels or []

        # Uplink/transit ports
        east, west = 1, 2

        # Local add/drop ports for each uplink
        southeast, southwest = 3, 4

        self.reset()

        # Route local<->uplink for add/drop ports<->line ports
        for uplink, local in (east, southeast), (west, southwest):
            self.install( uplink, local, localChannels )
            self.install( local, uplink, localChannels )

        # Pass transit channels in both directions
        self.install( east, west, passChannels )
        self.install( west, east, passChannels )


class OpticalIntf( TCIntf ):
    "For now, an OpticalIntf is just a TCIntf"
    pass


class OpticalLink( Link ):
    """"An emulation of a (bidirectional) optical link.

        The dataplane emulation is naturally bidirectional (veth pairs.)

        For the physical model(s), we create two unidirectional links,
        which are the reverse of each other in terms
        of fiber spans and amplfiers."""

    # Two unidirectional link models
    phyLink1 = None
    phyLink2 = None

    def __init__( self, src, dst, port1=None, port2=None,
                  boost=None, boost1=None, boost2=None, spans=None,
                  monitors=None, **kwargs ):
        """node1, node2: nodes to connect
           port1, port2: node ports
           boost1, boost2: boost amp (name, {params}) if any
           spans: list of (length in km, (ampName, params) | None )
           monitors: list of (monName, ampName)"""
        # Default span: 1m of fiber, no amplifier
        spans = spans or [1*m]

        # FIXME: There should be a better way to do this.
        # Also, the phy model binds ports to links while the
        # dataplane model doesn't (allowing reconnection.)
        # This is a somewhat serious issue that will be hard to fix
        port1 = kwargs.get( 'params1', {}).get( 'port', port1 )
        port2 = kwargs.get( 'params2', {}).get( 'port', port2 )
        self.port1 = port1 if port1 is not None else node1.newPort()
        self.port2 = port2 if port2 is not None else node1.newPort()
        kwargs.update( port1=self.port1, port2=self.port2 )

        # Initialize dataplane
        kwargs.update( cls1=OpticalIntf, cls2=OpticalIntf )
        super( OpticalLink, self).__init__( src, dst, **kwargs )

        # Boost amplifiers if any
        prefix1, prefix2 = ('%s-%s-' % (src, dst)), ('%s-%s-' % (dst, src)),
        boost1 = boost1 or (boost and ( prefix1 + boost[0], boost[1] ) )
        boost2 = boost2 or (boost and ( prefix2 + boost[0], boost[1] ) )
        if boost1:
            name, params = boost1
            boost1 = PhyAmplifier( name, **params )
        if boost2:
            name, params = boost2
            boost2 = PhyAmplifier( name, **params )

        # Create symmetric spans and phy links in both directions
        spans = self.parseSpans( spans )
        spans1 = [ PhySpan( length, PhyAmplifier( prefix1 + name, **params )
                            if name else None )
                   for length, name, params in spans ]

        spans2 = [ PhySpan( length, PhyAmplifier( prefix2 + name, **params )
                            if name else None )
                   for length, name, params in reversed( spans ) ]

        # XXX Output ports have to start at this number for some reason?
        OUT = 100
        self.phyLink1 = PhyLink(
            src.model, dst.model, output_port_node1=self.port1+OUT,
            input_port_node2=self.port2, boost_amp=boost1, spans=spans1 )
        self.phyLink2 = PhyLink(
            dst.model, src.model, output_port_node1=self.port2+OUT,
            input_port_node2=self.port1, boost_amp=boost2, spans=spans2 )

        # Create monitors and store in self.monitors
        monitors = monitors or {}
        monitored = { prefix+ampName: prefix+monitorName
                      for monitorName, ampName in monitors
                      for prefix in (prefix1, prefix2) }
        self.monitors = []
        for boost in boost1, boost2:
            if boost and boost.name in monitored:
                monitor = Monitor( boost, link=link, amplifier=boost )
                self.monitors.append( monitor )
        for link, spans in ((self.phyLink1, spans1), (self.phyLink2, spans2)):
            for span, amplifier in spans:
                if amplifier and amplifier.name in monitored:
                    name = monitored[ amplifier.name ]
                    monitor = Monitor(
                        name, link=link, span=span, amplifier=amplifier )
                    self.monitors.append( monitor )

    @staticmethod
    def parseSpans( spans=None ):
        "Parse list of spans and amplifiers into (length, amp) tuples"
        spans = spans or []
        result = []
        while spans:
            length, ampName, params = spans.pop(0), None, None
            # Maybe there's a better way of doing this polymorphic api
            if spans and isinstance( spans[ 0 ], BaseString ):
                ampName = spans.pop( 0 )
            elif spans and isinstance( spans[ 0 ], tuple ):
                ampName, params = spans.pop( 0 )
            result.append( ( length, ampName, params ) )
        return result


    def intfName( self, node, n ):
        "Construct a canonical interface name node-wdmN for interface N"
        return node.name + '-wdm' + repr( n )


# XXX Possibly obsolete but may be useful at some point.
# TODO: We will need a control API for the amplifiers

class AmplifierPair(object):
    "A bidirectional PhyAmplifier pair."

    phyAmp1 = None
    phyAmp2 = None

    def __init__( self, name, *args, **kwargs ):
        params1, params2  = kwargs.pop( 'params1' ), kwargs.pop( 'params2' )
        params1 = params1 or kwargs.copy()
        params2 = params2 or kwargs.copy()
        self.phyAmp1 = PhyAmplifier( name + '.1', *args, **params1)
        self.phyAmp2 = PhyAmplifier( name + '.2', *args, **params2)


### Support functions

def cleanOptLinks():
    info( "*** Removing all links of the pattern wxYZ-optN\n" )
    links = sh( "ip link show | "
                "egrep -o '([-_.[:alnum:]]+-wdm[[:digit:]]+)'"
    ).splitlines()

    # Delete blocks of links
    n = 1000  # chunk size
    for i in range( 0, len( links ), n ):
        cmd = ';'.join( 'ip link del %s' % link
                        for link in links[ i : i + n ] )
        sh( '( %s ) 2> /dev/null' % cmd )


# Importing this file will add the cleanup callback
Cleanup.addCleanupCallback( cleanOptLinks )


def disableIPv6( net ):
    "Disable IPv6 to avoid annoying router solicitations"
    for n in net.values():
        n.pexec( 'sysctl -w net.ipv6.conf.all.disable_ipv6=1' )
        n.pexec( 'sysctl -w net.ipv6.conf.default.disable_ipv6=1' )


### Monitoring and debugging

def dumpNet( net ):
    "dump out network information"
    print("Optical devices:")
    for node in net.switches:
        if not hasattr( node, 'model' ):
            continue
        model = node.model
        print( model, end=' ')
        print( "in", model.ports_in, "out", model.ports_out )


def formatSignals( signalPowers ):
    return '\n'.join(
        '%s %.2f dBm' % ( channel, signalPowers[ channel ] )
        for channel in sorted( signalPowers ) )


def dumpLinkPower(link):
    "Print out power for all spans in a Link"
    for span, amp in link.spans:
        print(span, end='')
        if amp:
            print(amp, 'input', formatSignals(amp.input_power),
                  'output', formatSignals(amp.output_power) )


### Sanity test

class TwoTransceiverTopo( Topo ):
    """Two hosts/transceivers connected by a 2-way fiber span, which may
       consist of links and 2-way amplifiers"""

    def build( self, spans=[ 25*km, 'amp1', 50*km, 'amp2', 25*km] ):
        # Nodes
        h1, h2 = [ self.addHost( h ) for h in ( 'h1', 'h2' ) ]
        t1, t2 = [ self.addSwitch( o, cls=Terminal,
                                   transceivers=[ ( 't1', -2*dBm, 'C' ) ] )
                   for o in ('t1', 't2') ]

        # Packet links: port 1 = ethernet port
        for h, o in ((h1, t1), (h2, t2)):
            self.addLink( h, o, port1=1, port2=1)

        # Optical links: port 2 = line port
        self.addLink( t1, t2, cls=OpticalLink, port1=2, port2=2,
                      spans=spans )


def twoTransceiverTest():
    "Test two transponders connected over a link"
    info( '*** Testing simple two transceiver network \n' )
    topo = TwoTransceiverTopo()
    net = Mininet( topo )
    h1, h2, t1, t2 = net.get( 'h1', 'h2', 't1', 't2' )
    net.start()
    # Set up lightpaths
    t1.connect( ethPort=1, tx=0, wdmPort=2, channel=1 )
    t2.connect( ethPort=1, tx=0, wdmPort=2, channel=1 )
    # Print power
    link = net.links[-1]
    dumpLinkPower( link.phyLink1 )
    dumpLinkPower( link.phyLink2 )
    # CLI(net)
    net.pingAll()
    net.stop()


if __name__ == '__main__':

    # Standalone cleanup: ./dataplane.py -c
    if argv[ 1: ] == [ '-c' ]:
        cleanup()
        exit( 0 )

    ### Run sanity test(s) [note: must run as root for mininet]
    cleanup()
    print( '*** Running dataplane sanity test' )
    setLogLevel( 'info' )
    twoTransceiverTest()
    print( 'Done.' )
