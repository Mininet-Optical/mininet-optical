### ONOS REST API/CLI

Supported ONOS CLI operations:

1. CONFIGURE A ROADM:        
       `onos> oe-config roadm [roadm_name] [port1_id] [port2_id] [channel_id]

2. CONFIGURE A TERMINAL:    
       `onos> oe-config terminal [terminal_name] [ethPort_id] [wdmPort_id] [channel_id] [power]

3. SHOW ALL LINKS:   
       `onos> oe-config show-links

4. SHOW ALL ROADM-ROADM LINKS:     
       `onos> oe-config show-roadm-links

5. SHOW ALL TERMINAL-ROADM LINKS:  
       `onos> oe-config show-terminal-links

6. SHOW ALL ROUTER LINKS:   
       `onos> oe-config show-router-links
      
7. SHOW NETWORK MONITER:    
       `onos> oe-config monitor
      
8. SHOW LINK OSNR:   
       `onos> oe-config osnr
      
9. SET AMP r1-r2-boost GAIN 0:  
       `onos> oe-config set-gain r1-r2-amp 0
       
10. ADD DEMO NETWORK WITH MESH NETWORK FLOWS (EACH FLOW COMES WITH A RANDOM CHANNEL, NOT DULICATED):  
       `onos> oe-config demo-mesh-flows

11. ADD A SINGLE FLOW FROM ROUTER1 s1 TO ROUTER2 s2 WITH A WAVELENGTH CHANNEL 5 (optional):  
       `onos> oe-config add-flow s1 s2 5

12. RESET A ROADM r1 CONFIGURATION:  
       `onos> oe-config reset r1

13. SHOW ALL PORTS OF A ROADM r1:  
       `onos> oe-config show-ports r1

14. CONFIGURE A DEMO NETWORK TOPOLOGY:  
       `onos> oe-config demo-topo
 
15. SET DEMO FLOWS:  
       `onos> oe-config demo-flows
       
16. CLEAN DEMO FLOWS:  
       `onos> oe-config clean-flows

      




