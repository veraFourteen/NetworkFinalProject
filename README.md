Final Project - Routing, Topology & Firewall
========

## Project Details
Using Mininet and Python POX controller, this project demenstrates the use of OpenFlow in Software Defined Network(SDN) by implementing customized topology and static layer-3 forwarder/switch.  
Furthermore for security concerns, Firewall can also be built with specific configurations and even do basic layer-4 tasks with OpenFlow.  
With OpenFlow-enabled coding, the network is effectively layerless: you can mix switch, router, and higher-layer functionality.  

## Implementation Coding and Testing

### Router Exercise
1. ``` mytopo.py ```
store in   
```sh 
home/mininet/mininet
```
run directly with 
```sh 
sudo mn --custom mytopo.py --topo mytopo --mac  --controller remote
```


2.``` router.py ```
store in  
```sh 
home/mininet/pox/ext
```
go to ```  home/mininet/pox ``` and run with  
```sh 
./pox.py log.level --DEBUG router misc.full_payload
```


### Advanced Topology

3. ``` advancedTopo.py ```
store in 
```sh 
home/mininet/mininet
```
run with 
```sh 
sudo mn --custom advancedTopo.py --topo mytopo --mac  --controller remote
```

Debug information are included as logs of POX and will be displayed while running the POX controller  

### Firewall

#### requirement
To run iperf on xterms, on the xterm for h2, start up a server:
``` iperf -s```
Then on the xterm for h3 start up a client:
``` iperf -c 10.0.0.2```
Your task is to prevent this from happening, and to block all flow entries with this particular port.

#### solution

```sh
class Firewall(object):
    
    def __init__(self, connection):
        self.connection = connection 
        connection.addListeners(self)
        
        self.port_table = {{'10.0.1.100': 1,
                        '10.0.2.100': 3,
                        '10.0.3.100': 2}
        
    def _handle_PacketIn(self, event):
        packet = event.parsed
        dst = packet.dst
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.actions.append(of.ofp_action_output(port=self.por_table[str(dst)]))
        msg.data = event.ofp 
        self.connection.send(msg)
        self.port_table[str(packet.src)] = event.port
        
def launch():
    def myfirewall(event):
        Firewall(event.connection)
        core.openflow.addListenerByName("PacketIn", myfirewall)

```

## Contribution: 100% by Qingge Li

## Encoutered Problems
Flooding packets with infinite loop  
