#!/usr/bin/python

"""
rest.py: Simple REST-based SDN control plane for mininet-optical
"""

from wsgiref.simple_server import make_server, WSGIRequestHandler
from bottle import route, get, post, request, default_app, abort
from threading import Thread

from dataplane import SwitchBase

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
    return dict( nodes=[ str(node) for node in net() ] )



@get ( '/links' )
def links():
    "Return list of links"
    links = [ ( intfspec(link.intf1), intfspec(link.intf2) )
              for link in net().links ]
    return dict( links=links )


def intfspec( intf ):
    "Return specifier dict(name, port, intf) for intf"
    return dict( node=intf.node.name, port=intf.node.ports[intf],
                 intf=intf.name )


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
