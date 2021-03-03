from mininet.cli import CLI
from mininet.examples.linuxrouter import LinuxRouter
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

"""
        LAN Network Address: 192.168.1.0/24
        WAN Network Address: 10.0.1.0/24

        Topo:
                    |Router|
                      /\
                    /   \
                   /     \
            |Switch1|   |Switch2|
                /\          |
               /  \     |Client_W|
              /    \
        |Client_L| |Controller|
        
"""


class SimpleTestTopo(Topo):
    def build(self):
        """
        Build a simple Testbed for Routers
        """
        router = self.addNode('router', cls=LinuxRouter, ip='192.168.1.1/24')

        switch1 = self.addSwitch('switch1')
        switch2 = self.addSwitch('switch2')

        client_l = self.addHost('client_l', ip='192.168.1.164/24', defaultRoute='via 192.168.1.1', intf='eth0')
        client_w = self.addHost('client_w', ip='10.0.1.100/24', defaultRoute='via 10.0.1.1', intf='eth0')

        controller = self.addHost('controller', ip='192.168.1.200/24', defaultRoute='via 192.168.1.1', intf='eth0')

        self.addLink(switch1, router, intfName='r0-eth1', params2={'ip': '192.168.1.1/24'})
        self.addLink(switch2, router, intfName='r0-eth2', params2={'ip': '10.0.1.1/24'})

        self.addLink(client_l, switch1)
        self.addLink(client_w, switch2)

        self.addLink(controller, switch1)


def simple_test():
    """Create and test a simple network"""
    topo = SimpleTestTopo()
    net = Mininet(topo=topo)
    net.start()
    print("Dumping host connections")
    dumpNodeConnections(net.hosts)
    print("Testing network connectivity")
    net.pingAll()
    CLI(net)


if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    simple_test()
