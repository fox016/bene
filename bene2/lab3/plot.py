import sys
import optparse

import matplotlib
matplotlib.use('Agg')
from pylab import *

doMod = True

# Draw graph from file
clf()
xlabel('Simulated Time')
ylabel('Sequence Number')
data = [line[:-1] for line in open("sequence_plot_data.txt", "r")]
send_times = []
send_packets = []
ack_times = []
ack_packets = []
drop_times = []
drop_packets = []
for point in data:
	event,a,b = point.split(",")
	if doMod:
		b = str(int(b) % 50)
	if event == "D":
		send_times.append(a)
		send_packets.append(b)
	elif event == "A":
		ack_times.append(a)
		ack_packets.append(b)
	elif event == "X":
		drop_times.append(a)
		drop_packets.append(b)
scatter(send_times, send_packets, marker='s', s=3)
scatter(ack_times, ack_packets, marker='o', s=0.2)
scatter(drop_times, drop_packets, marker='x')
savefig('sequence_plot.png')
