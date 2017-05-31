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
	net = Network('../networks/one-hop.txt')

	# setup routes
	n1 = net.get_node('n1')
	n2 = net.get_node('n2')
	link_1_2 = n1.links[0]
	link_2_1 = n2.links[0]
	n1.add_forwarding_entry(address=n2.get_address('n1'), link=link_1_2)
	n2.add_forwarding_entry(address=n1.get_address('n2'), link=link_2_1)

	# setup app
	d = DelayHandler()
	net.nodes['n2'].add_protocol(protocol="delay",handler=d)

	# send packets
	link_1_2.bandwidth = 1000000.0
	link_1_2.propagation = 0.010
	p1 = packet.Packet(destination_address=n2.get_address('n1'),ident=1,protocol='delay',length=1000)
	p2 = packet.Packet(destination_address=n2.get_address('n1'),ident=2,protocol='delay',length=1000)
	p3 = packet.Packet(destination_address=n2.get_address('n1'),ident=3,protocol='delay',length=1000)
	p4 = packet.Packet(destination_address=n2.get_address('n1'),ident=4,protocol='delay',length=1000)
	Sim.scheduler.add(delay=0, event=p1, handler=n1.send_packet)
	Sim.scheduler.add(delay=0, event=p2, handler=n1.send_packet)
	Sim.scheduler.add(delay=0, event=p3, handler=n1.send_packet)
	Sim.scheduler.add(delay=2, event=p4, handler=n1.send_packet)

	# run the simulation
	Sim.scheduler.run()
