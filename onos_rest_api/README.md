### ONOS REST API/CLI

Supported ONOS CLI operations:

1. CONFIGURE A ROADM:        
       `oe-config roadm [roadm_name] [port1_id] [port2_id] [channel_id]

2. CONFIGURE A TERMINAL:    
       `oe-config terminal [terminal_name] [ethPort_id] [wdmPort_id] [channel_id] [power]

3. SHOW ALL LINKS:   
       `oe-config show-links

4. SHOW ALL ROADM-ROADM LINKS:     
       `oe-config show-roadm-links

5. SHOW ALL TERMINAL-ROADM LINKS:  
      ` oe-config show-terminal-links

6. SHOW ALL ROUTER LINKS:   
      ` oe-config show-router-links
      
7. SHOW NETWORK MONITER:    
      ` oe-config monitor
      
8. SHOW LINK OSNR:   
      ` oe-config osnr
      
9. CONFIGURE A DEFAULT NETWORK TOPOLOGY:  
       `oe-config default-topo`

             h1 - s1 - t1 = r1 --- r2 --- r3 = t3 - s3 - h3
                          ||
                          t2 - s2 - h2
