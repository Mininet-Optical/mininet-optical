### Welcome to Mininet-Optical

[![tests][1]][2]

#### Overview

[Mininet-Optical](https://github.com/mininet-optical/mininet-optical)
is is a prototype implementation of an emulator for packet optical software-defined networks.

It includes:

- a **simulator** for the transmission physics of optical networks,
  based on the GN-model
- an **emulated dataplane** that extends [Mininet][3] with optical network elements and links
- a simple **SDN control plane** for the emulated network elements

The simulator may be used independently, or as part of a Mininet packet-optical network.

This enables end-to-end emulation of a software-defined network that includes optical network
elements such as ROADMs, optical transceivers, fiber spans, and EDFAs, packet SDN elements
such as OpenFlow switches and Ethernet links, and SDN controllers to manage both packet
and optical network elements.

Documentation is available at [mininet-optical.org](https://mininet-optical.org).

#### Directories

- mnoptical: Mininet-Optical Python package (`mnoptical`)
- examples: sample emulation scripts for Mininet-Optical
- tests: tests for simulation mode
- docs: Sphinx documentation 
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

#### Subcomponents of mnoptical/

- examples/: emulation mode scripts that can also be used as modules
- ofcdemo/: modules/scripts related to our OFC demo(s)
- topo/: sample topologies for simulation mode

#### Other files

- makefile: has `make clean|depend|install|devel|doc` targets
- requirements.txt: Python requirements file (for `make depend`)

[1]: https://github.com/mininet-optical/mininet-optical/workflows/tests/badge.svg
[2]: https://github.com/mininet-optical/mininet-optical/actions
[3]: https://mininet.org

#### Acknowledgments

Mininet Optical has been developed with support in part from the Department of 
Energy under grant DE-SC0015867, the National Science Foundation under the CIAN 
ERC, COSMOS PAWR platform and COSM-IC project under grants CNS-1827923, 
OAC-2029295, and CNS-2112562. And with support from the Science Foundation 
Ireland through the CONNECT Centre under grant #13/RC/2077_P2 and grants 18/RI/5721 and 14/IA/527.


