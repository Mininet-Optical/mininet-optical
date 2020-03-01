#!/usr/bin/python

"""
rest.py: Simple REST-based SDN control plane for mininet-optical
"""

from wsgiref.simple_server import make_server, WSGIRequestHandler
from bottle import route, get, post, request, default_app, abort
from threading import Thread

from dataplane import SwitchBase, Terminal, ROADM, OpticalLink
from mininet.node import Switch

"""
Prototype REST API

This is currently very limited. We may wish to add a number of
additional calls, such as the following:

ROADMs
- list rules
- install rule
- delete rule
- reset

Amplifiers
- get/set power

Transceivers
-  get/set power, channel/frequency, modulation

Monitors
-  get monitoring data (OSNR, etc.)
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
                 dict(link=(monitor.link.node1.name,
                            monitor.link.node2.name),
                      amp=monitor.amplifier.name,
                      target_gain=monitor.amplifier.target_gain)
                 for link in opticalLinks()
                 for monitor in link.monitors }
    return dict( monitors=monitors )


@get( '/monitor' )
def monitor():
    "Return information for monitor"
    query = request.query
    monitor = lookUpNode( query.monitor )
    if hasattr( monitor, 'restMonitor' ):
        result = monitor.restMonitor()
    else:
        abort( 404, "Node %s does not appear to be a monitor" % monitor )
    return result


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
def terminalLinks():
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
    node = lookUpNode( query.node )
    if hasattr( node, handlerName ):
        result = getattr( node, handlerName )( query )
    else:
        abort( 404, "No handler for node %s" % node )
    return result


@get( '/connect' )
def connect():
    "Configure connection in optical node"
    return nodeHandler( 'restConnectHandler' )


@get( '/ports' )
def ports():
    "Return a node's ports"
    query = request.query
    node = lookUpNode( query.node )
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
    node = lookUpNode( query.node )
    if hasattr( node, 'restRulesHandler' ):
        return node.restRulesHandler( query )
    else:
        abort( 404, "No rules handler for %s" % node )


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
