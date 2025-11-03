#The standard topology.
#
# UAV host <=> uav_sw <=> gcs_sw <=> GCS host
#		Run topology
# - sudo -E mn --controller=remote,ip=127.0.0.1,port=6653 --custom topology.py --topo network_from_truck
#
#

import os
os.system('sudo mn -c > /dev/null 2>&1')


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink

class network_from_truck(Topo):
    def build(self):
        uav = self.addHost('uav')
        gcs = self.addHost('gcs')
        uav_sw = self.addSwitch('uav_sw', dpid='0000000000000001')
        gcs_sw = self.addSwitch('gcs_sw', dpid='0000000000000002')
        self.addLink(uav, uav_sw)
        self.addLink(gcs, gcs_sw)
        self.addLink(
            uav_sw, gcs_sw,
            cls=TCLink,
            bw=4,          # bandwidth is 4 Mbps
            delay='10ms',   # 10 milliseconds latency
            loss=1,         # 1% packet loss
        )
        

if __name__ == '__main__':
    net = Mininet(topo=network_from_truck(), controller=RemoteController, switch=OVSSwitch)
    net.start()
    #net.pingAll()


topos = { 'network_from_truck': network_from_truck }
