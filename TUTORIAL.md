
[Terminal 1]  
- Run in terminal: make run 

* 2 terminals will be created, Terminal 3 - Mininet CLI and Terminal 4 - sdn_controller


[Terminal 2]  
- Run in terminal: ./QGroundControl.AppImage

* groundcontrol will run on terminal 2


[Terminal 1]
- Run in terminal:  sudo tcpdump -i gcs_sw-eth1 udp port 14550 -w MAVLink/mavlink.pcap

* Will capture UDP packeges between PX4 and groundcontrol



[Terminal 3 - Mininet CLI]                                               
- Run in terminal: xterm UAV_1

* 1 terminal will be created,  Terminal 5 - Mininet CLI (UAV_1)



[Terminal 5 - Mininet CLI (UAV_1)]                       
- Run in terminal: cd ~/PX4-Autopilot
- Run in terminal: make px4_sitl gazebo-classic_typhoon_h480
- Run in pxh>: mavlink stop-all
- Run in pxh>: mavlink start -u 14550 -o 14550 -t 10.0.0.254 -m onboard



[Terminal 3 - Mininet CLI]            
- Run in terminal: xterm gcs

* 1 terminal will be created,  Terminal 6 - Mininet CLI (gcs)



[Terminal 5 - Mininet CLI (UAV_1)]
- Run in terminal: Ctrl + c

* kill px4

- Run in terminal: cd Mininet_Project/scenarios/
* Run in terminal: python3 sdn_controller_tests.py scenario1.yaml
* change <scenario1.yaml> to other senorio to try more senarios


[Terminal 6 - Mininet CLI (gcs] 
- Run in terminal: iperf3 -s -J -p 5201

----when you are done----
   
[Terminal 1 ] make kill

