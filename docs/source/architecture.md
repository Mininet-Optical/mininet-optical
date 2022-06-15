### Mininet-Optical - An Introduction

Mininet-Optical is an optical network emulation tool that seeks to expand on Mininet's capabilities with simulating an optical network with tools such as Fiber Optic Cables, Terminals, Reconfigurable Optical Add-Drop Multiplexers (ROADMs), Amplifiers and so on.

Mininet is a network emulation tool that creates a realistic virtual network, running real kernel, switch and application code,on a single machine (VM, cloud or native).Since it is very easy to interact with therealistic virtual network using the Mininet CLI (and API), customize it, shareit with others, or deploy it on real hardware, Mininet is useful fordevelopment, teaching, and research. Mininet is also a great way to develop,share, and experiment with Software-Defined Networking (SDN) systems usingOpenFlow and P4.

![](images/Mininet_optical.svg)
<figcaption>Figure. Equivalence of a virtual network designed in Mininet-Optical and a real network

The illustrated virtual network is exactly equivalent to the real network. Any control mechanisms designed for the virtual network will work as is in the real network. As a result, Mininet-optical allows us to make a "digital twin" of a real network (or testbed) and carry out experiments in a sotware environment. As a result, we have faster turn out time and a fail safe approach. The software can be easily reset to the original condition in case of any unforeseen problems. 


#### Architecture

Mininet-Optical creates an abstract layer over the kernel of the base Linux OS. The library of Mininet-optical has implementations for various optical networking devices like  Fiber Optic Cables, Terminals, Reconfigurable Optical Add-Drop Multiplexers (ROADMs), Amplifiers and so on. The library also has modules for Optical signal generation and propagation. An user can modify or add further device modules using Python.

The network devices implemented inside Mininet-Optical interact with the SDN interface via the Python API. The SDN interface has provisions of designing the control logic. 

Mininet-Optical creates VMs over the base OS to create emulated copies of the hosts. 

The overall architecture is illustrated below. 

![](images/Mininet_optical_overview.svg)
<figcaption>Figure. Mininet-Optical Architecture
