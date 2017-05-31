import sys
sys.path.append('..')

from src.sim import Sim
from src.connection import Connection
from src.tcppacket import TCPPacket
from src.buffer import SendBuffer,ReceiveBuffer
from rtt import RoundTripTimer

class TCP(Connection):
	''' A TCP connection between two hosts.'''
	def __init__(self,transport,source_address,source_port, \
		destination_address,destination_port,app=None):

		Connection.__init__(self,transport,source_address,source_port, \
			destination_address,destination_port,app)

		Sim.set_debug("Link")

		### Sender functionality

		# send buffer
		self.send_buffer = SendBuffer()
		# maximum segment size, in bytes
		self.mss = 1000
		# largest sequence number that has been ACKed so far; represents
		# the next sequence number the client expects to receive
		self.sequence = 0
		# send window; represents the total number of bytes that may
		# be outstanding at one time
		self.cwnd = self.mss
		# slow start threshold; represents the window size at which slow
		# start stops and additive increase begins
		self.ssthresh = 100000
		# retransmission timer
		self.timer = None
		# EWMA timer
		self.rtt = RoundTripTimer()
		# ACK counter
		self.ack_count = 0

		### Receiver functionality

		# receive buffer
		self.receive_buffer = ReceiveBuffer()
		# ack number to send; represents the largest in-order sequence
		# number not yet received (largest ack sent so far by the 
		# receiver)
		self.ack = 0

	def trace(self,message):
		''' Print debugging messages. '''
		Sim.trace("TCP",message)

	def receive_packet(self,packet):
		''' Receive a packet from the network layer. '''
		if packet.ack_number > 0:
			# handle ACK
			self.handle_ack(packet)
		if packet.length > 0:
			# handle data
			self.handle_data(packet)

	''' Sender '''

	def send(self,data):
		''' Send data on the connection. Called by the application. This
			code currently sends all data immediately. '''
		self.send_buffer.put(data)
		self.send_available()

	def send_available(self):

		# While there is available data within the window
		while (self.send_buffer.available() is not 0) and \
		(self.send_buffer.outstanding() + self.mss <= self.cwnd):

			# Get the largest amout of data allowed
			tcp_packet, start_sequence = self.send_buffer.get(self.mss)

			# Record send time for RTT estimate
			self.rtt.record_send_time(start_sequence, len(tcp_packet), \
				Sim.scheduler.current_time())

			# Send packet
			self.send_packet(tcp_packet, start_sequence)

	def send_packet(self,data,sequence):
		packet = TCPPacket(source_address=self.source_address,
			   source_port=self.source_port,
			   destination_address=self.destination_address,
			   destination_port=self.destination_port,
			   body=data,
			   sequence=sequence,ack_number=self.ack)

		# send the packet
		self.trace("%s (%d) sending TCP segment to %d for %d" % \
			(self.node.hostname,self.source_address,\
			self.destination_address,packet.sequence))
		self.transport.send_packet(packet)

		# set a timer
		if not self.timer:
			self.timer = Sim.scheduler.add(delay=self.rtt.get_timeout(), \
				event='retransmit', handler=self.retransmit)

	def handle_ack(self,packet):
		''' Handle an incoming ACK. '''

		self.trace("%s (%d) received TCP ACK from %d for %d" % \
			(self.node.hostname, packet.destination_address, \
			packet.source_address, packet.ack_number))

		# If new ACK
		if packet.ack_number > self.sequence:

			# Record ACK time for RTT estimate
			self.rtt.record_ack_time(packet.ack_number, \
				Sim.scheduler.current_time())

			# Restart timer
			self.cancel_timer()
			self.timer = Sim.scheduler.add(delay=self.rtt.get_timeout(), \
				event='retransmit', handler=self.retransmit)

			# Update congestion window
			self.ack_count = 0
			new_bytes = self.mss
			if self.cwnd < self.ssthresh:
				self.trace("CWND,%f,%d,%d\n" % (Sim.scheduler.current_time(), self.cwnd, self.source_port))
				self.cwnd += new_bytes
			else:
				self.trace("CWND,%f,%d,%d\n" % (Sim.scheduler.current_time(), self.cwnd, self.source_port))
				self.cwnd += self.mss * new_bytes / self.cwnd

			# Update self.sequence (largest sequence number ACKed so far)
			self.sequence = packet.ack_number
		
			# Update buffer
			self.send_buffer.slide(packet.ack_number)

			# If all outstanding data is acknowledged, cancel timer
			if self.send_buffer.outstanding() == 0:
				self.cancel_timer()

			# Send available data
			self.send_available()

		# If repeat ACK
		elif packet.ack_number == self.sequence:
			self.ack_count += 1
			if self.ack_count == 3: # 3 dup => retransmit
				self.trace("3 duplicate ACKs (ACK# %d)" % packet.ack_number)
				self.do_retransmit()

	def retransmit(self,event):
		''' Retransmit data. '''
		self.trace("%s (%d) retransmission timer fired" % \
			(self.node.hostname,self.source_address))

		# Clear RTT clock send times, perform exponential backoff
		self.rtt.clear_send_times()
		self.rtt.exponential_backoff()

		# Restart timer to expire after RTO seconds
		self.timer = Sim.scheduler.add(delay=self.rtt.get_timeout(), \
			event='retransmit', handler=self.retransmit)

		# Retransmit
		self.do_retransmit()

	def do_retransmit(self):

		# Set ssthresh and cwnd
		self.ssthresh = max(self.cwnd/2, self.mss)
		self.cwnd = self.mss
		self.trace("CWND,%f,%d,%d\n" % (Sim.scheduler.current_time(), self.cwnd, self.source_port))

		# Resend earliest unACKed segment
		tcp_packet, start_sequence = self.send_buffer.resend(self.mss)
		if len(tcp_packet) == 0:
			self.cancel_timer()
		else:
			self.send_packet(tcp_packet, start_sequence)
	
	def cancel_timer(self):
		''' Cancel the timer. '''
		if not self.timer:
			return
		Sim.scheduler.cancel(self.timer)
		self.timer = None

	''' Receiver '''

	def handle_data(self,packet):
		''' Handle incoming data. This code currently gives all data to
		the application, regardless of whether it is in order, and sends
		an ACK.'''
		self.trace("%s (%d) received TCP segment from %d for %d" % \
			(self.node.hostname,packet.destination_address,\
			packet.source_address,packet.sequence))

		self.trace("R,%f,%d,%d" % (Sim.scheduler.current_time(), packet.length * 8, self.source_port))

		# Put packet in buffer
		self.receive_buffer.put(packet.body, packet.sequence)

		# Send all ordered data to the application
		ordered_data, start_sequence = self.receive_buffer.get()
		self.app.receive_data(ordered_data)

		# Update ACK value and send ACK
		self.ack = start_sequence + len(ordered_data)
		self.send_ack()

	def send_ack(self):
		''' Send an ack. '''
		packet = TCPPacket(source_address=self.source_address,
				   source_port=self.source_port,
				   destination_address=self.destination_address,
				   destination_port=self.destination_port,
				   sequence=self.sequence,ack_number=self.ack)

		# send the packet
		self.trace("%s (%d) sending TCP ACK to %d for %d" % \
			(self.node.hostname,self.source_address,\
			self.destination_address,packet.ack_number))
		self.transport.send_packet(packet)
