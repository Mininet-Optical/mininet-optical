#!/usr/bin/python

"""

fakecontroller.py: script to test REST API

The real controller will be ONOS, and it may use
GNMI or Netconf rather than REST.

"""

import requests


class TerminalProxy( object ):
    "Local proxy for Terminal/transceiver configuration via REST"

    def __init__( self, name ):
        self.name = name

    def connect( self, ethPort, tx, wdmPort, channel ):
        "Configure terminal/transceiver"
        params = dict( node=self.name, ethPort=ethPort, tx=tx, wdmPort=wdmPort,
                       channel=channel)
        print('connect', params)
        r = requests.get( 'http://localhost:8080/connect', params=params)
        print(r)


class ROADMProxy( object ):
    "Local proxy for ROADM configuration via REST"

    def __init__( self, name ):
        self.name = name

    def connect( self, port1, port2, channels ):
        "Configure ROADM"
        channels = ','.join( str(channel) for channel in channels)
        params = dict(
            node=self.name, port1=port1, port2=port2, channels=channels )
        print('connect', params)
        r = requests.get( 'http://localhost:8080/connect', params=params)
        print(r)


def fetchNodes():
    "Fetch node list using REST"
    print( '*** Fetching node list' )
    r = requests.get( 'http://localhost:8080/nodes' )
    print(r.json()['nodes'])


def fetchRules( nodes=['r1','r2','r3'] ):
    "Fetch ROADM rules using REST"
    print( '*** Fetching ROADM rules' )
    for node in nodes:
        r = requests.get( 'http://localhost:8080/rules', params=dict(node=node) )
        print( '***', node, 'rules:')
        print( r.json() )


def configureTransceivers():
    "Configure transceivers remotely using REST"

    print( "*** Configuring transceivers remotely..." )

    # Port numbering
    eth0, eth1, eth2 = 0, 1, 2
    wdm1, wdm2, wdm3, wdm4 = 1, 2, 3, 4

    t1, t2, t3 = [ TerminalProxy( name ) for name in ('t1', 't2', 't3') ]

    t1.connect( tx=0, ethPort=eth1, wdmPort=wdm3, channel=1)
    t1.connect( tx=1, ethPort=eth2, wdmPort=wdm4, channel=2)
    t2.connect( tx=0, ethPort=eth1, wdmPort=wdm3, channel=1)
    t2.connect( tx=1, ethPort=eth2, wdmPort=wdm4, channel=1)
    t3.connect( tx=0, ethPort=eth1, wdmPort=wdm3, channel=2)
    t3.connect( tx=1, ethPort=eth2, wdmPort=wdm4, channel=1)


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
    fetchNodes()
    configureTransceivers()
    configureROADMs()
    print( '*** Done.' )
