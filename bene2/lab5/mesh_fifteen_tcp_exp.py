import sys
sys.path.append('..')

from src.sim import Sim
from src import node
from src import link
from src.transport import Transport
from tcp import TCP # Use local TCP implementation
from src import packet
from routing import RoutingApp

from networks.network import Network

import optparse
import os
import subprocess

class AppHandler(object):
    def __init__(self,filename):
        self.filename = filename
        self.directory = 'received'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.f = open("%s/%s" % (self.directory,self.filename),'w')

    def receive_data(self,data):
        Sim.trace('AppHandler',"application got %d bytes" % (len(data)))
        self.f.write(data)
        self.f.flush()

class Main(object):

	def __init__(self):
		self.parse_options()
		self.filename = 'test_mesh.txt'
		self.run()

	def parse_options(self):
		parser = optparse.OptionParser(usage = "%prog [options]", version = "%prog 0.1")
		parser.add_option("-r", "--runtime", type="int", dest="runtime", default=29)
		parser.add_option("-f", "--dvfrequency", type="int", dest="dvfrequency", default=5)
		(options,args) = parser.parse_args()
		self.runtime = options.runtime
		self.dv_frequency = options.dvfrequency

	def run(self):

		# parameters
		Sim.scheduler.reset()
		Sim.set_debug("DvRoutingHandler")
		Sim.set_debug("Node")
		Sim.set_debug('AppHandler')
		Sim.set_debug('TCP')

		# setup network
		net = Network('networks/fifteen-nodes.txt')

		# get nodes
		n1 = net.get_node('n1')
		n2 = net.get_node('n2')
		n3 = net.get_node('n3')
		n4 = net.get_node('n4')
		n5 = net.get_node('n5')
		n6 = net.get_node('n6')
		n7 = net.get_node('n7')
		n8 = net.get_node('n8')
		n9 = net.get_node('n9')
		n10 = net.get_node('n10')
		n11 = net.get_node('n11')
		n12 = net.get_node('n12')
		n13 = net.get_node('n13')
		n14 = net.get_node('n14')
		n15 = net.get_node('n15')
		nodes = [n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15]

		# setup network limits
		for node in nodes:
			for link in node.links:
				link.bandwidth = 10000000.0
				link.queue_size = 25

		# setup protocol handlers
		for node in nodes:
			node.routing_handler = RoutingApp(node, self.dv_frequency)
			node.add_protocol(protocol='dvrouting', handler=node.routing_handler)

		# setup TCP
		t10 = Transport(n10)
		t15 = Transport(n15)
		a = AppHandler(self.filename)
		c10 = TCP(t10, n10.get_address('n1'), 1, n15.get_address('n14'), 1, a)
		c15 = TCP(t15, n15.get_address('n14'), 1, n10.get_address('n1'), 1, a)

		# set recurring timer to send routing messages
		for node in nodes:
			for delay in xrange(0, self.runtime, self.dv_frequency):
				Sim.scheduler.add(delay=delay, event=None, \
				handler=node.routing_handler.broadcast_dv)

		# set simulation end
		Sim.scheduler.add(delay=self.runtime, event=None, handler=lambda x: sys.exit())

		# send test data
		with open(self.filename, 'r') as f:
			while True:
				data = f.read(1000)
				if not data:
					break
				Sim.scheduler.add(delay=1, event=data, handler=c10.send)
				Sim.scheduler.add(delay=21, event=data, handler=c10.send)
				Sim.scheduler.add(delay=26, event=data, handler=c10.send)

		# bring down n1 - n2 link and resend data
		Sim.scheduler.add(delay=2, event=None, handler=n1.get_link('n2').down)
		Sim.scheduler.add(delay=2, event=None, handler=n2.get_link('n1').down)

		# bring up n1 - n2 link and resend data
		Sim.scheduler.add(delay=23, event=None, handler=n1.get_link('n2').up)
		Sim.scheduler.add(delay=23, event=None, handler=n2.get_link('n1').up)

		# run simulation
		Sim.scheduler.run()

if __name__ == '__main__':
    m = Main()
