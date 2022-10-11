#!/usr/bin/env python

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
from mnoptical.link import Link as PhyLink, Span as FiberSpan, SpanTuple
from mnoptical.node import ( LineTerminal as PhyTerminal, Transceiver,
                   Amplifier as PhyAmplifier,
                   Node as PhyNode,
                   Roadm as PhyROADM, Monitor as PhyMonitor,
                   SwitchRule as PhySwitchRule,
                   db_to_abs )

# Data plane
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSSwitch
from mininet.link import Link, TCIntf
from mininet.log import setLogLevel, info, warn, debug
from mininet.cli import CLI
from mininet.clean import sh, Cleanup, cleanup
from mininet.util import BaseString

from itertools import chain
from numbers import Number
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

    def addMonitor( self, monitor ):
            self.nameToNode[ monitor.name ] = monitor
            self.monitors.append( monitor )

    def addLinkComponents( self, link ):
        for monitor in link.monitors:
            self.addMonitor( monitor )

    def addLink( self, *args, **kwargs ):
        link = super( OpticalNet, self ).addLink( *args, **kwargs )
        if isinstance( link, OpticalLink ):
            self.addLinkComponents( link )
        return link

    def addSwitch( self, *args, **kwargs ):
        switch = super( OpticalNet, self ).addSwitch( *args, **kwargs )
        monitor = getattr( switch, 'modelMonitor', None )
        if monitor:
           self.addMonitor( monitor )
        return switch

    # Demo/debugging: support for setgain command

    def restSetrippleHandler( self, query ):
        "Demo/debugging: Support for REST setgain call"
        amp_name = query.amp_name
        ripple = query.ripple
        self.set_ripple(amp_name, ripple)
        return 'OK'

    def set_ripple(self, amp_name, ripple):
        srcdst = amp_name.split('-')
        if len(srcdst) < 2:
            print(srcdst)
            print("couldn't find src-dst in %s" % amp_name)
            return
        src, dst = srcdst[0:2]
        links = self.linksBetween(*self.get(src, dst))
        # Find amp
        l, amp = None, None
        for link in links:
            if not isinstance(link, OpticalLink):
                continue
            for phyLink in link.phyLink1, link.phyLink2:
                if phyLink.boost_amp.name == amp_name:
                    l, amp = phyLink, phyLink.boost_amp
                    break
                for span, spanamp in phyLink.spans:
                    if spanamp and spanamp.name == amp_name:
                        l, amp = phyLink, spanamp
                        break
        if not amp:
            return '%s not found' % amp_name
        # Set ripple function (wavelength dependent gain)
        amp.set_ripple_function(ripple)

    def restSetgainHandler( self, query ):
        "Demo/debugging: Support for REST setgain call"
        ampName = query.amplifier
        gain = query.gain
        print( "**************", ampName, gain )
        return self.setgainCmd( ampName, float( gain ) )

    def setgainCmd( self, ampName, gain ):
        "Demo/debugging: Support for demo CLI setgain command"
        # FIXME: This is ugly and also doesn't seem to work.
        # The amplifier gain is updated but the signals
        # don't seem to be updating properly.
        # Translated from mnoptical.network.mock_amp_gain_adjust()
        srcdst = ampName.split( '-' )
        if len( srcdst ) < 2:
            return "couldn't find src-dst in %s" % ampName
        src, dst = srcdst[0:2]
        links = self.linksBetween( *self.get(src, dst ) )
        # Find amp
        l, amp = None, None
        for link in links:
            if not isinstance( link, OpticalLink ):
                continue
            for phyLink in link.phyLink1, link.phyLink2:
                if phyLink.boost_amp.name == ampName:
                    l, amp = phyLink, phyLink.boost_amp
                    break
                for span, spanamp in phyLink.spans:
                    if spanamp and spanamp.name == ampName:
                        l, amp = phyLink, spanamp
                        break
        if not amp:
            return '%s not found' % ampName
        oldAmp = str( amp )
        src_roadm, dst_roadm = phyLink.node1, phyLink.node2
        # Set gain
        amp.mock_amp_gain_adjust( float( gain ) )
        newAmp = str( amp )
        # Reset the signal-propagation structures along the link
        l.reset_propagation_struct()
        op = l.output_port_node1
        # Pass only the signals corresponding to the output port
        pass_through_signals = src_roadm.port_to_optical_signal_power_out[op].copy()
        ase = src_roadm.port_to_optical_signal_ase_noise_out.get(op).copy()
        nli = src_roadm.port_to_optical_signal_nli_noise_out.get(op).copy()
        if ase is None or nli is None:
            print( 'WARNING: noise values not found for port', op,
                   'signal values will probably be incorrect!' )
        print("*** Recomputing propagation out of %s" % src_roadm.name)
        l.propagate(pass_through_signals, ase, nli)
        result = oldAmp + '->' + newAmp
        print("*** setgain end...", result)
        return result

