#Our future controller
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0

class LearningSwitch(app_manager.RyuApp):
        OFP_VERSION = [ofproto_v1_0.OFP_VERSION]

        def __init__(self, *args, **kwargs):
                super(LearingSwitch, self).__init__(*args, **kwargs)
		self.mac_to_port = {}

        @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def switch_feature_handler(self, ev):
	#Default rule, all unknown packages are sent to the controller
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		match = parser.OFPMatch()
		#THis catches all packages: Later its possible to use eg
		#paerser.OFPMatch(in_port=1, eth_type=0x0800, ipv4_dst="10.0.0.2")

		actions = [parser.OFPAcionOutput(ofproto.OFPP_CONTROLLER,
						ofproto.OFPCML_NO_BUFFER)]
		inst = [parser.OFPInstructionAnctions(ofproto.OFPIT_APPLY_ACTIONS,
								actions)]
		mod = parser.OFPFlowMod(datapath=datapath, priority=0,
					match=match, instructions=inst)

		datapath.send_msg(mod)

        def packet_in_handler(self, ev):
                msg = ev.msg
                datapath = msg.datapath
                dpid = datapath.id
		
