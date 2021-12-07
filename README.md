Final Project - Routing, Topology & Firewall
========

## Project Details
Using Mininet and Python POX controller, this project demenstrates the use of OpenFlow in Software Defined Network(SDN) by implementing customized topology and static layer-3 forwarder/switch.  
Furthermore for security concerns, Firewall can also be built with specific configurations and even do basic layer-4 tasks with OpenFlow.  
With OpenFlow-enabled coding, the network is effectively layerless: you can mix switch, router, and higher-layer functionality.  

## Implementation Coding and Testing

### Router Exercise
1. ```sh mytopo.py ```
store in   
```sh 
home/mininet/mininet
```
run directly with 
```sh 
sudo mn --custom mytopo.py --topo mytopo --mac  --controller remote
```


2.```sh router.py ```
store in  
```sh 
home/mininet/pox/ext
```
go to ```sh  home/mininet/pox ``` and run with  
```sh 
./pox.py log.level --DEBUG router misc.full_payload
```


## Advanced Topology

3. ```sh advancedTopo.py ```
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

No specific code is needed.  

## Contribution: 100% by Qingge Li

## Encoutered Problems
Flooding packets with infinite loop  
