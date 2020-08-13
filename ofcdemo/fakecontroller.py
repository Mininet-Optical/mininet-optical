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

    def reset(self):
        params = dict(node=self.name)
        print('reset', params)
        r = self.get('reset', params=params)
        print(r)

    def turn_on(self, out_ports):
        params = dict(node=self.name, out_ports=out_ports)
        print('turn_on', params)
        r = self.get('turn_on', params=params)
        print(r)


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

    def cleanme(self):
        r = self.get('cleanme', params=dict(node=self.name))
        print(r)


### Configuration Retrieval


def fetchNodes( net ):
    "Fetch node list using REST"
    print( '*** Fetching nodes' )
    r = net.get( 'nodes' )
    return r.json()[ 'nodes' ]


def fetchLinks( net ):
    print( '*** Fetching all links' )
    l = net.get( 'links' ).json()['links']
    print( '*** Fetching ROADM-ROADM links' )
    r = net.get( 'links/roadms' ).json()['links']
    print( '*** Fetching Terminal-ROADM links' )
    t = net.get( 'links/terminals' ).json()['links']
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
    results = { node: result.json()
                for node in nodes
                for result in [net.get( 'ports', dict( node=node ) ) ]
                if result.status_code == 200 }
    return results

def fetchOSNR( net ):
    "Fetch OSNR values"
    print( '*** Fetching OSNR values from monitors' )
    monitors = net.get( 'monitors' ).json()['monitors']
    for monitor, desc in monitors.items():
        osnr = net.get( 'monitor', params=dict(monitor=monitor ) )
        print( monitor + ':' )
        print( desc )
        print( osnr.json() )
