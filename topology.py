#The standard topology.
#
# UAV host <=> uav_sw <=> gcs_sw <=> GCS host
#		Run topology
# - sudo -E mn --custom topology.py --topo network_from_truck --controller=remote,ip=127.0.0.1,port=6653  --switch=ovs,protocols=OpenFlow13 
#
#
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI

class network_from_truck(Topo):
    def build(network):
        # Hosts
        
        uav = network.addHost('uav', ip='10.0.0.1/24')
        gcs = network.addHost('gcs', ip='10.0.0.2/24')
        
        # Switches
        uav_sw = network.addSwitch('uav_sw', dpid='0000000000000001')
        gcs_sw = network.addSwitch('gcs_sw', dpid='0000000000000002')
        
        
# Template X — Control/C2: small UDP, high priority, low latency/jitter    
# bandwidth is 128 kbps, 2 milliseconds latency, 0% packet loss

        network.addLink(uav, uav_sw, cls=TCLink, bw=0.128, delay='2ms', loss=0)
        network.addLink(uav_sw, gcs_sw, cls=TCLink, bw=0.128, delay='2ms', loss=0)
     
# Template Y — Video/Telemetry: higher bitrate, guaranteed minimum rate    
# bandwidth is 4 Mbps, 10 milliseconds latency, 1% packet loss

        network.addLink(gcs, gcs_sw, cls=TCLink, bw=4, delay='10ms', loss=1)
        network.addLink(uav_sw, gcs_sw, cls=TCLink, bw=4, delay='10ms', loss=1)


def main():
    net = Mininet(
        topo=network_from_truck(),
        controller=RemoteController,
    )

    net.start()
    
    CLI(net)
    net.stop()

# Make the topo visible to CLI
topos = { 'network_from_truck': network_from_truck }


# ---------- Start ----------
if __name__ == '__main__':
    main()
