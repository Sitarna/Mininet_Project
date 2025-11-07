#The standard topology.
#
# UAV host <=> uav_sw <=> gcs_sw <=> GCS host
# Run topology
# Clean previous Mininet sessions: sudo mn -c
# Run topology with template X: sudo -E python3 topology.py
# Run topology with template Y: sudo -E python3 topology.py Y
# - sudo -E mn --custom topology.py --topo network_from_truck --controller=remote,ip=127.0.0.1,port=6653  --switch=ovs,protocols=OpenFlow13 
#
#
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
import sys
  
class network_from_truck(Topo):
    def build(self, template='X'):
        # Hosts
        gcs = self.addHost('gcs', ip='10.0.0.1/24')
        uav_1 = self.addHost('UAV_1', ip='10.0.0.2/24')
        uav_2 = self.addHost('UAV_2', ip='10.0.0.3/24')
        uav_3 = self.addHost('UAV_3', ip='10.0.0.4/24')
        uav_4 = self.addHost('UAV_4', ip='10.0.0.5/24')
        uav_5 = self.addHost('UAV_5', ip='10.0.0.6/24')
        
        
        # Switches
        gcs_sw = self.addSwitch('gcs_sw'  , dpid='0000000000000001')
        uav_sw_1 = self.addSwitch('uav_sw_1', dpid='0000000000000002')
        uav_sw_2 = self.addSwitch('uav_sw_2', dpid='0000000000000003')
        uav_sw_3 = self.addSwitch('uav_sw_3', dpid='0000000000000004')
        uav_sw_4 = self.addSwitch('uav_sw_4', dpid='0000000000000005')
        uav_sw_5 = self.addSwitch('uav_sw_5', dpid='0000000000000006')
        
# Template X — Control/C2: small UDP, high priority, low latency/jitter    
# bandwidth is 128 kbps, 2 milliseconds latency, 0% packet loss
     
# Template Y — Video/Telemetry: higher bitrate, guaranteed minimum rate    
# bandwidth is 4 Mbps, 10 milliseconds latency, 1% packet loss

        if template == 'X':
            bw = 0.128
            delay = '2ms'
            loss = 0
        elif template == 'Y':
            bw = 4
            delay = '10ms'
            loss = 1
        else:
            raise ValueError("Unknown template. Use 'X' or 'Y'.")

        # Links
        self.addLink(uav_1,    uav_sw_1, cls=TCLink, bw=bw, delay=delay, loss=loss)
        self.addLink(uav_sw_1, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss)
        
        self.addLink(uav_2,    uav_sw_2, cls=TCLink, bw=bw, delay=delay, loss=loss)
        self.addLink(uav_sw_2, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss)
        
        self.addLink(uav_3,    uav_sw_3, cls=TCLink, bw=bw, delay=delay, loss=loss)
        self.addLink(uav_sw_3, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss)
        
        self.addLink(uav_4,    uav_sw_4, cls=TCLink, bw=bw, delay=delay, loss=loss)
        self.addLink(uav_sw_4, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss)
        
        self.addLink(uav_5,    uav_sw_5, cls=TCLink, bw=bw, delay=delay, loss=loss)
        self.addLink(uav_sw_5, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss)
                
        self.addLink(gcs,    gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss)
        
def main(template='X'):
    topo=network_from_truck(template=template)
    net = Mininet(
        topo=topo,
        controller=RemoteController,
        switch=lambda name, **kwargs: OVSSwitch(name, protocols='OpenFlow13', **kwargs),
        link=TCLink
    )

    net.start()

    print(f"\n=== Topology started with template {template} ===")
    gcs_host = net.get('gcs')
    print(f"GCS IP: {gcs_host.IP()}")
    for i in range(1, 6):
        uav_host = net.get(f'UAV_{i}')
        print(f"UAV {i} IP: {uav_host.IP()}")
        net.ping([gcs_host, uav_host])

    CLI(net)
    net.stop()

# Make the topo visible to CLI
topos = { 'network_from_truck': network_from_truck }


# ---------- Start ----------
 
if __name__ == '__main__':
    template = sys.argv[1] if len(sys.argv) > 1 else 'X'
    main(template=template)