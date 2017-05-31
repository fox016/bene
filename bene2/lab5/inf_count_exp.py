import sys
sys.path.append('..')

from src.sim import Sim
from src import node
from src import link
from src import packet
from routing import RoutingApp
from routing import SendingApp

from networks.network import Network

import optparse
import os
import subprocess

class Main(object):

	def __init__(self):
		self.parse_options()
		self.run()

	def parse_options(self):
		parser = optparse.OptionParser(usage = "%prog [options]", version = "%prog 0.1")
		parser.add_option("-r", "--runtime", type="int", dest="runtime", default=30)
		parser.add_option("-f", "--dvfrequency", type="int", dest="dvfrequency", default=5)
		(options,args) = parser.parse_args()
		self.runtime = options.runtime
		self.dv_frequency = options.dvfrequency

	def run(self):

		# parameters
		Sim.scheduler.reset()
		Sim.set_debug("DvRoutingHandler")
		Sim.set_debug("Node")

		# setup network
		net = Network('networks/five-nodes.txt')

		# get nodes
		n1 = net.get_node('n1')
		n2 = net.get_node('n2')
		n3 = net.get_node('n3')
		n4 = net.get_node('n4')
		n5 = net.get_node('n5')
		nodes = [n1, n2, n3, n4, n5]

		# setup protocol handlers
		for node in nodes:
			node.routing_handler = RoutingApp(node, self.dv_frequency)
			node.add_protocol(protocol='dvrouting', handler=node.routing_handler)
			node.add_protocol(protocol='senddata', handler=SendingApp(node))

		# set recurring timer to send routing messages
		for node in nodes:
			for delay in xrange(0, self.runtime, self.dv_frequency):
				Sim.scheduler.add(delay=delay, event=None, \
				handler=node.routing_handler.broadcast_dv)

		# set simulation end
		Sim.scheduler.add(delay=self.runtime, event=None, handler=lambda x: sys.exit())

		# send test data
		body = 'Hello, world!'

		p1 = packet.Packet(source_address=n1.get_address('n3'), destination_address=\
			n5.get_address('n3'), ttl=100, protocol='senddata', body=body)
		Sim.scheduler.add(delay=1, event=p1, handler=n1.send_packet)

		p2 = packet.Packet(source_address=n2.get_address('n1'), destination_address=\
			n4.get_address('n3'), ttl=100, protocol='senddata', body=body)
		Sim.scheduler.add(delay=2, event=p2, handler=n2.send_packet)

		p3 = packet.Packet(source_address=n5.get_address('n3'), destination_address=\
			n3.get_address('n5'), ttl=100, protocol='senddata', body=body)
		Sim.scheduler.add(delay=3, event=p3, handler=n5.send_packet)

		# bring down n3 - n5 link
		Sim.scheduler.add(delay=4, event=None, handler=n3.get_link('n5').down)
		Sim.scheduler.add(delay=4, event=None, handler=n5.get_link('n3').down)

		# run simulation
		Sim.scheduler.run()

if __name__ == '__main__':
    m = Main()
