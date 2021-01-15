### Mininet-Optical Prototype and Demo

![Tests](https://github.com/UA-Agile-Cloud/optical-network-emulator/workflows/run-tests/badge.svg)

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
