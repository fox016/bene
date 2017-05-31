import sys
sys.path.append('..')

from src.sim import Sim
from src import node
from src import link
from src import packet

from networks.network import Network

import random

class Generator(object):
	def __init__(self,node,destination,load,duration):
		self.node = node
		self.load = load
		self.duration = duration
		self.destination = destination
		self.start = 0
		self.ident = 1

	def handle(self,event):
		# quit if done
		now = Sim.scheduler.current_time()
		if (now - self.start) > self.duration:
			return

		# generate a packet
		self.ident += 1
		p = packet.Packet(destination_address=self.destination,ident=self.ident,protocol='delay',length=1000)
		Sim.scheduler.add(delay=0, event=p, handler=self.node.send_packet)
		# schedule the next time we should generate a packet
		Sim.scheduler.add(delay=random.expovariate(self.load), event='generate', handler=self.handle)

class DelayHandler(object):
	def receive_packet(self,packet):
		print packet.queueing_delay

def write_queue_average(util):
	
	print "UTIL:", util

	# reset scheduler
	Sim.scheduler.reset()

	# setup network
	net = Network('../networks/one-hop.txt')

	# setup routes
	n1 = net.get_node('n1')
	n2 = net.get_node('n2')
	n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
	n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])

	# setup app
	d = DelayHandler()
	net.nodes['n2'].add_protocol(protocol="delay",handler=d)

	# setup packet generator
	destination = n2.get_address('n1')
	max_rate = 1000000/(1000*8)
	load = util * max_rate
	g = Generator(node=n1,destination=destination,load=load,duration=20)
	Sim.scheduler.add(delay=0, event='generate', handler=g.handle)
	
	# run the simulation
	Sim.scheduler.run()

utils = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.95,0.98]
for util in utils:
	write_queue_average(util)
