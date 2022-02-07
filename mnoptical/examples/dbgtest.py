#!/usr/bin/env python3

"""
dbgtest.py: test debugging support
"""

from mnoptical.dataplane import OpticalNet as Mininet, ROADM, OpticalLink
from mnoptical.node import SignalTracing as ST, NodeAuditing as NA

from mnoptical.examples.uniroadmchain import UniRoadmChain
from mnoptical.ofcdemo.demolib import cleanup

from mininet.log import setLogLevel, info

def dbgtest(net):
    "Test debugging support"
    info('*** Testing debugging support\n')
    # Check path from t1
    t1, t2 = net['t1'].model, net['t2'].model
    paths = ST.channel_paths(t1)
    sigs, entries = tuple(paths.keys()), tuple(paths.values())
    assert len(sigs) == 1, "More than one signal found"
    assert len(entries) == 1, "More than one path found"
    sig = sigs[0]
    path = entries[0]
    assert sig.index == 1, "Signal index should be 1"
    assert path[0] == t1, "Path should start at t1"
    assert path[-1] == t2, "Path should end at t2"
    for sig, path in paths.items():
        state = ST.path_state(sig, path)
    # Audit ROADMs and Links
    roadms = [node.model for node in net.switches
              if isinstance(node, ROADM)]
    for roadm in roadms:
        roadmErrors = NA.check_roadm_propagation(roadm)
        assert roadmErrors == 0
    links = [link for link in net.links
             if isinstance(link, OpticalLink)]
    for link in links:
        for plink in link.phyLink1, link.phyLink2:
            if plink:
                linkErrors = NA.check_link_propagation(plink)
                assert linkErrors == 0


if __name__ == '__main__':

    cleanup()  # Just in case!
    setLogLevel('info')
    topo = UniRoadmChain(roadmCount=4)
    net = Mininet(topo=topo, controller=None)
    net.start()
    info(topo.__doc__, '\n')
    net.topo.configNet(net)
    dbgtest(net)
    net.stop()
