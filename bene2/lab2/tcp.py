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
		destination_address,destination_port,app=None,window=3000):

		print "INIT LOCAL TCP ( source =", source_address, \
			", destination =", destination_address, ", window =", \
			window, ")"

		Connection.__init__(self,transport,source_address,source_port, \
			destination_address,destination_port,app)

		### Sender functionality

		# send window; represents the total number of bytes that may
		# be outstanding at one time
		self.window = window
		# send buffer
		self.send_buffer = SendBuffer()
		# maximum segment size, in bytes
		self.mss = 1000
		# largest sequence number that has been ACKed so far; represents
		# the next sequence number the client expects to receive
		self.sequence = 0
		# retransmission timer
		self.timer = None
		# EWMA timer
		self.rtt = RoundTripTimer()

		### Receiver functionality

		# receive buffer
		self.receive_buffer = ReceiveBuffer()
		# ack number to send; represents the largest in-order sequence
		# number not yet received (largest ack sent so far by the 
		# receiver)
		self.ack = 0

		self.queue_file = open("queue_delay.txt", "w")

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
		(self.send_buffer.outstanding() + self.mss <= self.window):

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

		self.queue_file.write(str(Sim.scheduler.current_time()) + "\n")

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

		self.trace("%s (%d) received TCP ack from %d for %d" % \
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

			# Update self.sequence (largest sequence number ACKed so far)
			self.sequence = packet.ack_number
		
			# Update buffer
			self.send_buffer.slide(packet.ack_number)

			# If all outstanding data is acknowledged, cancel timer
			if self.send_buffer.outstanding() == 0:
				self.cancel_timer()

		# Send available data
		self.send_available()

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

		# Resend earliest unACKed segment
		tcp_packet, start_sequence = self.send_buffer.resend(self.mss)
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

		print "QUEUEING DELAY", packet.queueing_delay

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