Mininet = OpticalNet


class Monitor:
    "A hacked PhyMonitor that can stand in for a node"

    # XXX Hacked node compatibility, should probably fix
    waiting = False
    execed = True
    intfs = {}
    def __init__( self, name, monitor):
        self.name = name
        self.model = monitor
    def intfList( self ):
        return []
    def intfNames( self ):
        return []
    def pexec( self, *args, **kwargs ):
        pass

    # SDN monitoring support

    def restMonitor( self, query ):
        "Return OSNR to REST agent"
        monitor = self.model
        port, mode = None, None
        if query.port:
            port = int(query.port)
        if query.mode:
            mode = str(query.mode)
            monitor.modify_mode(mode=mode)
        signals = monitor.get_optical_signals(port)
        signals = sorted(signals, key=lambda s:s.index)
        osnr = { signal.index:
                 dict(freq=signal.frequency, osnr=monitor.get_osnr( signal ),
                      gosnr=monitor.get_gosnr( signal ),
                      power=monitor.get_power( signal ),
                      ase=monitor.get_ase_noise( signal ),
                      nli=monitor.get_nli_noise( signal ))
                 for signal in signals }
        return dict( osnr=osnr )

    def __str__( self ):
        return str( self.model)


def PhySpan( length, amp=None ):
    "Return a usable span of length km with amplifer amp"
    result = SpanTuple( FiberSpan( length=length*km) , amp )
    return result


class SwitchBase( OVSSwitch ):
    "Base class for optical devices"

    modelClass = PhyNode

    def __init__( self, name, dpid=None, listenPort=None,
                  inNamespace=False, isSwitch=True, batch=False,
                  **phyParams ):
        # No batch initialization for now since we add a flow in start()
        super( SwitchBase, self ).__init__(
            name, dpid=dpid, listenPort=listenPort,
            inNamespace=inNamespace,
            isSwitch=isSwitch, batch=False )

        self.model = self.modelClass( name, **phyParams )

        monitor = getattr( self.model, 'monitor', None )
        if monitor:
            self.modelMonitor = Monitor( monitor.name, monitor )

    def cmd( self, *args, **kwargs ):
        # simplified version that calls pexec
        cmd = ' '.join( str(arg) for arg in args )
        out, err, code = self.pexec( cmd, shell=True )
        if code != 0 and not cmd.startswith( 'ip link del' ):
            raise Exception(
                '%s returned %d: %s' % ( args, code, out+err ) )
        return out

    dpidBase = 0x1000

    def defaultDpid( self, dpid=None ):
        "Return a default DPID"
        if dpid is None:
            SwitchBase.dpidBase += 1
            dpid = '%x' % SwitchBase.dpidBase
        return super( SwitchBase, self ).defaultDpid( dpid )

    @staticmethod
    def restPortsDict( node ):
        "Construct a ports dict for a node"
        return {port: intf.name for port, intf in node.intfs.items() }

    def restResetHandler( self, query ):
        "REST reset handler"
        self.reset()
        return 'OK'

    def reset( self ):
        "Reset function - override this!"
        raise NotImplementedError( '%s needs to implement reset()' )


