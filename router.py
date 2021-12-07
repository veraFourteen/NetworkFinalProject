from pox.core import core
from pox.lib.packet import ethernet, arp, ipv4, icmp
from pox.lib.addresses import IPAddr, EthAddr
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.packet.ethernet import ETHER_BROADCAST
import pox


log = core.getLogger()

class Router(object):
    ''' Router that acts like a static layer-3 forwarder/switch with masked IP prefix ranges
    '''
    def __init__(self, connection):
        self.connection = connection 
        connection.addListeners(self)

        # ARP table with made up MAC address
        self.arp_table = {'10.0.1.1': '01:01:01:01:01:01',
                        '10.0.2.1': '02:02:02:02:02:02',
                        '10.0.3.1': '03:03:03:03:03:03'}

        # ip to port dictionary
        self.port_table = {'10.0.1.100': 1,
                        '10.0.2.100': 3,
                        '10.0.3.100': 2}

        # message queue format:  {destinationIP : [IP packet, sourceMAC]}
        self.msg_queue = {}

        # routing table: network, ip of host, interface name, interface address, switch port
        self.rtable = [['10.0.1.0/24', '10.0.1.100', 's1-eth1', '10.0.1.1', 1],
                    ['10.0.2.0/24', '10.0.2.100', 's1-eth2', '10.0.2.1', 3],
                    ['10.0.3.0/24', '10.0.3.100', 's1-eth3', '10.0.3.1', 2]]


    def _handle_PacketIn(self, event):
        ''' Required function for OpenFlow to look up.
        Catagorize input packets received from the router to ARP and IP type.
        '''
        log.debug('Receving packets...')
        ether_pkt = event.parsed

        if ether_pkt.type == ethernet.ARP_TYPE:
            self.handle_arp_pkt(event, ether_pkt.payload)
        elif ether_pkt.type == ethernet.IP_TYPE:
            self.handle_ip_pkt(event, ether_pkt)


    def handle_arp_pkt(self, event, arp_pkt):
        ''' For ARP REPLY received by the router: updata ARP table and send buffered IP packet if any
        For ARP_REQUEST received by the router: send reply to source with MAC address I know.
        '''

        if arp_pkt.opcode == arp.REPLY:
            log.debug('--ARP Reply received--')
            log.debug(arp_pkt)

            # update ARP table
            if str(arp_pkt.protosrc) not in self.arp_table.keys():
                self.arp_table[str(arp_pkt.protosrc)] = str(arp_pkt.hwsrc)
                log.debug(self.arp_table)
                log.debug(self.msg_queue)

            # check msg_queue and send out any ip packets with given MAC
            dstip = str(arp_pkt.protosrc) 
            if dstip in self.msg_queue.keys(): 
                
                ether = ethernet()
                ether.type = ethernet.IP_TYPE
                ether.payload = self.msg_queue[dstip][0]
                ether.src = EthAddr(self.msg_queue[dstip][1])
                ether.dst = EthAddr(self.arp_table[dstip])
                self.send_pkt(ether, self.port_table[dstip])
                del self.msg_queue[dstip] # clean up msg_queue
                log.debug('--IP packet sent--')
                log.debug(ether)

        elif arp_pkt.opcode == arp.REQUEST:
            log.debug('--ARP Request received--')
            log.debug(arp_pkt)
            if str(arp_pkt.protodst) in self.arp_table.keys():
                # construct ARP reply
                arp_reply = arp()
                arp_reply.hwsrc = EthAddr(self.arp_table[str(arp_pkt.protodst)])
                arp_reply.hwdst = arp_pkt.hwsrc
                arp_reply.opcode = arp.REPLY
                arp_reply.protosrc = arp_pkt.protodst
                arp_reply.protodst = arp_pkt.protosrc

                ether = ethernet()
                ether.type = ether.ARP_TYPE
                ether.src = EthAddr(self.arp_table[str(arp_pkt.protodst)])
                ether.dst = arp_pkt.hwsrc
                ether.payload = arp_reply

                # send ARP reply
                self.send_pkt(ether, event.ofp.in_port)
                log.debug('--ARP reply sent--')
                log.debug(ether)


    def handle_ip_pkt(self, event, ether_pkt):
        ''' For IP specific ICMP echo packets: construct ICMP reply and send back
        For IP packets to be routed to destination: check ARP table for destination MAC address
        If MAC address is known, route the packet through correct port to destination
        If MAC not known, store packet is msg_queue for now and broadcast ARP Request for its destination adress
        '''
        ip_pkt = ether_pkt.payload
        dstip = ip_pkt.dstip

        log.debug('--IP packet received--')
        log.debug(ip_pkt)

        # route pkt to host from rtable
        for item in self.rtable:
            # if dstip is the router
            if str(dstip) == item[3] and ip_pkt.protocol == ipv4.ICMP_PROTOCOL and ip_pkt.payload.type == 8:

                log.debug('--ICMP echo received--')
                self.handle_icmp_pkt(event, ether_pkt, 0)
                log.debug('--ICMP reply sent--')
                return

            # route the pkt to dest address
            elif dstip.inNetwork(item[0]):
                log.debug('ip in network, finding routes...')

                # check ARP table for MAC address
                if str(dstip) in self.arp_table.keys():
                    ether_pkt.src = EthAddr(self.arp_table[item[3]])
                    ether_pkt.dst = EthAddr(self.arp_table[str(dstip)])
                    self.send_pkt(ether_pkt, self.port_table[str(dstip)]) # originally item[4]
                    log.debug('--IP packet routed--')
                # send out ARP request to ask for MAC address
                else:
                    # update buffer with destination ip, and the packet iteself
                    self.msg_queue[str(dstip)] = [ip_pkt, str(ether_pkt.src)]

                    # construct arp request and broadcast
                    arp_req = arp()
                    arp_req.opcode = arp.REQUEST
                    arp_req.protosrc = IPAddr(item[3])
                    arp_req.protodst = IPAddr(str(dstip)) #originally just dstip
                    arp_req.hwsrc = EthAddr(self.arp_table[item[3]])
                    arp_req.hwdst = ETHER_BROADCAST

                    ether = ethernet()
                    ether.type = ether.ARP_TYPE
                    ether.src = EthAddr(self.arp_table[item[3]])
                    ether.dst = ETHER_BROADCAST
                    ether.payload = arp_req

                    self.send_pkt(ether, self.port_table[str(dstip)])# originally item[4], something with port
                    log.debug('--MAC not known, ARP REQUEST sent--')

                return

        # send ICMP dest unreachable as cannot find dstip in rtable
        self.handle_icmp_pkt(event, ether_pkt, 3)
        log.debug('--ICMP dest unreachable sent--')

    def handle_icmp_pkt(self, event, ether_pkt, type):
        ''' Send ICMP reply message for ICMP messages received, and send ICMP unreachable for wrong address
        '''
        ip_pkt = ether_pkt.payload
        icmp_pkt = ip_pkt.payload
        
        icmp_reply = icmp()
        icmp_reply.code = 0
        icmp_reply.type = type # includes 0 for echo reply and 3 for unreachable dest
        icmp_reply.payload = icmp_pkt.payload

        ip = ipv4()
        ip.protocol = ipv4.ICMP_PROTOCOL
        ip.srcip = ip_pkt.dstip
        ip.dstip = ip_pkt.srcip
        ip.payload = icmp_reply

        ether = ethernet()
        ether.type = ethernet.IP_TYPE
        ether.src = ether_pkt.dst
        ether.dst = ether_pkt.src
        ether.payload = ip

        self.send_pkt(ether, event.ofp.in_port)
        log.debug('--ICMP message sent--')

    def send_pkt(self, the_pkt, the_port):
        ''' Sends the_pkt through the_port after receing the pkt,
         applying to any packets and ports
        '''
        msg = of.ofp_packet_out()
        msg.data = the_pkt.pack()
        msg.actions.append(of.ofp_action_output(port=the_port))
        self.connection.send(msg)


def launch():
    def myrouter(event):
        Router(event.connection)
    core.openflow.addListenerByName("PacketIn", myrouter)
    log.debug("-------starts-------")
