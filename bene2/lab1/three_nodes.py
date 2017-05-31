import sys
sys.path.append('..')

from src.sim import Sim
from src import node
from src import link
from src import packet

from networks.network import Network

import random

class DelayHandler(object):
	def receive_packet(self,packet):
		#print Sim.scheduler.current_time(),packet.ident,packet.created,Sim.scheduler.current_time() - packet.created,packet.transmission_delay,packet.propagation_delay,packet.queueing_delay
		print packet.created, packet.ident, Sim.scheduler.current_time()


if __name__ == '__main__':

	# parameters
	Sim.scheduler.reset()

	# setup network
	net = Network('three-nodes.txt')

	# setup routes
	n1 = net.get_node('n1')
	n2 = net.get_node('n2')
	n3 = net.get_node('n3')
	link_1_2 = n1.links[0]
	link_2_3 = n2.links[1]
	n1.add_forwarding_entry(address=n2.get_address('n1'), link=link_1_2)
	n1.add_forwarding_entry(address=n3.get_address('n2'), link=link_1_2)
	n2.add_forwarding_entry(address=n3.get_address('n2'), link=link_2_3)
	n2.add_forwarding_entry(address=n1.get_address('n2'), link=n2.links[0])
	n3.add_forwarding_entry(address=n2.get_address('n3'), link=n3.links[0])

	# setup app
	d = DelayHandler()
	n1.add_protocol(protocol="delay",handler=d)
	n2.add_protocol(protocol="delay",handler=d)
	n3.add_protocol(protocol="delay",handler=d)

	# send packets
	link_1_2.bandwidth = 1000000000.0
	link_2_3.bandwidth = 1000000000.0
	link_1_2.propagation = 0.100
	link_2_3.propagation = 0.100
	for i in xrange(1000):
		p = packet.Packet(source_address=n1.get_address('n2'),destination_address=n3.get_address('n2'),ident=i,protocol='delay',length=1000)
		Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)

	# run the simulation
	Sim.scheduler.run()
