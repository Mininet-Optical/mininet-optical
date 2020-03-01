#!/usr/bin/python

"""

fakecontroller.py: script to test REST API

This is not intended to be a 'real' controller -
it is an extremely simple set of proxy objects
that make it easy to exercise the prototype
SDN control REST API via python.

The real controller will be ONOS, and it may use
GNMI or Netconf rather than REST.

"""

import requests
# just in case we ever need python 2
from subprocess import check_call, CalledProcessError


### Proxy Objects

class Proxy( object ):
    "Base proxy class"

    def __repr__( self ):
        return self.name


ListenPortBase = 6653

class OFSwitchProxy( Proxy ):
    "Local proxy for OpenFlow switch configuration using ovs-ofctl"

    listenPort = ListenPortBase

    def __init__( self, name, ip='127.0.0.1', port=None):
        self.name = name
        self.ip = ip
        if port is None:
            OFSwitchProxy.listenPort += 1
            port = OFSwitchProxy.listenPort
        self.port = port
        self.remote = 'tcp:%s:%d' % (ip, port)

    def dpctl( self, cmd, params='', verbose=False):
        "Invoke ovs-ofctl to program remote switch"
        if verbose:
            print( self, cmd, params )
        params = params.split()
        args = [ 'ovs-ofctl', cmd, self.remote ] + params
        try:
            check_call( args )
        except CalledProcessError as exc:
            print( '%s %s %s returned %d' % (
                self, cmd, params, exc.returncode ) )


class RESTProxy( Proxy ):
    "Proxy for REST API objects/calls"

    def __init__( self, name=None, baseURL='http://localhost:8080/'):
        self.name = name
        self.baseURL = baseURL

    def get( self, path, params=None ):
        "Make a REST request"
        # print(path, params)
        result = requests.get( self.baseURL + path, params=(params or {}) )
        # print(result.url)
        return result


class NodeProxy( RESTProxy ):
    "Base class for switching node proxies"

    def ports( self ):
        "Fetch node's switching rules if any"
        r = self.get( 'ports', params=dict(node=self.name) )
        return r.json()


class SwitchProxy( NodeProxy ):
    "Base class for switching node proxies"

    def rules( self ):
        "Fetch node's switching rules if any"
        r = self.get( 'rules', params=dict(node=self.name) )
        return r.json()


class TerminalProxy( SwitchProxy ):
    "Local proxy for Terminal/transceiver configuration via REST"

    def connect( self, ethPort, wdmPort, channel=None, power=None ):
        "Configure terminal/transceiver"
        params = dict( node=self.name, ethPort=ethPort, wdmPort=wdmPort,
                       channel=channel, power=power)
        print('connect', params)
        r = self.get( 'connect', params=params )
        print( r )


class ROADMProxy( SwitchProxy ):
    "Local proxy for ROADM configuration via REST"

    def connect( self, port1, port2, channels ):
        "Configure ROADM"
        channels = ','.join( str(channel) for channel in channels)
        params = dict(
            node=self.name, port1=port1, port2=port2, channels=channels )
        print('connect', params)
        r = self.get( 'connect', params=params)
        print( r )



### Configuration Retrieval


def fetchNodes( net ):
    "Fetch node list using REST"
    print( '*** Fetching nodes' )
    r = net.get( 'nodes' )
    json = r.json()
    print( json )
    return json[ 'nodes' ]


def fetchLinks( net ):
    print( '*** Fetching all links' )
    l = net.get( 'links' )
    print( l.json() )
    print( '*** Fetching ROADM-ROADM links' )
    r = net.get( 'links/roadms' )
    print( r.json() )
    print( '*** Fetching Terminal-ROADM links' )
    t = net.get( 'links/terminals' )
    print( t.json() )
    return l, r, t


def fetchRules( roadms ):
    "Fetch ROADM rules using REST"
    print( '*** Fetching ROADM rules' )
    for roadm in roadms:
        print( '***', node, 'rules:')
        print( r.rules() )


def fetchPorts( net, nodes ):
    "Fetch ports for all nodes"
    print( '*** Fetching ports for all nodes' )
    for node in nodes:
        result = net.get( 'ports',  dict( node=node ) )
        if result.status_code == 200:
            print( node, result.json() )

