import sys
import optparse

import matplotlib
matplotlib.use('Agg')
from pylab import *

# Draw graph from file
'''
clf()
xlabel('# of times an RTO timer is set')
ylabel('RTO')
data = [line[:-1] for line in open("timeouts.txt", "r")]
rto_line = plot(xrange(len(data)), data, label='RTO')
savefig('timeout_graph.png')
'''

#Draw graphs from data
window_size = [1000, 2000, 5000, 10000, 15000, 20000]
queue_delay = [5.36, 2.67, 1.06, 0.53, 0.35, 0.26]
transfer_time = [10.71, 5.37, 2.15, 1.08, 0.73, 0.55]
clf()
xlabel('Window Size (bytes)')
ylabel('Throughput (Kbits / second)')
line = plot(window_size, map(lambda time: (514520 * 8) / time / 1000, transfer_time), label='Throughput')
savefig('graphs/throughput_graph.png')

clf()
xlabel('Window Size (bytes)')
ylabel('Average Queue Delay (seconds)')
line = plot(window_size, queue_delay, label='Queue Delay')
savefig('graphs/queue_delay_graph.png')
