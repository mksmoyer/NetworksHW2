from abc import ABC

from host.host import Host
from network.network_interface import NetworkInterface
from network.packet import Packet
from simulation.clock import Clock
from util.timeout_calculator import TimeoutCalculator

"""
This host implements the stop and wait protocol. Here the host only
sends one packet in return of an acknowledgement.
"""


class StopAndWaitHost(Host, ABC):

    def __init__(self, clock: Clock, network_interface: NetworkInterface, timeout_calculator: TimeoutCalculator):
        # Host configuration
        self.timeout_calculator: TimeoutCalculator = timeout_calculator
        self.network_interface: NetworkInterface = network_interface
        self.clock: Clock = clock

        # TODO: Add any stateful information you might need to track the progress of this protocol as packets are
        #  sent and received.
        #    - Feel free to create new variables and classes, just don't delete any existing infrastructure.
        #    - In particular, you should make use of the network interface to interact with the network.

        # next_up is the pakcet we are waiting to be acked, inflight is an array holding the inflight packet
        # acked is an array with the acked packets
        self.next_up = 0
        self.inflight = []
        self.acked = []


    def run_one_tick(self) -> int | None:
        current_time = self.clock.read_tick()

        # TODO: STEP 1 - Process newly received messages
        #  - These will all be acknowledgement to messages this host has previously sent out.
        #  - You should mark these messages as successfully delivered.

        # mark delivered by adding to list of acked packets, then increase next_up
        packets_received = self.network_interface.receive_all()
        if packets_received and packets_received[0].sequence_number == self.next_up:
            self.acked.append (packets_received[0])
            self.next_up += 1

        # TODO: STEP 2 - Retry any messages that have timed out
        #  - When you transmit a packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see if the inflight message's timeout has already passed.
        #  - If the packet did time out, construct a new packet and transmit
        #      - The new packet should have the same sequence number
        #      - You should set the packet's retransmission_flag to true
        #      - The sent time should be the current timestamp
        #      - Use the transmit() function of the network interface to send the packet

        # if there are packets in flight, we see if the time since sending exceeds the current timeout at this tick
        # if the timeout is exceeded, we make a packet with retransmission flag True and the same sequence number to simulate retransmission
        # also need to clear inflight array of the old packet and add new one to inflight
        if self.inflight and (current_time - self.inflight[0].sent_timestamp) > self.timeout_calculator.timeout:
            self.inflight.clear()
            retransmission_packet = Packet(sent_timestamp=current_time, sequence_number=self.next_up, retransmission_flag=True, ack_flag=False)
            self.network_interface.transmit(retransmission_packet)
            self.inflight.append(retransmission_packet)


        # TODO: STEP 3 - Transmit new messages
        #  - When you transmit a packet (in steps 2 and 3), you should track that message as inflight
        #  - If you don't have a message inflight, we should send the next message
        #  - Construct and transmit the packet
        #      - The packet represents a new message that should have its own unique sequence number
        #      - Sequence numbers start from 0 and increase by 1 for each new message
        #      - Use the transmit() function of the network interface to send the packet

        # Set up packet with retransmission and ack flags as false because it is new
        # Making new packets with sequence number next_up, which is the sequence number after the largest one which has been acked so far
        if not self.inflight:
            new_packet = Packet(sent_timestamp=current_time, sequence_number=self.next_up, retransmission_flag=False, ack_flag=False)
            self.network_interface.transmit(new_packet)
            self.inflight.append(new_packet)

        # TODO: STEP 4 - Return
        #  - Return the largest in-order sequence number
        #      - That is, the sequence number such that it, and all sequence numbers before, have been ACKed

        # The last time we succesfully receive, next_up is moved to the next one being waited for, so next_up-1 is the last ack
        return self.next_up
        