def fetchOSNR( net ):
    "Fetch OSNR values"
    print( '*** Fetching OSNR values from monitors' )
    monitors = net.get( 'monitors' ).json()['monitors']
    for monitor, desc in monitors.items():
        osnr = net.get( 'monitor', params=dict(monitor=monitor ) )
        print( monitor + ':' )
        print( desc )
        print( osnr.json() )


### Control Plane Configuration

def configurePacketSwitches():
    "Configure Open vSwitch 'routers' using OpenFlow"

    print( "*** Configuring Open vSwitch 'routers' remotely... " )

    # Port numbering
    eth1, eth2, eth3 = 1, 2, 3

    # Configure routers
    # eth0: local, eth1: dest1, eth2: dest2
    routers = s1, s2, s3 = [ OFSwitchProxy( s ) for s in  ('s1', 's2', 's3') ]
    subnets = { s: '10.%d.0.0/24' % pop
                for pop, s in enumerate(routers, start=1) }
    for pop, dests in enumerate([(s2,s3), (s1, s3), (s1,s2)], start=1):
        router, dest1, dest2 = routers[ pop - 1], dests[0], dests[1]
        print( 'Configuring', router, 'at', router.remote, 'via OpenFlow...' )
        router.dpctl( 'del-flows' )
        for eth, dest in enumerate( [ dest1, dest2, router ], start=1 ) :
            for protocol in 'ip', 'icmp', 'arp':
                flow = ( protocol + ',ip_dst=' + subnets[dest]+
                         ',actions=dec_ttl,output:%d' % eth )
                router.dpctl( 'add-flow', flow )


def configureTransceivers():
    "Configure transceivers remotely using REST"

    print( "*** Configuring transceivers remotely..." )

    # Port numbering
    eth0, eth1, eth2 = 0, 1, 2
    wdm1_, wdm2_, wdm3, wdm4 = 1, 2, 3, 4

    t1, t2, t3 = [ TerminalProxy( name ) for name in ('t1', 't2', 't3') ]

    t1.connect( ethPort=eth1, wdmPort=wdm3, channel=1, power=0.0 )
    t1.connect( ethPort=eth2, wdmPort=wdm4, channel=2, power=0.0 )
    t2.connect( ethPort=eth1, wdmPort=wdm3, channel=1, power=0.0 )
    t2.connect( ethPort=eth2, wdmPort=wdm4, channel=1, power=0.0 )
    t3.connect( ethPort=eth1, wdmPort=wdm3, channel=2, power=0.0 )
    t3.connect( ethPort=eth2, wdmPort=wdm4, channel=1, power=0.0 )


def configureROADMs():
    "Configure ROADMs remotely using REST"

    print( '*** Configuring ROADMS remotely...' )
    # Port numbering
    wdm1, wdm2, wdm3, wdm4 = 1, 2, 3, 4

    # Configure roadms
    r1, r2, r3 = [ ROADMProxy( name ) for name in ( 'r1', 'r2', 'r3' ) ]
    local1, local2, line1, line2 = wdm1, wdm2, wdm3, wdm4

    # r1: add/drop ch1<->r2, ch2<->r3
    r1.connect( port1=local1, port2=line1, channels=[1] )
    r1.connect( port1=local2, port2=line1, channels=[2] )

    # r2: add/drop ch1<->r1, ch1<->r3
    r2.connect( port1=local1, port2=line1, channels=[1] )
    r2.connect( port1=local2, port2=line2, channels=[1] )
    # r2: pass through ch2 r1<->r3
    r2.connect( port1=line1, port2=line2, channels=[2] )

    # r3: add/drop ch2<->r1, ch1<->r2
    r3.connect( port1=local1, port2=line1, channels=[2] )
    r3.connect( port1=local2, port2=line1, channels=[1] )


if __name__ == '__main__':
    net = RESTProxy()
    nodes = fetchNodes( net )
    fetchLinks( net )
    fetchPorts( net, nodes )
    # Note the ONOS fwd app will handle packet switch configuration
    configurePacketSwitches()
    configureTransceivers()
    configureROADMs()
    fetchOSNR( net )
    print( '*** Done.' )
