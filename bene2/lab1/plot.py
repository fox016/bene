import sys
import optparse

import matplotlib
matplotlib.use('Agg')
from pylab import *

# Set up network variables
max_rate = 1000000.0/8000
mean_service_rate = 0.8 * max_rate

# Graph theory line
clf()
p = np.arange(0.0,1.0,0.01)
theory_line = plot(p,(1/(2*mean_service_rate))*(p/(1-p)), label='Theory')
xlabel('Utilization')
ylabel('Queuing Delay (s)')

# Graph experimental average
data = [line[:-1] for line in open("experiment_data.txt", "r")]
util = []
delay = []
list_num = []
for line in data:
	if line[0] is "U":
		util.append(float(line[6:]))
		if list_num:
			delay.append(sum(list_num) / len(list_num))
		list_num = []
	else:
		list_num.append(float(line))
delay.append(sum(list_num) / len(list_num))
average_line = plot(util, delay, label='Average')

# Draw graph
blue_line = Line2D([],[],color='blue',label='Theory')
green_line = Line2D([],[],color='green',label='Average')
legend(handles=[blue_line, green_line], loc=2)
savefig('graph.png')
