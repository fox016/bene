import sys
import optparse
import numpy

import matplotlib
matplotlib.use('Agg')
from pylab import *

def find_first_index(value, array):
	for index in range(len(array)):
		if array[index] >= value:
			return index

def find_last_index(value, array):
	for index in range(len(array)-1, -1, -1):
		if array[index] <= value:
			return index
	return len(array)-1

# Read data from file
data = [line[:-1] for line in open("plot_data.txt", "r")]
cwnd_times = []
cwnd_sizes = []
receiver_times = []
receiver_sizes = []
for line in data:
	event,time,value,port = line.split(",")
	port = int(port)
	if event == "CWND":
		cwnd_times.append(time)
		cwnd_sizes.append(value)
	elif event == "R":
		receiver_times.append(float(time))
		receiver_sizes.append(int(value))

# Calculate receiver rates over time
rates = []
rate_times = numpy.arange(receiver_times[0], receiver_times[-1], 0.1)
for rate_time in rate_times:
	start_index = find_first_index(rate_time-1.0, receiver_times)
	end_index = find_last_index(rate_time, receiver_times)
	rates.append(sum(receiver_sizes[start_index:end_index+1]) / 1000.0)
#print(rates)

# Draw receiver rate graph
clf()
xlabel('Simulated Time (s)')
ylabel('Receiver Rate (kbps)')
plot(rate_times, rates, label='Receiver Rate')
savefig('graphs/new_receiver_rate.png')

# Draw queue size graph
"""
clf()
xlabel('Simulated Time (s)')
ylabel('Queue Size (packets)')
plot(queue_times, queue_sizes, label='Queue Size')
scatter(drop_times, drop_sizes, marker='x', color='r')
savefig('graphs/new_queue_size.png')
"""

# Draw congestion window graph
clf()
xlabel('Simulated Time (s)')
ylabel('Congestion Window (bytes)')
plot(cwnd_times, cwnd_sizes, label='Congestion Window')
savefig('graphs/new_cwnd.png')
