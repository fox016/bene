import sys
sys.path.append('..')

import json

from src.sim import Sim
from src import node
from src import link
from src import packet

class RoutingApp(object):

	def __init__(self, node, dv_frequency):
		self.node = node
		self.dv_frequency = dv_frequency
		self.dv_table = {}
		self.neighbor_timers = {}
		self.neighbor_dv = {}
		self.destinations = set()
		for link in self.node.links:
			self.add_dv_entry(str(link.address), 0, None)
			self.destinations.add(str(link.address))

	def receive_packet(self, packet):
		Sim.trace("DvRoutingHandler", "host %s received dv message: %s" % \
			(self.node.hostname, packet.body))
		body_obj = json.loads(packet.body)
		self.start_neighbor_timer(body_obj['from'])
		self.update_dv(body_obj['from'], body_obj['dv_table'])

	def start_neighbor_timer(self, neighbor_node):
		self.cancel_neighbor_timer(neighbor_node)
		self.neighbor_timers[neighbor_node] = \
			Sim.scheduler.add(delay=3*self.dv_frequency, event=neighbor_node, \
			handler=self.detect_link_fail)

	def cancel_neighbor_timer(self, neighbor_node):
		if neighbor_node in self.neighbor_timers:
			if self.neighbor_timers[neighbor_node]:
				Sim.scheduler.cancel(self.neighbor_timers[neighbor_node])

	def update_dv(self, from_node, dv_table):
		self.neighbor_dv[from_node] = dv_table
		for dest_addr in dv_table:
			self.destinations.add(dest_addr)
		for destination in self.destinations:
			dist, next_hop = self.get_path(destination)
			if dist == float("inf") and destination in self.dv_table:
				self.dv_table.pop(destination)
				Sim.trace("DvRoutingHandler", "remove entry: host %s dv table: %s" % \
					(self.node.hostname, json.dumps(self.dv_table)))
				self.broadcast_dv()
			elif next_hop:
				did_update = self.add_dv_entry(destination, dist, next_hop)
				if did_update:
					self.broadcast_dv()

	def get_path(self, dest_addr):
		if dest_addr in self.dv_table and self.dv_table[dest_addr]['dist'] == 0:
			return 0, None
		min_dist, next_hop = float("inf"), None
		for neighbor in self.neighbor_dv:
			if dest_addr in self.neighbor_dv[neighbor]:
				dist = self.neighbor_dv[neighbor][dest_addr]['dist']+1
				if dist < min_dist:
					min_dist, next_hop = dist, neighbor
		return min_dist, next_hop

	def add_dv_entry(self, dest_addr, dist, next_hop):
		next_hop_change = False
		dist_change = False
		if dest_addr not in self.dv_table:
			next_hop_change = True
			dist_change = True
		else:
			next_hop_change = (self.dv_table[dest_addr]['next_hop'] != next_hop)
			dist_change = (self.dv_table[dest_addr]['dist'] != dist)
		self.dv_table[dest_addr] = {"dist": dist, "next_hop": next_hop}
		if dist_change or next_hop_change:
			Sim.trace("DvRoutingHandler", "add entry: host %s dv table: %s" % \
				(self.node.hostname, json.dumps(self.dv_table)))
		if next_hop_change and next_hop:
			self.update_forwarding_table(dest_addr, next_hop)
		return dist_change or next_hop_change

	def update_forwarding_table(self, dest_addr, next_hop):
		Sim.trace("DvRoutingHandler", "host %s update forwarding table (dest: %s, next hop: %s)" % \
			(self.node.hostname, dest_addr, next_hop))
		out_link = self.node.get_link(next_hop)
		self.node.add_forwarding_entry(address=int(dest_addr), link=out_link)

	def broadcast_dv(self, event=None):
		body_obj = {"from": self.node.hostname, "dv_table": self.dv_table}
		body_str = json.dumps(body_obj)
		p = packet.Packet(source_address=0, destination_address=0, ttl=1, protocol='dvrouting', \
			body=body_str, length=len(body_str))
		Sim.scheduler.add(delay=0, event=p, handler=self.node.send_packet)

	def detect_link_fail(self, bad_node):
		Sim.trace("DvRoutingHandler", "host %s detected failed link to host %s" % \
			(self.node.hostname, bad_node))
		self.neighbor_dv.pop(bad_node, None)
		self.neighbor_timers.pop(bad_node, None)

class SendingApp(object):

	def __init__(self, node):
		self.node = node

	def receive_packet(self, packet):
		Sim.trace("DvRoutingHandler", "host %s received data: %s" % (self.node.hostname, packet.body))