class Terminal( SwitchBase ):
    """
    Simple terminal which is just a bank of transceivers
    and some ethernet ports that can connect to them.
    """

    # Physical model (PhyTerminal)
    model = None
    modelClass = PhyTerminal

    blockCookie = 0xbadfeed

    @staticmethod
    def makeTransceiver( txid, args ):
        "Helper constructor for node.Transceiver"
        if isinstance( args, dict ):
            return Transceiver( txid, **args )
        if isinstance( args, Transceiver ):
            # enable passing Transceiver as param
            return args
        # Remove obsolete 'C' band parameter if any
        if len( args ) > 2 and args[ 2 ] == 'C':
            args = args[ :2 ] + args[ 3: ]
        return Transceiver( txid, *args )

    def __init__( self, *args, transceivers=None, **kwargs ):
        # Note that Topo() objects store parameters that are
        # passed to the appropriate constructor functions
        if not transceivers:
            raise ValueError( "Terminal: missing transceivers parameter list" )
        transceivers = [ self.makeTransceiver( i, args ) for
                         i, args in enumerate( transceivers,  ) ]
        super().__init__( *args, transceivers=transceivers, **kwargs )
        self.model.receiver_callback = self.receiverCallback

    def start( self, _controllers ):
        "Override to start without controller"
        super( Terminal, self ).start( controllers=[] )
        self.reset()

    def reset( self ):
        "Reset/clear routes"
        self.dpctl( 'del-flows' )
        # Drop IPv6 router solicitations
        self.dpctl( 'add-flow', 'ipv6,actions=drop')
        self.txChannel = {}
        self.failedChannels = set()
        self.model.reset()

    def configTx( self, txNum, channel=None, power=None ):
        """Configure transceiver txNum
           channels: [channel index...]
           power: power in dBm"""
        transceiver = self.model.transceivers[ txNum ]
        if channel is not None:
            self.txChannel[ txNum ] = channel
        if power is not None:
            transceiver.operation_power = db_to_abs(power)

    def txnum( self, wdmPort ):
        "Return a tx number for wdmPort number"
        # This is inefficient but could be cached
        txnum = 0
        isoutput = self.intfs[wdmPort].isOutput()
        # Return our index in array of WDM ports of our type
        # So output 1 gets tx1, input 4 gets tx4, etc..
        for port in sorted( self.ports.values() ):
            intf = self.intfs[ port ]
            if hasattr( intf, 'isOutput') and intf.isOutput() == isoutput:
                if port == wdmPort:
                    return txnum
                txnum += 1
        raise Exception( '%s could not find tx for port %d' %
                         ( self, wdmPort ) )

    def restTurnonHandler( self ):
        self.turn_on()
        return 'OK'

    def turn_on( self ):
        self.model.turn_on()

    def restConnectHandler( self, query ):
        "REST connect handler"
        ethPort = int( query.ethPort )
        wdmPort = int( query.wdmPort )
        channel, power, wdmInPort = None, None, None
        if query.wdmInPort:
            wdmInPort = int( query.wdmInPort )
        if query.channel:
            channel = int( query.channel )
        if query.power:
            power = float( query.power )
        self.connect( ethPort, wdmPort,
                      channel=channel, power=power,
                      wdmInPort=wdmInPort)
        return 'OK'

    def connect( self, ethPort, wdmPort, channel=None, power=None,
                wdmInPort=None ):
        """Connect an ethPort to transceiver tx on port wdmPort
           ethPort: ethernet port number
           wdmPort: WDM port number"""
        # Update physical model
        tx = self.txnum( wdmPort )
        transceiver = self.model.transceivers[ tx ]
        self.configTx( txNum=tx, channel=channel, power=power )
        if wdmInPort is None:
            wdmInPort = wdmPort
        wdmInputIntf = self.intfs[ wdmInPort ]
        wdmIntf = self.intfs[ wdmPort ]
        if wdmIntf.isOutput():
            # print(self, 'uplink', 'tx', transceiver.id, 'ch', channel, 'port', wdmPort )
            self.model.assoc_tx_to_channel(
                transceiver, channel, out_port=wdmPort )
        if wdmInputIntf.isInput():
            # print(self, 'downlink', 'tx', transceiver.id, 'ch', channel, 'port', wdmInPort )
            self.model.assoc_rx_to_channel( transceiver, channel, wdmInPort )

        # Remove old flows if any
        for port in wdmInPort, wdmPort:
            self.dpctl( 'del-flows', 'in_port=%d' % port )
            self.dpctl( 'del-flows', 'out_port=%d' % port )

        # Tag outbound packets and/or untag inbound packets

        outbound = ( 'priority=100,' +
                     'in_port=%d,' % ethPort +
                     'actions=mod_vlan_vid=%d,' % channel +
                     'output:%d' % wdmPort )

        inbound = ( 'priority=100,' +
                    'in_port=%d,' % wdmInPort +
                    'dl_vlan=%d,' % channel +
                    'actions=strip_vlan,'
                    'output:%d' % ethPort )

        if wdmIntf.isOutput():
            self.dpctl( 'add-flow', outbound )
        if wdmInputIntf.isInput():
            self.dpctl( 'add-flow', inbound )

    def receiverCallback( self, inport, signalInfoDict ):
        "Callback from PHY when signal is received"
        for signal, info in signalInfoDict.items():
            if not info[ 'success' ]:
                self.block( inport, signal.index )
            else:
                self.unblock( inport, signal.index )

    def block( self, inport, channel ):
        "Block channel at inport"
        if ( channel, inport ) in self.failedChannels:
            return
        self.failedChannels.add( ( channel, inport ) )
        print("***", self, "blocking port", inport, "channel", channel)
        blockInbound = ( 'priority=200,' +
                         'in_port=%d,' % inport +
                         'dl_vlan=%d,' % channel +
                         'cookie=%d,' % self.blockCookie +
                         'actions=drop' )
        self.dpctl( 'add-flow', blockInbound )

    def unblock( self, inport, channel ):
        "Unblock signal at inport"
        if ( channel, inport ) not in self.failedChannels:
            return
        print("***", self, "unblocking port", inport, "channel", channel)
        self.failedChannels.remove( ( channel, inport ) )
        # No priority or actions in delete
        blockInbound  = ( 'in_port=%d,' % inport +
                          'dl_vlan=%d,' % channel +
                          'cookie=%d/-1' % self.blockCookie )
        self.dpctl( 'del-flows', blockInbound )


