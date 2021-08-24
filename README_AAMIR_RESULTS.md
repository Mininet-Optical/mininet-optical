# Aamir's Thesis Files
This version/branch is the code that Aamir used for his Master's thesis in 2021. 
This has a version used here includes the necissary git files to emulate a 4 node 
optical network topology with 90 transceivers and 100 km between each channel.
##Running the network emulation
To run this code there are three files that need to be run. All in the `ofcdemo/` folder.
- Demo_Control.py
- demolib_2021.py
- demo_2021.py

In order to run this file you need to initialize (from the `optical-network-emulator/`
 folder) demo_2021.py with the command 
```commandline
sudo PYTHONPATH=. python3 ofcdemo/demo_2021.py
```
Which runs the code. From here we open another command line terminal in the 
`optical-network-emulator/` folder and run `Demo_Control.py` with the following line.
```commandline
PYTHONPATH=. python3 ofcdemo/Demo_Control.py
```
###Setting parameters for node traffic transmission 
Inside the file, lines 605-612 are where we define the parameters of our network traffic.

```python
    #Experimental Margins ####################
    CAP_Min_100 = 18 #gosnr (dB)
    CAP_Min_200 = 25.8 #gosnr (dB)
    Traffic_Rate = 1.0
    BBU_Cap = 100 #Requests
    Days = 7 #Days
    pattern='diurnal'
    #############################################
```
Where we set the gOSNR threshold value for the 100G, and 200G configuration.
And ``Traffic_Rate`` is how much the traffic capacity is scaled at. 
>Traffic capacity = 36,000Gb/s * Traffic_Rate

The BBU_cap is how many CPRI traffic requests BBU4 can take from R3.
and `pattern` chooses the traffic style. `diurnal` is the traffic pattern we 
imitated from the literature, and `sawtooth` is one which returns a sawtooth 
traffic pattern.

###Results
This file produces three files for the results. The first is the main results 
file we call `record.txt` which is a record of all the necissary files.

```
Running Simulation with diurnal traffic loaded at <1.0> capacity | with 100G margin of 20 to 25.8 | And BBU4 Capacity of 100 Requests | For 7 Days.
Hour, r2, r3, Lightpaths, average wavelengths, T1 traffic, t4 traffic, r2 rejections, r3 rejections, Total_Rejections,50G, 100G, 200G, Uniderutilised, Total Provisionsing
0, 3600.0, 9360.0, 95, 53.333333333333336, 403, 115, 0.0, 0.0, 0.0, 0, 59, 36, 1, 13100, 12960.0
1, 3060.0, 7560.0, 95, 53.333333333333336, 327, 97, 0.0, 0.0, 0.0, 0, 59, 36, 4, 13100, 10620.0
2, 2520.0000000000005, 5760.0, 92, 51.666666666666664, 258, 72, 0.0, 0.0, 0.0, 0, 57, 35, 10, 12700, 8280.0
```

The first line tells us the simulation parameters. The second line is the result
parameters for our run. and lines 2-5 show the first three hours of our run. 
Every value is seperated by commas.

You can also view the lightpath channels every hour with `Hourly_Results.txt` that proved the results.
 ```
*****Results for every hour*****
Running hour # 0
Number of Lightpaths active: link r1-r2: 80, link r2-r3: 62, link r3-r4: 15
	 Links between r1-r2: dict_items([(0, 0), (86, 1), (29, 2), (6, 3), (72, 4), (3, 5), (33, 6), (82, 7), (34, 8), (49, 9), (44, 10), (56, 11), (51, 12), (16, 13), (42, 14), (36, 15), (62, 16), (32, 17), (87, 18), (61, 32), (59, 33), (74, 34), (85, 35), (43, 36), (84, 37), (60, 38), (76, 39), (89, 40), (23, 41), (13, 42), (12, 43), (21, 44), (48, 45), (19, 46), (80, 47), (68, 48), (27, 49), (88, 50), (7, 51), (14, 52), (10, 53), (69, 54), (18, 55), (64, 56), (52, 57), (75, 58), (28, 59), (73, 60), (53, 61), (46, 62), (11, 63), (70, 64), (45, 65), (25, 66), (20, 67), (77, 68), (30, 69), (37, 70), (39, 71), (81, 72), (17, 73), (67, 74), (15, 75), (2, 76), (35, 77), (55, 78), (47, 79), (58, 80), (5, 81), (9, 82), (71, 83), (41, 84), (8, 85), (1, 86), (31, 87), (38, 88), (40, 89), (22, 90), (79, 91), (54, 92), (63, 93)]) 
	 	 Lightpath # 0 is propegating on channel None with gOSNR of None, Link cap of None, and these channels:None and travelling down this path: None 
	 	 Lightpath # 1 is propegating on channel 86 with gOSNR of 29.22277151338153, Link cap of 200, and these channels:{1, 2, 3, 4, 5, 6, 7, 8} and travelling down this path: ('t2', 'r2', 'r1', 't1') 
	 	 Lightpath # 2 is propegating on channel 29 with gOSNR of 29.128132928421753, Link cap of 200, and these channels:{9, 10, 11, 12, 13, 14, 15, 16} and travelling down this path: ('t2', 'r2', 'r1', 't1') 
```

The first line shows the hour, and how many lightpaths are propegating between each link.
The next lines show the lighpath ID, channel, gOSNR, channel provisioning, traffic ID's and path.

##Files
I have saved the final results from my runs. these are the results produced for my experiments in 
Chapter 5 of my thesis (`Aamir_s_Thesis___SDN.pdf`).
The raw data was copied into `July 27 2021.xlsx` and the final charts used in the thesis are in 
`Final Thesis Data.xlsx`.

