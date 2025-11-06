#Our future controller
#Run the controller: sudo -E ~/venv-ryu39/bin/ryu-manager --ofp-tcp-listen-port 6653 ./sdn_controller.py --verbose

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types
from ryu.lib.mac import haddr_to_bin

class LearningSwitch(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

        def __init__(self, *args, **kwargs):
            super(LearningSwitch, self).__init__(*args, **kwargs)
            self.mac_to_port = {}
            
            #Prioritites for later. Think that priority 1 is a drone looking for people
            #and prio 3 is a media drone
            self.drone_priority = {
                "10.0.0.2": 1,
                "10.0.0.3": 2,
                "10.0.0.4": 3,
                "10.0.0.5": 3,
                "10.0.0.6": 3
                }

        @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
        def switch_feature_handler(self, ev):
            #Default rule, all unknown packages are sent to the controller
            #Datapath represents a "switch"
            datapath = ev.msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            match = parser.OFPMatch()
        #THis catches all packages: Later its possible to use eg
        #paerser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_dst="10.0.0.2")

            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                             ofproto.OFPCML_NO_BUFFER)]
        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                  actions)]
        
            mod = parser.OFPFlowMod(datapath=datapath, priority=0,
                                    match=match, instructions=inst)

            datapath.send_msg(mod)
        
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
            if eth.ethertype == 0x88cc:
                return
                
            dst = eth.dst
            src = eth.src
            in_port = msg.match['in_port']
            
            self.mac_to_port.setdefault(dpid, {})
            

            self.mac_to_port[dpid][src] = in_port
            self.logger.info("Switch %s learned %s is at port %s", dpid, src, in_port)

                
                
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
            else:
                out_port = ofproto.OFPP_FLOOD
                
            actions = [parser.OFPActionOutput(out_port)]
                
           
            
            if out_port != ofproto.OFPP_FLOOD:
                match = parser.OFPMatch(eth_dst=dst)
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                
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