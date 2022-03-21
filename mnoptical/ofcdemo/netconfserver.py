#!/usr/bin/env python3
"""
netconfserver.py: simple netconf server for mininet-optical

TODO:

- implement boost/preamp configuration for new simulator version
- improve configuration report
- implement configuration updates

"""

# pylint: disable=no-name-in-module
from lxml.etree import (QName, Element, SubElement, tostring, fromstring,
                        tounicode)

from netconf import nsmap_update
from netconf.server import SSHUserPassController, NetconfSSHServer
from netconf.util import (elm, subelm, leaf_elm, filter_results,
                          xpath_filter_result, filter_to_xpath)

from os.path import dirname
from threading import Thread
from time import sleep

from mininet.log import info
from mnoptical.dataplane import ROADM
from mnoptical.units import abs_to_db

linein = 5101
lineout = 4201

### Parameters

### XML namespaces

EdfaNsmap = { 'lotee': 'http://www.lumentum.com/lumentum-ote-edfa'}
ConnNsmap = { 'lotet': 'http://www.lumentum.com/lumentum-ote-connection'}
nsmap =  { 'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0' }
for m in EdfaNsmap, ConnNsmap:
    nsmap.update( m )

nsmap_update(nsmap)

### Netconf connection parameters
SSLKeyFile = f"{dirname(__file__)}/../../testcerts/fakeserver.key"
NetconfPortBase = 1830  # default is 830 but we use 1831+


Debug = False

def debug(*args, **kwargs):
    "debug print"
    if Debug:
        print(''.join(map(str, args)), **kwargs)

### Helper functions

def xmlstring( atree ):
    "Return lxml element as a string"
    if atree is not None:
        return tostring(atree, pretty_print=True).decode()

### Connection parsing

configNs = dict( nc="urn:ietf:params:xml:ns:netconf:base:1.0",
                 lotet='http://www.lumentum.com/lumentum-ote-connection')

def parseconn( conn ):
    "Parse config connection and return <dn>,<config> as dicts"

    def convert( value ):
        value = value.strip()
        if isinstance( value, str ) and value and value[0].isnumeric():
            return ( float( value ) if '.' in value or 'e' in value
                     else int( value ) )
        return value

    def textToDict( text ):
        "Convert 'foo=1;bar=2...' to dict"
        result = {}
        entries = text.split( ';' )
        for entry in entries:
            k, v = entry.split( '=' )
            result[ k.strip() ] = convert( v.strip() )
        return result

    def freqToChannels( startfreq, endfreq ):
        half_channel_width = 25  # in GHz
        start_center_frequency = 191350  # in GHz
        startfreq, endfreq = int(startfreq), int(endfreq)
        startfreq += half_channel_width
        channels = []
        ch = (startfreq - start_center_frequency)//50
        assert ch >= 0
        while startfreq < endfreq:
            channels.append( ch )
            startfreq += 50
        return channels

    dn, config, module, inport, outport, channels = (
        None, None, None, None, None, [] )

    for item in conn:
        name = QName(item.tag).localname
        if name == 'dn': dn = item
        elif name == 'config': config = item
    if dn is not None:
        dn = textToDict( dn.text )
        module = dn[ 'module' ]
    if config is not None:
        config = { QName( item.tag ).localname: item.text
                   for item in config }
        for k, v in config.items():
            if isinstance( v, str ) and ';' in v:
                config[ k ] = textToDict( v )
            else:
                config[ k ] = convert( v )
    if config:
        startfreq, endfreq = config[ 'start-freq' ], config[ 'end-freq' ]
        inport = config[ 'input-port-reference' ][ 'port' ]
        outport = config[ 'output-port-reference' ][ 'port' ]
        channels = freqToChannels( startfreq, endfreq )
    return dn, config, module, inport, outport, channels


### Per-ROADM netconf agent

