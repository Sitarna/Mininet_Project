#Our future controller
#Run the controller: sudo -E ~/venv-ryu39/bin/ryu-manager --ofp-tcp-listen-port 6653 ./sdn_controller.py --verbose
import sys, os
sys.path.append(os.path.dirname(__file__))

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ipv4, arp
from ryu.lib.packet import ethernet, ether_types
from ryu.lib.mac import haddr_to_bin
from threading import Thread

from .client import provision
import time 
from pathlib import Path

class LearningSwitch(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

        def __init__(self, *args, **kwargs):
            super(LearningSwitch, self).__init__(*args, **kwargs)
            self.mac_to_port = {}
            
            # VM-facing interface
            self.vm_ip = "10.0.0.254"
            self.vm_mac = None          # will be learned dynamically from ARP
            self.vm_registered = False  # becomes True when we detect veth_mn on switch

    
            #Prioritites for later. Think that priority 1 is a rescue/search, prio 2 is an e.g surveillance
            #and prio 3 is a media drone
            self.drone_priority = {
                "10.0.0.2": 1,
                "10.0.0.3": 2,
                "10.0.0.4": 3,
                "10.0.0.5": 3,
                "10.0.0.6": 3
                }
            self.meters_installed = {}
            self.meter_id_map = {}
            self.ip_to_host = {}
        
        #should be self explanatory
        def get_priority(self, pkt):
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            if ip_pkt:
                return self.drone_priority.get(ip_pkt.src,3)
            return 3
        
        #Get our prioritites straight
        def setup_meters(self, datapath):
            if self.meters_installed.get(datapath.id, False):
                return
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            
            #Just temporary rates depending on priority
            #change rates later if needed:D
            rates = {1: 2000, 2: 1000, 3: 500}
            burst = 100
            
            self.meter_id_map = {1:1, 2:2, 3:3}
            
            self.meters_installed[datapath.id] = True
            
            for prio, rate in rates.items():
                meter_id = prio
                bands = [parser.OFPMeterBandDrop(rate=rate, burst_size=burst)]
                mod = parser.OFPMeterMod(datapath=datapath,
                                         command=ofproto.OFPMC_ADD,
                                         flags=ofproto.OFPMF_KBPS,
                                         meter_id=meter_id,
                                         bands=bands)
                
                datapath.send_msg(mod)
                self.meter_id_map[prio] = meter_id
                


        @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
        def switch_feature_handler(self, ev):
            datapath = ev.msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            # Table-miss flow
            match = parser.OFPMatch()
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=match, instructions=inst)
            datapath.send_msg(mod)

            self.setup_meters(datapath)

            # Request port descriptions to detect VM
            req = parser.OFPPortDescStatsRequest(datapath, 0)
            datapath.send_msg(req)
        
        @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
        def port_desc_stats_reply_handler(self, ev):
            datapath = ev.msg.datapath
           
            for port in ev.msg.body:
                # port.name is a bytes sometimes; cast to str for safety
                try:
                    pname = port.name.decode() if isinstance(port.name, bytes) else port.name
                except Exception:
                    pname = port.name
                if pname == "veth_mn":
                    self.logger.info("Detected VM link on switch %s, port %s", datapath.id, port.port_no)
                    # Store mapping; MAC may be unknown yet so store placeholder
                    stored_mac = self.vm_mac if self.vm_mac else None
                    self.ip_to_host[self.vm_ip] = (stored_mac, datapath.id, port.port_no)
                    if stored_mac:
                        self.mac_to_port.setdefault(datapath.id, {})[stored_mac] = port.port_no
                    self.vm_registered = True
        
        def provision_async(self, template):
            def worker():
                try:
                    result = provision(template)
                    self.logger.debug("Provision finished with code: %s, template: %s", result, template)
                except Exception as e:
                    self.logger.exception("Provision error: %s", e)
            t = Thread(target=worker)
            t.daemon = True
            t.start()
          
        def install_vm_flow(self, datapath):
            if self.vm_mac and self.vm_ip in self.ip_to_host:
                ofproto = datapath.ofproto
                parser = datapath.ofproto_parser
                vm_port = self.ip_to_host[self.vm_ip][2]

                match = parser.OFPMatch(
                    eth_type=0x0800,
                    ipv4_dst=self.vm_ip,
                    ip_proto=17  # UDP
                )
                actions = [parser.OFPActionOutput(vm_port)]
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                flow_mod = parser.OFPFlowMod(datapath=datapath,
                                             priority=100,
                                             match=match,
                                             instructions=inst)
                datapath.send_msg(flow_mod)
                self.logger.info("Installed dedicated flow for VM %s at port %s", self.vm_ip, vm_port)

        def handle_arp(self, datapath, in_port, eth, arp_pkt, msg):
            parser = datapath.ofproto_parser
            ofproto = datapath.ofproto
            
        
            self.ip_to_host[arp_pkt.src_ip] = (arp_pkt.src_mac, datapath.id, in_port)
            self.mac_to_port.setdefault(datapath.id, {})[arp_pkt.src_mac] = in_port

            if arp_pkt.src_ip == self.vm_ip:
                if self.vm_mac != arp_pkt.src_mac:
                    self.logger.info(f"Auto-learning VM MAC: {arp_pkt.src_mac} (was: {self.vm_mac})")
                self.vm_mac = arp_pkt.src_mac

                self.ip_to_host[self.vm_ip] = (self.vm_mac, datapath.id, in_port)
                self.mac_to_port.setdefault(datapath.id, {})[self.vm_mac] = in_port

                self.install_vm_flow(datapath)
            
            
            if arp_pkt.opcode == arp.ARP_REQUEST:
                self.logger.info("An arp package has appeared from switch %s", datapath.id)
                tgt = arp_pkt.dst_ip
                if tgt in self.ip_to_host:
                    tgt_mac, _, _ = self.ip_to_host[tgt]
                    
                    if tgt_mac is None:
                        self.logger.warning("Cannot send ARP reply: target unkown")
                        return False
                    
                    eth_rep = ethernet.ethernet(dst=eth.src, src=tgt_mac, ethertype=ether_types.ETH_TYPE_ARP)
                    arp_rep = arp.arp(opcode=arp.ARP_REPLY,
                                      src_mac=tgt_mac,
                                      src_ip=tgt,
                                      dst_mac=arp_pkt.src_mac,
                                      dst_ip=arp_pkt.src_ip)
                    p = packet.Packet()
                    p.add_protocol(eth_rep)
                    p.add_protocol(arp_rep)
                    p.serialize()
                    actions = [parser.OFPActionOutput(in_port)]
                    out = parser.OFPPacketOut(datapath=datapath,
                                              buffer_id=ofproto.OFP_NO_BUFFER,
                                              in_port=ofproto.OFPP_CONTROLLER,
                                              actions=actions,
                                              data=p.data)
                    
                    datapath.send_msg(out)
                    return True
                return False
        

        @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
        def packet_in_handler(self, ev):
            msg = ev.msg
            datapath = msg.datapath
            dpid = datapath.id
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            
            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocol(ethernet.ethernet)
            
         
            #Ignore LLDP packages
            #if eth.ethertype == 0x88cc or eth is None:
            #    return
               
            if eth is None or eth.ethertype == 0x88cc:
               return
   
            dst = eth.dst
            src = eth.src
            in_port = msg.match['in_port']
            
            self.mac_to_port.setdefault(dpid, {})
            
            if src not in self.mac_to_port[dpid]:
                self.logger.info("Switch %s learned %s is at port %s", dpid, src, in_port)

            self.mac_to_port[dpid][src] = in_port
            
            arp_pkt = pkt.get_protocol(arp.arp)
            if arp_pkt:
                handled = self.handle_arp(datapath, in_port, eth, arp_pkt, msg)
                if handled:
                    return
                
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
            else:
                out_port = ofproto.OFPP_FLOOD
                
            actions = [parser.OFPActionOutput(out_port)]
               
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            if ip_pkt and ip_pkt.dst == self.vm_ip:
                # only forward if VM info is known
                if self.vm_ip in self.ip_to_host and self.vm_mac:
                    vm_mac = self.vm_mac
                    vm_port = self.ip_to_host[self.vm_ip][2]
                    actions = [parser.OFPActionOutput(vm_port)]

                    match = parser.OFPMatch(
                        eth_type=0x0800,
                        ipv4_dst=self.vm_ip,
                        ip_proto=17  # UDP
                    )

                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                    flow_mod = parser.OFPFlowMod(datapath=datapath, priority=50, match=match, instructions=inst)
                    datapath.send_msg(flow_mod)
            else:
                # VM not known yet, just flood or drop
                self.logger.info("VM not learned yet, flooding packet to discover VM")
                actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        
            if out_port != ofproto.OFPP_FLOOD: #and allow:
                priority_level = self.get_priority(pkt)
                template = f"priority_{priority_level}"
                #self.provision_async(template)

                meter_id = self.meter_id_map.get(priority_level, 3)                
                
                match = parser.OFPMatch(eth_dst=dst)
                inst = [parser.OFPInstructionMeter(meter_id, ofproto.OFPIT_METER),
                        parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                
                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    flow_mod = parser.OFPFlowMod(datapath=datapath,
                                              priority=10,
                                              match=match,
                                              instructions=inst,
                                              buffer_id=msg.buffer_id)
            
                else:
                    flow_mod = parser.OFPFlowMod(datapath=datapath,
                                              priority=10,
                                              match=match,
                                              instructions=inst)
                
                datapath.send_msg(flow_mod)
                      
            data = None if msg.buffer_id != ofproto.OFP_NO_BUFFER else msg.data
            packet_out = parser.OFPPacketOut(datapath=datapath,
                                             buffer_id=msg.buffer_id,
                                             in_port=in_port,
                                             actions=actions,
                                             data=data)
            datapath.send_msg(packet_out)
