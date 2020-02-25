### Mininet-Optical Prototype and Demo

This is a prototype implementation of an emulator for packet optical software-defined networks.

It includes:

- a **simulator** for the transmission physics of optical networks, 
  based on the Gaussian Noise (GN) model
- an **emulated dataplane** that extends Mininet with optical network elements and links
- a simple **control plane** for the emulated network elements

The simulator may be used independently, or as part of the Mininet packet-optical network.

This enables end-to-end emulation of a software-defined network that includes optical network 
elements such as ROADMs, optical transceivers, fiber spans, and EDFAs, packet SDN elements 
such as OpenFlow switches and Ethernet links, as well as SDN controllers to manage both packet
and optical network elements.