class NetconfAgent:

    "Netconf agent for single (Lumentum-like) ROADM"

    def __init__( self, roadm, port=None, username=None, password=None):
        "Create netconf agent for roadm"

        port = port or roadm.netconfPort
        username = username or roadm.username
        password = password or roadm.password

        self.roadm = roadm
        self.connections = {}

        info( f'*** Starting Netconf Agent for {roadm} on port {port}\n' )

        controller = SSHUserPassController(
            username=username, password=password )

        self.server = NetconfSSHServer(
            server_ctl=controller, server_methods=self,
            port=port, host_key=SSLKeyFile, debug=True)
        assert self.server

    def nc_append_capabilities( self, caps ):
        "Add our base netconf capability"
        # debug("NC_APPEND_CAPABILITIES")
        subelm( caps, 'capability').text = \
            "urn:ietf:params:netconf:capability:xpath:1.0"
        for cap in nsmap.values():
            subelm( caps, 'capability').text = cap

    def rpc_get( self, session, rpc, filter_or_none):
        "Get some config data"
        # debug( "RPC_GET", tounicode(rpc))
        data = elm('nc:data')
        self.add_config(data)
        # FIXME: workaround for filtering not working properly
        if False and filter_or_none and 'connections' in tounicode(
                filter_or_none):
            xpath = '/connections/connection'
            data = xpath_filter_result( data, xpath)
        debug("RETURNING", tounicode(data, pretty_print=True))
        return data

    def rpc_get_config( self, session, rpc, source_elm, filter_or_none ):
        """Passed the source element"""
        debug( "GET_CONFIG!!!" )
        data = elm( "nc:data" )
        self.add_config(data)
        return data

    def rpc_edit_config( self, session, rpc, source_elm,
                         filter_or_none ):
        debug("EDIT_CONFIG")
        data = elm("nc:data")
        config = rpc.xpath(
            '/nc:rpc/nc:edit-config/nc:config/lotet:connections/'
            'lotet:connection', namespaces=configNs)
        for conn in config:
            dn, config, module, inport, outport, channels = parseconn(
                conn )
            self.updateConnections( inport, outport, channels, conn )
            if dn and config:
                print(self.roadm, "connecting", inport, outport, channels)
                self.roadm.connect( inport, outport, channels )
        data.append( elm('ok') )
        return data

    def updateConnections( self, inport, outport, channels, conn ):
        # Delete any overlapping connections
        # (assume they are auto-deleted in emulator as well)
        for i, o, c in list( self.connections.keys() ):
            if ((i == inport or o == outport) and
                c.intersection( channels )):
                del self.connections[i,o,c]
        self.connections[ inport, outport, frozenset(channels) ] = conn
        debug(" UPDATED CONNECTIONS ")
        debug(self.connections)

    def rpc_disable_als( self, session, rpc, *params ):
        debug("DISABLE_ALS")
        data = elm("nc:data")
        return data

    def rpc_remove_all_connections( self, session, rpc, *params ):
        debug("remove_all_connections", self.roadm)
        self.roadm.reset()
        data = elm("nc:data")
        data.append( elm('ok') )
        return data

    def rpc_delete_connection( self, session, rpc, *params):
        debug("DELETE_CONNECTION")
        dn = rpc[0][0]
        self.delete_connection_dn(dn)
        data = elm('nc:data')
        data.append( elm('ok') )
        return data

    def delete_connection_dn(self, dn):
        for spec in self.connections.keys():
            conn = self.connections[spec]
            for entry in conn:
                if entry.tag.endswith('dn') and entry.text == dn.text:
                    inport, outport, channels = spec
                    debug("removing connection", inport, outport, channels)
                    self.roadm.connect( inport, outport, channels, action='remove')
                    del self.connections[spec]
                    return

    def stop( self ):
        "Shut down Netconf server"
        self.server.close()
        self.server.join()

    def add_config( self, data ):
        "Add config entries to rpc return data"
        # XXX to be implemented:
        # self.add_ports( data )
        self.add_edfas( data )
        self.add_connections( data )

    def add_edfas( self, data ):
        "Add EDFA config to data"
        entries = subelm( data, 'edfas', nsmap=EdfaNsmap )
        boost, preamp = 1, 2
        for i in range(1,3):
            edfa = subelm( entries, 'edfa')
            state = subelm( edfa, 'state' )
            state.append( leaf_elm( 'input-power', 0 ) )
            state.append( leaf_elm( 'output-power', 0 ) )
            if i == boost:
                voas = subelm( state, 'voas' )
                voa = subelm( voas, 'voa' )
                voa.append( leaf_elm( 'voa-input-power', 0) )
                voa.append( leaf_elm( 'voa-output-power', 0) )
                voa.append( leaf_elm( 'voa-attenuation', 0) )
            conf = subelm( edfa, 'config' )
            conf.append( leaf_elm( 'lotee:target-gain', 0) )
            conf.append( leaf_elm( 'lotee:target-power', 0) )
            conf.append( leaf_elm( 'lotee:target-gain-tilt', 0) )
            conf.append( leaf_elm( 'lotee:control-mode', 0) )
            conf.append( leaf_elm( 'lotee:gain-switch-mode', 0) )
            conf.append( leaf_elm( 'lotee:maintenance-state', 0) )

    def findInputPower( self, ch ):
        "Return first signal power at ROADM's line input for channel"
        roadm = self.roadm.model
        portsigs = roadm.port_to_optical_signal_in
        found, power = None, None
        for port in [linein]:
            for signal in portsigs[port]:
                if signal.index == ch:
                    found = signal
                    break
        if found:
            state = signal.loc_in_to_state.get( roadm, None)
            if state:
                power = abs_to_db(state['power'])
        return power


    def findOutputPower( self, ch ):
        "Return first signal power at ROADM's line output for channel"
        roadm = self.roadm.model
        portsigs = roadm.port_to_optical_signal_out
        found, power = None, None
        for port in [lineout]:
            for signal in portsigs[port]:
                if signal.index == ch:
                    found = signal
                    break
        if found:
            state = signal.loc_in_to_state.get( roadm, None)
            if state:
                power = abs_to_db(state['power'])
        return power

    def add_connections( self, data):
        connections = SubElement( data, 'connections',
                                  nsmap={None:nsmap['lotet']} )
        for spec in self.connections.keys():
            conn = self.connections[spec]
            inport, outport, channels = spec
            if not conn.xpath('state'):
                state = subelm(conn, 'state')
                iat = subelm(state, 'input-channel-attributes')
                ipower = subelm(iat, 'power')
                oat = subelm(state, 'output-channel-attributes')
                opower = subelm(oat, 'power')
            ipower = conn.xpath(
                'state/input-channel-attributes/power')[0]
            opower = conn.xpath(
                'state/output-channel-attributes/power')[0]
            # We currently only handle a single signal
            assert len(channels) == 1
            ch = list(channels)[0]
            ipow = self.findInputPower(ch)
            opow = self.findOutputPower(ch)
            ipower.text = str(ipow) if ipow is not None else '-50'
            opower.text = str(opow) if opow is not None else '-50'
            connections.append( conn )
        return


class NetconfServer:
    "Collection of Netconf agents for Mininet-Optical network"

    def __init__( self, net, **params):
        self.net = net
        self.servers = []
        self.params = params

    def start( self ):
        "Start up netconf agents"
        roadms = [ s for s in self.net.switches
                   if hasattr( s, 'netconfPort' ) ]
        for roadm in roadms:
            server = NetconfAgent(
                roadm, port=roadm.netconfPort, **self.params )
            self.servers.append( server )

    def stop( self ):
        for s in self.servers:
            s.stop()


def runTestServer():
    "Run netconf server in test mode"
    class DummyRoadm:
        netconfPort = 1831
        username = 'dummy'
        password = 'dummy'
    server = NetconfAgent(DummyRoadm())
    print( '* Starting netconf Agent()')
    try:
        while True: sleep( 30 )
    except KeyboardInterrupt:
        print( '* Stopping netconf server\n' )
        server.stop()


if __name__ == '__main__':
    runTestServer()
    print( '* Done.' )
