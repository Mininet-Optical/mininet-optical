### Mininet-Optical Prototype and Demo

[![tests][1]](https://github.com/UA-Agile-Cloud/optical-network-emulator/actions)

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

- mnoptical: Mininet-Optical Python package (`mnoptical`)
- examples: sample emulation scripts for Mininet-Optical
- tests: tests for simulation mode
- onos_rest_api: ONOS CLI tool and REST proxy used in OFC20 demo
- opticalemulator: southbound REST driver for ONOS used in OFC20 demo
- dist (if present): created by `make dist`

#### Python modules in mnoptical/

- dataplane.py: dataplane emulation
- edfa_params.py: EDFA wavelength dependent gain functions
- link.py: optical link simulation
- network.py: network container for simulation mode
- node.py: optical network element simulation
- rest.py: REST agent for external SDN control
- units.py: units of measurement
- terminal_params: parameters for Terminal simulation
- visualize_topo.py: visualization support

### Subcomponents of mnoptical/

- examples/: emulation mode scripts that can also be used as modules
- ofcdemo/: modules/scripts related to our OFC demo(s)
- topo/: sample topologies for simulation mode

#### Other files

- makefile: has make clean|depend|install|devel targets
- requirements.txt: Python requirements file (for `pip3 install -r`)

[1]: https://github.com/UA-Agile-Cloud/optical-network-emulator/workflows/tests/badge.svg
