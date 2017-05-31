import sys
sys.path.append('..')

from src.sim import Sim
from src.node import Node
from src.link import Link
from src.transport import Transport
from tcp import TCP # Use local TCP implementation

from networks.network import Network

import optparse
import os
import subprocess

class AppHandler(object):
    def __init__(self,filename):
        self.filename = filename
        self.directory = 'received'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.f = open("%s/%s" % (self.directory,self.filename),'w')

    def receive_data(self,data):
        Sim.trace('AppHandler',"application got %d bytes" % (len(data)))
        self.f.write(data)
        self.f.flush()

class Main(object):
    def __init__(self):
        self.directory = 'received'
        self.parse_options()
        self.run()
        self.diff(self.filename)
        self.diff("2_"+self.filename)
        self.diff("3_"+self.filename)
        self.diff("4_"+self.filename)
        self.diff("5_"+self.filename)

    def parse_options(self):
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-f","--filename",type="str",dest="filename",
                          default='test.txt',
                          help="filename to send")

        parser.add_option("-l","--loss",type="float",dest="loss",
                          default=0.0,
                          help="random loss rate")

        (options,args) = parser.parse_args()
        self.filename = options.filename
        self.loss = options.loss

    def diff(self, new_filename):
        args = ['diff','-u',self.filename,self.directory+'/'+new_filename]
        result = subprocess.Popen(args,stdout = subprocess.PIPE).communicate()[0]
        print
        if not result:
            print "File transfer correct!"
        else:
            print "File transfer failed. Here is the diff:"
            print
            print result

    def run(self):
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug('AppHandler')
        Sim.set_debug('TCP')

        # setup network
        net = Network('test-network.txt')
        net.loss(self.loss)

        # setup routes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
        n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)

        # setup applications
        a = AppHandler(self.filename)
	b = AppHandler("2_"+self.filename)
	c = AppHandler("3_"+self.filename)
	d = AppHandler("4_"+self.filename)
	e = AppHandler("5_"+self.filename)

        # setup parallel connections
        c1 = TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a)
        c2 = TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a)
        c3 = TCP(t1,n1.get_address('n2'),2,n2.get_address('n1'),2,b)
        c4 = TCP(t2,n2.get_address('n1'),2,n1.get_address('n2'),2,b)
        c5 = TCP(t1,n1.get_address('n2'),3,n2.get_address('n1'),3,c)
        c6 = TCP(t2,n2.get_address('n1'),3,n1.get_address('n2'),3,c)
        c7 = TCP(t1,n1.get_address('n2'),4,n2.get_address('n1'),4,d)
        c8 = TCP(t2,n2.get_address('n1'),4,n1.get_address('n2'),4,d)
        c9 = TCP(t1,n1.get_address('n2'),5,n2.get_address('n1'),5,e)
        c10 = TCP(t2,n2.get_address('n1'),5,n1.get_address('n2'),5,e)

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)
                Sim.scheduler.add(delay=1.5, event=data, handler=c3.send)
                Sim.scheduler.add(delay=3.0, event=data, handler=c5.send)
                Sim.scheduler.add(delay=4.5, event=data, handler=c7.send)
                Sim.scheduler.add(delay=6.0, event=data, handler=c9.send)

        # run the simulation
        Sim.scheduler.run()

if __name__ == '__main__':
    m = Main()