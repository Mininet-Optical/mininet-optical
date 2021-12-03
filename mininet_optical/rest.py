#!/usr/bin/python

"""
rest.py: Simple REST-based SDN control plane for mininet-optical
"""

from wsgiref.simple_server import make_server, WSGIRequestHandler
from bottle import route, get, post, request, default_app, abort
from threading import Thread

from mininet_optical.dataplane import SwitchBase, Terminal, ROADM, OpticalLink
from mininet.node import Switch

"""
Prototype REST API

This is currently very limited.  We implement the following
functions:

Network operations

- list nodes: /nodes -> nodes:[ { node: class } ... ]
- list links: /links -> links:[ { node1:port1, node2:port2 } ... ]
- inter-ROADM links: /links/roadms
- terminal links: /links/terminals
- router links: /links/routers

Generic node operations

- reset: /reset?node=r1
- list ports: /ports?node=t1 -> ports={ port: name ... }

ROADM operations

- install rule: /connect?node=r1&port1=n&port2=n&channels='1,2,3'
- delete rule: /connect?node=n&port1=n&port2=n&channels='1,2,3'&action=remove
- list rules: /rules?node=r1 -> rules:{ ruleId: dict(port1, port2, channels) }

Terminal/transceiver operations

- set transceiver(wdmPort)'s channel, power, and ethPort (packet downlink port)
   /connect?node=t1&wdmPort=t1-wdm5&channel=1&power=0.0&ethPort=1

Monitor operations

- list monitors: /monitors
- get monitor data (OSNR, gOSNR): /monitor?monitor=r1-r2-amp2-mon
  -> osnr:{ signal: {freq, osnr, gosnr} }

"""

def net():
    "Return current network object"
    return RestServer.net


@get( '/nodes' )
def nodes():
    "Return list of nodes"
    return dict( nodes={ name:node.__class__.__name__
                         for name, node in net().items() } )


@get( '/monitors' )
def monitors():
    "Return list of monitors"
    monitors = { monitor.name:
                 dict(link=(link.phyLink1.src_node.name,
                            link.phyLink1.dst_node.name),
                      amp=monitor.model.component.name,
                      target_gain=monitor.model.component.target_gain)
                 for link in opticalLinks()
                 for monitor in link.monitors }
    return dict( monitors=monitors )


@get( '/monitor' )
def monitor():
    "Return information for monitor"
    return monitorHandler( 'restMonitor' )


def opticalLinks():
    "Return optical links"
    return [ link for link in net().links
             if isinstance( link, OpticalLink ) ]

@get ( '/links' )
def links():
    "Return list of links"
    return dict( links=[ linkspec( link ) for link in net().links ] )


def linkspec( link ):
    "Return specifier dict(node1, port1, node2, port2) for link"
    intf1, intf2 = link.intf1, link.intf2
    node1, node2 = intf1.node, intf2.node
    port1, port2 = node1.ports[intf1], node2.ports[intf2]
    return { node1.name:port1, node2.name:port2 }


@get( '/links/roadms' )
def interRoadmLinks():
    "Return links between ROADMs (only)"
    links = [ linkspec( link ) for link in net().links
              if ( isinstance( link.intf1.node, ROADM) and
                   isinstance( link.intf2.node, ROADM) ) ]
    return dict( links=links )


@get( '/links/terminals' )
def terminalLinks():
    "Return links from terminals to ROADMs (only)"
    links = [ linkspec( link ) for link in net().links
              if ( (isinstance( link.intf1.node, Terminal) and
                    isinstance( link.intf2.node, ROADM) ) or
                   (isinstance( link.intf2.node, Terminal) and
                    isinstance( link.intf1.node, ROADM) ) ) ]

    return dict( links=links )


@get( '/links/routers' )
def routerLinks():
    "Return links to/from packet switches/routers"
    links = [ linkspec( link ) for link in net().links
              if ((isinstance( link.intf1.node, Switch) and
                   not isinstance( link.intf1.node, SwitchBase)) or
                  (isinstance( link.intf2.node, Switch) and
                   not isinstance( link.intf2.node, SwitchBase))) ]
    return dict( links=links )


