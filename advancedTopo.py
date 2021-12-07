"""Custom topology by Qingge Li

Three hosts and one switch connecting the three host.

   host --- switch --- switch --- host 
              |
             host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""
from mininet.topo import Topo

class AdvancedTopo( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        # Add hosts and switches
        thirdHost = self.addHost( 'h3' )
        fourthHost = self.addHost( 'h4' )
        fifthHost = self.addHost( 'h5' )
        firstswitch = self.addSwitch( 's1' )
        secondSwitch = self.addSwitch( 's2' )

        # Add links
        self.addLink( firstswitch, thirdHost )
        self.addLink( firstswitch, fourthHost )
        self.addLink( firstswitch, secondSwitch )
        self.addLink( secondSwitch, fifthHost )

        # Set Up Hosts
        thirdHost = self.addHost('h3', ip='10.0.1.2/24', defaultRoute='via 10.0.1.1')
        fourthHost = self.addHost('h4', ip='10.0.1.3/24', defaultRoute='via 10.0.1.1')
        fifthHost = self.addHost('h5', ip='10.0.2.2/24', defaultRoute='via 10.0.2.1')


topos = {'advancedtopo' : (lambda: AdvancedTopo())}