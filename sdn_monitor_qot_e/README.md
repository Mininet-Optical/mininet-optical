The scripts in this directory enable to reproduction of the PTL 2020 experiments for Monitoring-Based QoT Estimation Correction Evaluated in Optical SDN Emulation System.

There are two linear topologies described as follows:

1) 5 ROADM nodes connected by optical fibre links of 240 km, made up of 3 x 80 km spans. Boost EDFAs at each ROADM output compensate the 17 dB mean ROADM loss, and inline EDFAs compensate the 17.6 dB fibre span loss. The total end-to-end distance is 960 km. OPM devices are applied at the EDFA outputs depending on the monitoring stategy described below. For the purposes of this analysis, we consider OPM devices capable of separately measuring signal power, ASE noise and non-linear interference noise levels.

2) 15 ROADM nodes, connected by 480 km links, made up of 6 x 80 km spans, totaling 6,720 km. To model the WDG behaviour, measured 90-channel WDG functions from two stage gain flattened EDFAs were used, and were randomly assigned to each EDFA.
For the transmission system, 3 different C-band traffic loads were considered, corresponding to 10-, 30- and 90-% of the system capacity -- 9, 27 and 81 signals, respectively, in a 90-channel transmission system. 

Two different channel allocation strategies were examined: sequential and random, to account for wavelength loading and configuration dependencies.

For the SDN control we implement a mock-controller based on proxy objects that allow control over the network with a customized SDN control REST API via Python.
