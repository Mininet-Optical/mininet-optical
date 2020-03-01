### ONOS REST API/CLI

Supported CLI opertions:

1. CONFIGURE A ROADM: 
       `emulator-config-topo roadm [roadm_name] [port1_id] [port2_id] [channel_id]`

2. CONFIGURE A TERMINAL: 
       `emulator-config-topo terminal [terminal_name] [ethPort_id] [wdmPort_id] [channel_id] [power]`

3. SHOW ALL LINKS: 
       `emulator-config-topo show-links`

4. SHOW ALL ROADM-ROADM LINKS: 
       `emulator-config-topo show-roadm-links`

5. SHOW ALL TERMINAL-ROADM LINKS: 
      `emulator-config-topo show-terminal-links`

6. CONFIGURE A DEFAULT NETWORK TOPOLOGY: 
       `emulator-config-topo default-topo`

             h1 - s1 - t1 = r1 --- r2 --- r3 = t3 - s3 - h3
                          ||
                          t2 - s2 - h2
