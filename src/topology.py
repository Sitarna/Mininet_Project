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
from mininet.node import Node
from mininet.topo import Topo
from mininet.node import Intf
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
import sys
import subprocess
import shlex
from time import sleep
  
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
            bw = 0.256
            delay = '2ms'
            loss = 0
            max_queue_size = 1000
        elif template == 'Y':
            bw = 4
            delay = '10ms'
            loss = 1
            max_queue_size = 1000
        else:
            raise ValueError("Unknown template. Use 'X' or 'Y'.")
        
        # Links
        self.addLink(uav_1,    uav_sw_1, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        self.addLink(uav_sw_1, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        
        self.addLink(uav_2,    uav_sw_2, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        self.addLink(uav_sw_2, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        
        self.addLink(uav_3,    uav_sw_3, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        self.addLink(uav_sw_3, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        
        self.addLink(uav_4,    uav_sw_4, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        self.addLink(uav_sw_4, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        
        self.addLink(uav_5,    uav_sw_5, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
        self.addLink(uav_sw_5, gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
                
        self.addLink(gcs,    gcs_sw, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size = max_queue_size)
 
# connect mininet and Vm 
def setup_veth(vm_if='veth_vm', mn_if='veth_mn', vm_ip='10.0.0.254/24', mn_node=None):

    subprocess.call(f"ip link show {vm_if} >/dev/null 2>&1 && ip link del {vm_if} || true", shell=True)
    subprocess.call(f"ip link show {mn_if} >/dev/null 2>&1 && ip link del {mn_if} || true", shell=True)

    # Create veth pair
    subprocess.check_call(shlex.split(f"ip link add {vm_if} type veth peer name {mn_if}"))

    # Bring both interfaces up on host namespace
    subprocess.check_call(shlex.split(f"ip link set {vm_if} up"))
    subprocess.check_call(shlex.split(f"ip link set {mn_if} up"))

    # If a Mininet switch object is provided, attach mn_if to its bridge explicitly
    if mn_node:
        # mn_node.name is the bridge name that OVS created for that switch
        bridge = mn_node.name
        subprocess.check_call(shlex.split(f"ovs-vsctl --may-exist add-port {bridge} {mn_if}"))
        sleep(0.1)

    # Configure VM-side IP
    subprocess.check_call(shlex.split(f"ip addr flush dev {vm_if}"))
    subprocess.check_call(shlex.split(f"ip addr add {vm_ip} dev {vm_if}"))
    subprocess.check_call(shlex.split(f"ip link set {vm_if} up"))

    try:
        out = subprocess.check_output(shlex.split("ovs-vsctl show")).decode()
    except subprocess.CalledProcessError:
        out = ""
    if mn_if not in out:
        subprocess.check_call(shlex.split(f"ovs-vsctl --may-exist add-port {mn_node.name} {mn_if}"))


def main(template='X'):
    topo=network_from_truck(template=template)
    net = Mininet(
        topo=topo,
        controller=RemoteController,
        switch=lambda name, **kwargs: OVSSwitch(name, protocols='OpenFlow13', **kwargs),
        link=TCLink
    )

    net.start()

    # Retrieve switch and host objects
    gcs_sw = net.get('gcs_sw')
    gcs_host = net.get('gcs')

    # Setup VM <-> Mininet veth
    #To be able to reach groundcontroll from mininet
    setup_veth(vm_if='veth_vm', mn_if='veth_mn', vm_ip='10.0.0.254/24', mn_node=gcs_sw)

  
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