class ROADM( SwitchBase ):
    """A simple ROADM emulation based on OVSSwitch

       Emulates a colorless, directionless ROADM.

       Currently uses VLAN field for channel/lambda index."""

    model = None
    modelClass = PhyROADM

    def __init__( self, name, **kwargs ):
        kwargs = kwargs.copy()
        super().__init__( name, **kwargs )

    def start( self, _controllers ):
        "Override to start without controller"
        super().start( controllers=[] )
        self.phyReset()
        self.dpReset()

    # Physical model operations

    @staticmethod
    def ruleTuple( inport, outport, channels ):
        "Return hashable tuple for rule"
        return PhySwitchRule(
            inport, outport, tuple( sorted( channels ) ) )

    def phyReset( self ):
        "Reset physical model"
        self.model.reset()

    def phyInstall( self, inport, outport, channels ):
        "Install switching rules into the physical model"
        self.model.install_switch_rule( inport, outport, channels )

    def phyRemove( self, inport, outport, channels ):
        for channel in channels:
            self.model.delete_switch_rule( inport, channel, switch=True )

    def restRulesHandler( self, query ):
        "Handle REST rules request"
        return [ dict( inport=inport, channel=channel, outport=outport )
                 for match, outport in self.model.switch_table
                 for inport, channel in match ]

    def restCleanmeHandler(self, query):
        "Handle REST clean request - same as reset for now"
        self.reset()
        return 'OK'

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
            debug('install/uninstall', inport, outport, channel, cmd)
            flow = self.dpFlow( inport, outport, channel, cmd )
            self.dpctl( cmd, flow )

    def dpRemove( self, inport, outport, channels ):
        "Remove a switching rule from the dataplane"
        #print('remove', inport, outport, channels)
        self.dpInstall( inport, outport, channels, cmd='del-flows' )

    # Combined dataplane/phy emulation operations

    def reset( self ):
        "Reset dataplane and physical model"
        self.dpReset()
        self.phyReset()

    def install( self, inport, outport, channels, action='install' ):
        "Install rules into dataplane and physical model"
        if action == 'install':
            self.dpInstall( inport, outport, channels )
            self.phyInstall( inport, outport, channels )
        elif action == 'remove':
            self.dpRemove( inport, outport, channels  )
            self.phyRemove( inport, outport, channels )
        else:
            raise Exception( 'unknown action <%s>' % action )

    # Here for symmetry, but not actually used by REST API
    def remove( self, inport, outport, channels ):
        "Remove rules from dataplane and physical model"
        self.install( inport, outport, channels, action='remove' )

    def restConnectHandler( self, query, action='install' ):
        "REST connect handler"
        port1 = int( query.port1 )
        port2 = int( query.port2 )
        channels = [int(channel)
                    for channel in query.channels.split(',')]
        action = query.get( 'action', action )
        self.connect( port1, port2, channels, action )
        return 'OK'

    def connect( self, port1, port2, channels, action='install' ):
        """Install rule connecting port1 -> port2.
           If interfaces are bidirectional, connect port2<->port1
           action: 'install' | 'remove' to install or remove rule"""
        intf1, intf2 = self.intfs[ port1 ], self.intfs[ port2 ]
        assert intf1.isInput() and intf2.isOutput()
        self.install( port1, port2, channels, action=action )
        # Install reverse rule if interfaces are bidirectional
        if intf1.isOutput() and intf2.isInput():
            self.install( port2, port1, channels, action=action )


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
    "A bidirectional Optical Interface"
    def isInput( self ):
        "Is this interface a WDM input?"
        return True
    def isOutput( self ):
        "Is this interface a WDM output?"
        return True


