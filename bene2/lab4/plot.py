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

connections = int(sys.argv[1])

# Read data from file
data = [line[:-1] for line in open("plot_data.txt", "r")]
queue_times = []
queue_sizes = []
drop_times = []
drop_sizes = []
cwnd_times = []
cwnd_sizes = []
receiver_times = []
receiver_sizes = []
for i in range(connections):
	cwnd_times.append(list())
	cwnd_sizes.append(list())
	receiver_times.append(list())
	receiver_sizes.append(list())
for line in data:
	event,time,value,port = line.split(",")
	port = int(port)
	if event == "Q":
		queue_times.append(time)
		queue_sizes.append(value)
	elif event == "X":
		drop_times.append(time)
		drop_sizes.append(int(value)+1)
	elif event == "CWND":
		cwnd_times[port-1].append(time)
		cwnd_sizes[port-1].append(value)
	elif event == "R":
		receiver_times[port-1].append(float(time))
		receiver_sizes[port-1].append(int(value))

# Calculate receiver rates over time
rates = []
rate_times = []
for i in range(connections):
	rates.append(list())
	rate_times.append(numpy.arange(receiver_times[i][0], receiver_times[i][-1], 0.1))
for index in range(len(receiver_times)):
	rate_time_list = rate_times[index]
	for rate_time in rate_time_list:
		start_index = find_first_index(rate_time-1.0, receiver_times[index])
		end_index = find_last_index(rate_time, receiver_times[index])
		rates[index].append(sum(receiver_sizes[index][start_index:end_index+1]) / 1000.0)

# Draw receiver rate graph
clf()
xlabel('Simulated Time (s)')
ylabel('Receiver Rate (kbps)')
for index in range(len(rates)):
	plot(rate_times[index], rates[index], label='Receiver Rate')
savefig('graphs/new_receiver_rate.png')

# Draw queue size graph
clf()
xlabel('Simulated Time (s)')
ylabel('Queue Size (packets)')
plot(queue_times, queue_sizes, label='Queue Size')
scatter(drop_times, drop_sizes, marker='x', color='r')
savefig('graphs/new_queue_size.png')

# Draw congestion window graph
clf()
xlabel('Simulated Time (s)')
ylabel('Congestion Window (bytes)')
for index in range(len(cwnd_times)):
	plot(cwnd_times[index], cwnd_sizes[index], label='Congestion Window')
savefig('graphs/new_cwnd.png')