def lookUpNode( node ):
    "Look up node from query"
    try:
        return RestServer.net[ node ]
    except:
        abort( 404, "Unknown node: %s" % node )


def nodeHandler( handlerName ):
    "Handle a node query"
    query = request.query
    node = lookUpNode( query.node )  # pylint: disable=no-member
    if hasattr( node, handlerName ):
        result = getattr( node, handlerName )( query )
    else:
        abort( 404, "No handler for node %s" % node )
    return result

def monitorHandler( handlerName ):
    "Handle a node query"
    query = request.query
    monitor = lookUpNode( query.monitor )  # pylint: disable=no-member
    if hasattr( monitor, handlerName ):
        result = getattr( monitor, handlerName )( query )
    else:
        abort( 404, "No handler for monitor %s" % monitor )
    return result

@get( '/reset' )
def reset():
    "Reset/clear a node's flow rules"
    return nodeHandler( 'restResetHandler' )


@get( '/connect' )
def connect():
    "Configure (or install/remove) connection in optical node"
    return nodeHandler( 'restConnectHandler' )


@get( '/disconnect' )
def disconnect():
    "Configure (or install/remove) connection in optical node"
    return nodeHandler( 'restDisconnectHandler' )


@get( '/ports' )
def ports():
    "Return a node's ports"
    query = request.query
    node = lookUpNode( query.node )  # pylint: disable=no-member
    # Ugly, but functional on any node
    return SwitchBase.restPortsDict( node )



@get( '/info' )
def info():
    "Return an object's configuration and other information"
    pass


@get( '/config' )
def config():
    "Set an object's configuration"
    pass


@get( '/rules' )
def rules():
    "Return rules for node"
    query = request.query
    node = lookUpNode( query.node )  # pylint: disable=no-member
    if hasattr( node, 'restRulesHandler' ):
        return node.restRulesHandler( query )
    else:
        abort( 404, "No rules handler for %s" % node )


@get( '/cleanme' )
def cleanme():
    "Return cleanme for node"
    query = request.query
    node = lookUpNode( query.node )  # pylint: disable=no-member
    if hasattr( node, 'restCleanmeHandler' ):
        return node.restCleanmeHandler( query )
    else:
        abort( 404, "No cleanme handler for %s" % node )


@get( '/turn_on' )
def turn_on():
    query = request.query
    node = lookUpNode(query.node)  # pylint: disable=no-member
    if hasattr( node, 'restTurnonHandler' ):
        return node.restTurnonHandler()
    else:
        abort( 404, "No turn_on handler for %s" % node )


# Demo support (not part of SDN API)

@get( '/setgain' )
def setgain():
    "Demo support: tell Mininet to adjust the gain for am amplifier"
    net().restSetgainHandler( request.query )

@get( '/set_ripple' )
def set_ripple():
    "Demo support: tell Mininet to adjust the ripple function for am amplifier"
    net().restSetrippleHandler( request.query )


# REST Server

class QuietHandler( WSGIRequestHandler ):
    "Handler with quiet logging"
    quiet = True
    def log_request( self, *args, **kwargs ):
        if not self.quiet:
            return WSGIRequestHandler.log_request( *args, **kwargs )


class RestServer( object ):
    "Simple REST server"

    net = {}

    def __init__( self, net, quiet=True ):
        """net: mininet-optical network or node dict
           quiet: quiet logging? (True)"""
        RestServer.net = net
        self.quiet = quiet

    def start( self ):
        "Start REST server"
        app = default_app()
        handler = QuietHandler if self.quiet else WSGIRequestHandler
        self.server = make_server(
            'localhost', 8080, app, handler_class=handler )
        self.thread = Thread( target=self.server.serve_forever )
        self.thread.start()

    def stop( self ):
        self.server.shutdown()
        self.thread.join()
