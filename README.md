### Mininet-Optical Prototype and Demo

![tests](https://github.com/UA-Agile-Cloud/optical-network-emulator/workflows/tests/badge.svg)

This is a prototype implementation of an emulator for packet optical software-defined networks.

It includes:

- a **simulator** for the transmission physics of optical networks,
  based on the GN-model
- an **emulated dataplane** that extends Mininet with optical network elements and links
- a simple **SDN control plane** for the emulated network elements

The simulator may be used independently, or as part of a Mininet packet-optical network.

This enables end-to-end emulation of a software-defined network that includes optical network
elements such as ROADMs, optical transceivers, fiber spans, and EDFAs, packet SDN elements
such as OpenFlow switches and Ethernet links, and SDN controllers to manage both packet
and optical network elements.

#### Directories

description-files: wavelength-dependent gain functions for EDFAs
ofcdemo: files related to our OFC demo(s)
onos_rest_api: ONOS CLI tool and REST proxy
opticalemulator: southbound REST driver for ONOS
sdn_monitor_qot_e: files for our QoT estimation paper(s)
tests: tests for Mininet-Optical
topo: sample topologies for simulation mode

#### Python modules

link.py: optical link simulation
network.py: network container for simulation mode
node.py: optical network element simulation
README.md: this file
requirements.txt: Python requirements file (for pip3 install -r)
rest.py: REST agent for external SDN control
units.py: units of measurement
visualize_topo.py: visualization support