class OpticalIn( OpticalIntf ):
    "A unidirectional optical input interface"
    def isInput( self ):
        "Is this interface a WDM input?"
        return True
    def isOutput( self ):
        "Is this interface a WDM output?"
        return False


class OpticalOut( OpticalIntf ):
    "A unidirectional  optical output interface"
    def isInput( self ):
        "Is this interface a WDM input?"
        return False
    def isOutput( self ):
        "Is this interface a WDM output?"
        return True


class OpticalLink( Link ):
    """"An emulation of an optical link, bidirectional by default but
        optionally unidirectional.

        The dataplane emulation is naturally bidirectional (veth pairs.)

        By default, the Optical link is also a bidirectional fiber pair
        in both directions.

        For the physical model(s), we create two unidirectional links,
        which are the reverse of each other in terms
        of fiber spans and amplfiers."""

    # Two unidirectional link models
    phyLink1 = None
    phyLink2 = None

    def __init__( self, src, dst, port1=None, port2=None,
                  boost=None, boost1=None, boost2=None, spans=None,
                  bidirectional=True, **kwargs ):
        """node1, node2: nodes to connect
           port1, port2: node ports
           boost1, boost2: boost amp (name, {params}|[args]) if any
           spans: list of (length in km, (ampName, {params}|[args]) | None )
           NOTE - a prefix of 'src-dst-' will be added to node
           names, resulting in names like r1-r2-boost, r1-r2-amp1, etc.
           Note also that as described above, amplifier parameters
           may be either a dict or a list, to allow things like
           spans = [25*km, ('amp1', 5*dB), 25*km,  ... ] as well as
           boost = ('boost', {'target_gain': 17*dB, ...})
           """

        # Default span: 1m of fiber, no amplifier
        spans = spans or [1*m]

        # FIXME: There should be a better way to do this.
        # Also, the phy model binds ports to links while the
        # dataplane model doesn't (allowing reconnection.)
        # This is a somewhat serious issue that will be hard to fix
        port1 = kwargs.get( 'params1', {}).get( 'port', port1 )
        port2 = kwargs.get( 'params2', {}).get( 'port', port2 )
        self.port1 = port1 if port1 is not None else src.newPort()
        self.port2 = port2 if port2 is not None else dst.newPort()
        assert self.port1 >= 0 and self.port2 >= 0, (
            "OpticalLink: newPort() returned negative port number"
        )
        kwargs.update( port1=self.port1, port2=self.port2 )

        # Initialize dataplane
        if bidirectional:
            kwargs.update( cls1=OpticalIntf, cls2=OpticalIntf )
        else:
            kwargs.update( cls1=OpticalOut, cls2=OpticalIn )
        super( OpticalLink, self).__init__( src, dst, **kwargs )

        assert isinstance(self.intf1, OpticalIntf)
        assert isinstance(self.intf2, OpticalIntf)

        def component( prefix, cls=None, args=None, params=None):
            "Helper function to create segment components"
            if not cls: return []
            args, params = args or [], params or {}
            if prefix and not getattr(cls, 'anonymous', False):
                # Non-anonymous class gets its name parameter adjusted
                if params:
                    params = params.copy()
                try:
                    name = params.pop('name', None)
                    name, args = args[0], args[1:]
                    args: args = (prefix+name,) + tuple(args[1:])
                except:
                    raise Exception(f'name required for component of type {cls}')
            return cls( *args, **params )

        # Boost amplifiers if any
        # Note amp params can be a dict or a positional list, to allow
        # ('boost1', 3*dB) or ('boost1', {'target_gain': 3*dB})
        prefix1 = '%s-%s-' % (src, dst)
        prefix2 = '%s-%s-' % (dst, src)
        boost1 = boost1 or boost
        boost2 = boost2 or boost
        boost1 = boost1 and component(
            prefix1, *self._parseArgs( boost1, PhyAmplifier ) )
        boost2 = boost2 and component(
            prefix2, *self._parseArgs( boost2, PhyAmplifier ) )

        # Create spans and phy links in both directions
        # FIXME: We probably want to rethink this so that it is
        # actually symmetric in terms of fiber lengths! We could
        # do so by using a bidirectional amp pair with eastbound
        # and westbound target gain (!) It would make things more
        # realistic but harder to use.
        spans = self._parseSpans( spans )
        spans1 = [ SpanTuple( component('', *span), component(prefix1, *amp) )
                   for span, amp in spans ]
        if bidirectional:
            spans2 = [ SpanTuple( component('', *span),
                                  component(prefix2, *amp) )
                   for span, amp in spans ]
        self.phyLink1 = PhyLink(
            src.model, dst.model, src_out_port=self.port1,
            dst_in_port=self.port2, boost_amp=boost1, spans=spans1 )
        if bidirectional:
            self.phyLink2 = PhyLink(
                dst.model, src.model, src_out_port=self.port2,
                dst_in_port=self.port1, boost_amp=boost2, spans=spans2 )

        # Create monitors and store in self.monitors
        monitors, phyLinks = [], [ self.phyLink1 ]
        if bidirectional:
            phyLinks.append( self.phyLink2 )
        for link in phyLinks:
            if link.boost_amp and hasattr( link.boost_amp, 'monitor' ):
                monitors.append( link.boost_amp.monitor )
            monitors.extend( amp.monitor for fiber, amp in link.spans
                         if amp and hasattr( amp, 'monitor' ) )
        self.monitors = [ Monitor( monitor.name, monitor )
                          for monitor in monitors ]


    def _parseArgs( self, args, cls=None ):
        "Parse (cls, *args, [params]) tuples"
        if not args: return []
        if not cls:
            cls, args, params = args[0], args[1:], {}
        if args and isinstance(args[-1], dict):
            args, params = args[:-1], args[-1]
        else:
            params = {}
        return cls, args, params

    def _parseSpans( self, spans=None ):
        "Parse list of spans and amplifiers into (span, amp) tuples"
        # For convenience, we support a variety of parameter formats
        # span/amp format (cls, *args, [params])
        # shortcuts: Number -> (Span, int) ; str -> (Amplifier, str)
        spans, result = (list(spans) or []), []
        while spans:
            if isinstance( spans[0], ( Number, tuple ) ):
                # Length or custom span tuple
                if isinstance( spans[0], Number):
                    span, amp  = (FiberSpan, dict(length=spans.pop(0))), []
                else:
                    span, amp = spans.pop(0), []
                # Optional amplifier tuple
                if spans and isinstance( spans[0], tuple ):
                    # No class specified -> PhyAmplifier
                    if isinstance( spans[0][0], BaseString ):
                        amp = (PhyAmplifier,) + spans.pop(0)
                    elif issubclass(spans[0][0], PhyAmplifier):
                        amp = spans.pop(0)
            else:
                raise Exception(
                    f'{spans[0]}: Expected fiber length or tuple' )
            result.append( (self._parseArgs(span), self._parseArgs(amp) ) )
        return result

    def intfName( self, node, n ):
        "Construct a canonical interface name node-wdmN for interface N"
        return node.name + '-wdm' + repr( n )


