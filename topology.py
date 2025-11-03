#The standard topology.
#
# UAV host <=> uav_sw <=> gcs_sw <=> GCS host
#		Run topology
# - sudo -E mn --controller=remote,ip=127.0.0.1,port=6653 --custom topology.py --topo network_from_truck
#
#
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI

class network_from_truck(Topo):
    def build(self):
        # Hosts
        
        uav = self.addHost('uav')
        gcs = self.addHost('gcs')
        
        # Switches
        uav_sw = self.addSwitch('uav_sw', dpid='0000000000000001')
        gcs_sw = self.addSwitch('gcs_sw', dpid='0000000000000002')
        
        
# Template X — Control/C2: small UDP, high priority, low latency/jitter    
# bandwidth is 128 kbps, 2 milliseconds latency, 0% packet loss

        self.addLink(uav, uav_sw, cls=TCLink, bw=0.128, delay='2ms', loss=0)
        self.addLink(uav_sw, gcs_sw, cls=TCLink, bw=0.128, delay='2ms', loss=0)
     
# Template Y — Video/Telemetry: higher bitrate, guaranteed minimum rate    
# bandwidth is 4 Mbps, 10 milliseconds latency, 1% packet loss

        self.addLink(gcs, gcs_sw, cls=TCLink, bw=4, delay='10ms', loss=1)
        self.addLink(uav_sw, gcs_sw, cls=TCLink, bw=4, delay='10ms', loss=1)


def main():
    net = Mininet(topo=network_from_truck(),
                  controller=RemoteController,
                  switch=OVSSwitch)
    net.start()
    CLI(net)
    net.stop()

# Make the topo visible to CLI
topos = { 'network_from_truck': network_from_truck }


# ---------- Start ----------
if __name__ == '__main__':
    main()
