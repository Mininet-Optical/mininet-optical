Mininet-Optical Examples
------------------------

These examples are intended to serve as simple examples of
how to use the Mininet-Optical emulation API.

*Bidirectional* examples from tutorial:

simplelink.py: simplified single link topology
singlelink.py: single link topology
singleroadm.py: three terminals connected to a single ROADM

Config scripts (using REST API) for above:

config-singlelink.sh: configure {simple,single}link.py
config-singleroadm.sh: configure singleroadm.py for connectivity
                       between h1 and h2 (only!)

*Unidirectional* examples:

unilinear1.py: unidirectional linear network with 1-degree ROADMs
unilinear2.py: unidirectional linear network with 2-degree ROADMs
uniring.py: unidirectional ring network
uniroadmchain.py: simple unidirectional ROADM chain(s) for testing

The unidirectional examples currently use the internal control API
and implement a 'config' CLI command to configure the network.