def UnidirectionalOpticalLink( *args, **kwargs ):
    "Unidirectional OpticalLink constructor"
    kwargs.update( bidirectional=False )
    return OpticalLink( *args, **kwargs )

UniLink = UnidirectionalOpticalLink


# XXX Possibly obsolete but may be useful at some point.
# TODO: We will need a control API for the amplifiers

class AmplifierPair(object):
    "A bidirectional PhyAmplifier pair."

    phyAmp1 = None
    phyAmp2 = None

    def __init__( self, name, *args, **kwargs ):
        params1 = kwargs.pop( 'params1' )
        param2s = kwargs.pop( 'params2' )
        params1 = params1 or kwargs.copy()
        params2 = params2 or kwargs.copy()
        self.phyAmp1 = PhyAmplifier( name + '.1', *args, **params1)
        self.phyAmp2 = PhyAmplifier( name + '.2', *args, **params2)


# Comb Source with simulated (only) optical signals

class CombSource(ROADM):
    """Comb Source with simulated optical signals.

       The CombSource component emulates a comb source in COSMOS or
       other hardware testbeds. It is a dataplane component (the MUX
       half of a ROADM) but it only generates and transmits simulated
       signals. It is convenient for emulating a hardware comb source
       or for generating opaque background traffic in the simulated
       physical plane."""

    # Default MUX port numbers
    ADD = 4100
    LINEOUT = 4201

    def __init__(self, name, *args, power={1: 0*dBm}, **kwargs):
        """power: in form of dict {ch: power} where
           ch: channels to transmit
           power: tx power"""
           
        self.power = power
        super().__init__(name, *args, **kwargs)
        self.addTerminal()

    def addTerminal(self):
        "Add our simulated LineTerminal"
        self.lt = lt = PhyTerminal(self.name + '-lt')
        mux = self.model
        if isinstance(self.power, dict):
            for i, (ch, power) in enumerate(self.power.items(), start=1):
                tx = Transceiver(i, f'tx{ch}', power)
                lt.add_transceiver(tx)
                PhyLink(lt, mux, i, self.ADD+i, spans=[PhySpan(1*m)])
        else:
            raise Exception(
                "Expected dict of type {channel: power}")

    def restTurnonHandler(self):
        "Handle REST call: /turn_on?node=name"
        self.turn_on()

    def turn_on(self):
        "Configure components and turn on signals"
        lt, mux = self.lt, self.model
        # Configure transceivers
        for i, (channel, power) in enumerate(self.power.items(), start=1):
            outport = i
            tx = lt.transceivers[i-1]
            lt.assoc_tx_to_channel(tx, channel, outport)
            mux.install_switch_rule(self.ADD+i, self.LINEOUT, [channel])
        # Start transmission
        self.lt.turn_on()


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
    return str(signalPowers)
    return '\n'.join(
        'channel %s power %s' % ( channel, signalPowers[ channel ] )
        for channel in sorted( signalPowers ) )


