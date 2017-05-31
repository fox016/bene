class RoundTripTimer(object):
	
	def __init__(self):
		self.samples = {}
		self.rto = 1
		self.estimated_rtt = 1
		self.dev_rtt = 0
		self.alpha = 0.125
		self.beta = 0.25
		self.max_rto = 60

	def get_timeout(self):
		self.rto = min(self.rto, self.max_rto)
		return self.rto

	def record_send_time(self, sequence, length, time):
		self.samples[sequence+length] = time

	def record_ack_time(self, ack, time):
		if ack not in self.samples:
			return
		sample_rtt = time - self.samples[ack]
		self._update_estimates(sample_rtt)

	def exponential_backoff(self):
		self.rto = self.rto * 2

	def clear_send_times(self):
		self.samples = {}

	def _update_estimates(self, sample_rtt):
		self.estimated_rtt = ((1 - self.alpha) * self.estimated_rtt) + \
			(self.alpha * sample_rtt)
		self.dev_rtt = ((1 - self.beta) * self.dev_rtt) + \
			(self.beta * abs(sample_rtt - self.estimated_rtt))
		self.rto = self.estimated_rtt + (4 * self.dev_rtt)
