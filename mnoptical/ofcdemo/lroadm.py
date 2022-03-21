#!/usr/bin/python

"""
lroadm.py:

A simple Lumentum-like ROADM (LROADM) with a (somewhat) compatible NETCONF API
This 1-degree ROADM corresponds to half of a hardware ROADM.

"""

from mnoptical.dataplane import (
    UnidirectionalOpticalLink as ULink,
    ROADM, Terminal,
    OpticalNet as Mininet,
    km, m, dB, dBm)

from mnoptical.ofcdemo.demolib import OpticalCLI as CLI, cleanup
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.netconfserver import NetconfServer
from mnoptical.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.log import setLogLevel, info, debug
from mininet.node import OVSSwitch

from sys import argv

### Default netconf username and password for testing
username = 'admin'
password = 'admin'

### Lumentum ROADM class

NetconfPortBase = 1830  # Control port base

class LROADM( ROADM ):
    "Lumentum-like ROADM with a netconf port"

    # Default netconf username and password
    username = 'admin'
    password = 'admin'

    # Port number constants and helper functions
    linein, lineout = 5101, 4201
    addbase, dropbase = 4100, 5200
    def addport(self, i): return self.addbase + i
    def dropport(self, i): return self.dropbase + i

    def __init__( self, *args, netconfPort=None, **kwargs):
        if not netconfPort:
            raise Exception('Lumentum: netconfPort required')
        self.username = kwargs.pop('username', self.username)
        self.password = kwargs.pop('password', self.password)
        super().__init__(*args, **kwargs)
        self.netconfPort = netconfPort

    def __str__( self ):
        return self.name