def dumpLinkPower( link ):
    "Print out power for all spans in a Link"
    print("*********************** LINK POWER")
    for span, amp in link.spans:
        print( span, end='' )
        if amp:
            print(amp,
                  'input', formatSignals(amp.port_to_optical_signal_in),
                  'output',
                  formatSignals(amp.port_to_optical_signal_out) )


### Sanity test

class TwoTransceiverTopo( Topo ):
    """Two hosts/transceivers connected by a 2-way fiber span, which may
       consist of links and 2-way amplifiers"""

    def build( self, spans=[ 25*km, 'amp1', 50*km, 'amp2', 25*km] ):
        # Nodes
        h1, h2 = [ self.addHost( h ) for h in ( 'h1', 'h2' ) ]
        t1, t2 = [ self.addSwitch( o, cls=Terminal,
                                   transceivers=[
                                       ( 't1', -2*dBm, 'C' ) ] )
                   for o in ('t1', 't2') ]

        # Packet links: port 1 = ethernet port
        for h, o in ((h1, t1), (h2, t2)):
            self.addLink( h, o, port1=1, port2=1)

        # Optical links: port 2 = line port
        self.addLink( t1, t2, cls=OpticalLink, port1=2, port2=2,
                      spans=spans )

def twoTransceiverTest( cli=False):
    "Test two transponders connected over a link"
    info( '*** Testing simple two transceiver network \n' )
    topo = TwoTransceiverTopo()
    net = Mininet( topo )
    h1, h2, t1, t2 = net.get( 'h1', 'h2', 't1', 't2' )
    net.start()
    t1.connect(ethPort=1, wdmPort=2, channel=1)
    t2.connect(ethPort=1, wdmPort=2, channel=1)
    t1.turn_on()
    if cli:
        CLI(net)
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
