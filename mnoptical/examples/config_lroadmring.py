#!/usr/bin/env python3

"""
config_lroadrming.py: simple LumentumRing control script
                      using ofcdemo.lumentum_NETCONF_API
"""

from mnoptical.ofcdemo.lroadm import (
    LROADM, NetconfPortBase, username, password
)

from mnoptical.ofcdemo.lumentum_NETCONF_API import (
    Lumentum, Lumentum_NETCONF
)

from mnoptical.examples.lroadmring import LumentumBase

from mnoptical.ofcdemo.fakecontroller import TerminalProxy

from subprocess import run
from sys import argv

# We allocate a channel for each (src, dst)/(dst,src) pair,
# except for loopback (which we don't want anyway
# because of the ethernet layer.)

def allocChannels(N):
    "Return channel map (src,dst)->ch for N-node mesh"
    ch = 1
    chmap = {}
    for src in range(1, N+1):
        for dst in range(src, N+1):
            # Skip loopback
            if src != dst:
                chmap[src,dst] = chmap[dst,src] = ch
                ch += 1
    return chmap

def genConnection(module, inport, outport, channel, loss=0.0):
    "Return a netconf connection configuration string"
    startfreq, endfreq = Lumentum.freqRangeGHz(channel)
    connection = Lumentum.WSSConnection(
        module=module, connection_id=channel, operation='in-service',
        blocked='false', input_port=inport, output_port=outport,
        start_freq=startfreq, end_freq=endfreq,
        attenuation=loss, name=f'CH{channel}')
    return connection

def genConnections(i, N, chmap):
    """Return netconf connection list connecting
       roadm i to the other roadms in 1..N, each
       via a dedicated channel. This enables full mesh
       connectivity without channel collisions."""
    connections = []
    linein, lineout = LROADM.linein, LROADM.lineout
    passchannels = set(chmap.values())
    for dst in range(1, N+1):
        if i == dst: continue
        addport = LROADM.addbase + dst
        dropport = LROADM.dropbase + dst
        ch = chmap[i,dst]
        assert ch == chmap[dst,i]
        mux, demux = 1, 2
        print(f'r{i} add {ch} from {addport}, drop {ch} to {dropport}')
        incoming = genConnection(demux, linein, dropport, ch)
        outgoing = genConnection(mux, addport, lineout, ch)
        connections.extend([incoming, outgoing])
        passchannels -= {ch}
    print(f'r{i} pass channels {passchannels}')
    for chin in passchannels:
        inpass = genConnection(demux, linein, lineout, chin)
        connections.append(inpass)
    return connections

def configRoadms(N, chmap):
    "Configure LumentumRing ROADMs as a full mesh (NETCONF)"
    # Initialize ROADM connections
    roadms = [Lumentum(f'localhost:{NetconfPortBase+i}',
                       username=username, password=password)
              for i in range(1, N+1)]
    # Configure ROADMs
    for i, roadm in enumerate(roadms, start=1):
        print(f'*** Configuring r{i}')
        connections = genConnections(i, N, chmap)
        reply = roadm.wss_add_connections(connections)
    # Fetch connections
    for i, roadm in enumerate(roadms, start=1):
        connections = roadm.wss_get_connections()
        info = Lumentum_NETCONF.parseConnections(connections)
        print(f'*** r{i} Connections:')
        print(info)

def configTerminals(N, chmap):
    "Connect each transceiver to a dedicated ethernet port (REST)"
    # Note this will not work for hardware unless it supports our
    # REST interface
    ethbase = LumentumBase.ethbase
    txbase, rxbase = LumentumBase.txbase, LumentumBase.rxbase
    for i in range(1, N+1):
        term = TerminalProxy(f't{i}', baseURL='http://localhost:8080/')
        for dst in range(1, N+1):
            if i == dst: continue
            ch = chmap[i,dst]
            # We need two connect() calls to connect our ethernet
            # port to the split wdm tx/rx ports.
            # Note that we aren't configuring power here and are just
            # using the default tx power.
            assert term.connect(ethPort=ethbase+dst, wdmPort=txbase+dst, channel=ch).ok
            assert term.connect(wdmPort=rxbase+dst, ethPort=ethbase+dst, channel=ch).ok
            assert term.turn_on().ok

def configSwitches(N):
    "Program OpenFlow switches with inbound and outbound rules"
    # We assume the default IP addresses of 10.1 .. 10.4
    # If those change, then this configuration will not work
    # Note we are also assuming local OVS switches; remote switches
    # should use the appropriate IP address and port.
    hostport, ethbase = LumentumBase.hostport, LumentumBase.ethbase
    listenPortBase = LumentumBase.listenPortBase
    for i in range(1, N+1):
        # Switch management IP address and passive OpenFlow port
        switch = f'tcp:127.0.0.1:{listenPortBase+i}'
        # Inbound: everything goes to host port
        ip = '10.0.0.{i}'
        for inport in range(1, N+1):
            flow = f'in_port={inport},actions=output:{hostport}'
            run(f'ovs-ofctl add-flow {switch} {flow}'.split(), check=True)
        # Outbound: route to appropriate uplink port
        for dst in range(1, N+1):
            if i == dst: continue
            ip = f'10.0.0.{dst}'
            outport = ethbase + dst
            for protocol in 'ip', 'icmp', 'arp':
                flow = (f'in_port={hostport},{protocol},'
                        f'ip_dst={ip},actions=output:{outport}')
                run(f'ovs-ofctl add-flow {switch} {flow}'.split(), check=True)

def config(N):
    "Configure LumentumRing"
    # Allocate channels
    chmap = allocChannels(N)
    print("*** Configuring ROADMs...")
    configRoadms(N, chmap)
    print("*** Configuring Terminals...")
    configTerminals(N, chmap)
    print("*** Configuring Switches...")
    configSwitches(N)
    return chmap

def dumpChmap(N, chmap):
    "Dump channel map"
    for src in range(1,N+1):
        print(f't{src}: ', end='')
        for dst in range(1,N+1):
            if src == dst: continue
            ch = chmap[src,dst]
            print(f'ch{ch}<->t{dst} ', end='')
        print()

if __name__ == '__main__':
    # We test this as part of the lroadmring.py test
    if 'test' in argv:
        exit(0)
    print("*** Configuring LROADM Ring Network...")
    N = 4
    chmap = config(N)
    dumpChmap(N, chmap)
