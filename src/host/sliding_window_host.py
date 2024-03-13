from abc import ABC

from host.host import Host
from network.network_interface import NetworkInterface
from network.packet import Packet
from simulation.clock import Clock
from util.timeout_calculator import TimeoutCalculator

"""
This host follows the SlidingWindow protocol. It maintains a window size and the
list of unACKed packets.
"""


class SlidingWindowHost(Host, ABC):

    def __init__(self, clock: Clock, network_interface: NetworkInterface, window_size: int,
                 timeout_calculator: TimeoutCalculator):
        # Host configuration
        self.timeout_calculator: TimeoutCalculator = timeout_calculator
        self.network_interface: NetworkInterface = network_interface
        self.clock: Clock = clock
        

        # TODO: Add any stateful information you might need to track the progress of this protocol as packets are
        #  sent and received.
        #    - Feel free to create new variables and classes, just don't delete any existing infrastructure.
        #    - In particular, you should make use of the network interface to interact with the network.
        #    - It's worth keeping in mind that you'll soon have to implement AIMD, which also implements the sliding
        #      window protocol. It might be worth structuring your code here in such a way that you can reuse it for
        #      AIMD.
        self.window_size = window_size
        self.next_up = 0
        self.inflight: List[Packet] = []
        self.acked: List[Packet] = []
        self.buffer: List[Packet] = []

    def run_one_tick(self) -> int | None:
        current_time = self.clock.read_tick()
        self.timeout = self.timeout_calculator.timeout()

        # TODO: STEP 1 - Process newly received messages
        #  - These will all be acknowledgement to messages this host has previously sent out.
        #  - You should mark these messages as successfully delivered.

        for packet in self.buffer:
            if packet.sequence_number == self.next_up:
                self.acked.append(packet)
                self.buffer.remove(packet)
                self.next_up += 1

        packets_received = self.network_interface.receive_all()
        for packet in packets_received:
            if packet.sequence_number == self.next_up:
                self.acked.append(packet)
                self.inflight.remove(packet)
                self.next_up += 1
            else:
                self.buffer.append(packet)
                self.inflight.remove(packet)



        # TODO: STEP 2 - Retry any messages that have timed out
        #  - When you transmit each packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see if there are any inflight messages who's timeout has already passed
        #  - If you find a timed out message, create a new packet and transmit it
        #      - The new packet should have the same sequence number
        #      - You should set the packet's retransmission_flag to true
        #      - The sent time should be the current timestamp
        #      - Use the transmit() function of the network interface to send the packet

        for packet in self.inflight:
            if (current_time - packet.sent_timestamp) > self.timeout:
                retransmission_packet = Packet(sent_timestamp=current_time, sequence_number=packet.sequence_number, retransmission_flag=True, ack_flag=False)
                self.network_interface.transmit(retransmission_packet)
                self.inflight.remove(packet)
                self.inflight.append(retransmission_packet)





        # TODO: STEP 3 - Transmit new messages
        #  - When you transmit each packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see how many additional packets we can put inflight based on the sliding window spec
        #  - Construct and transmit the packets
        #      - Each new packet represents a new message that should have its own unique sequence number
        #      - Sequence numbers start from 0 and increase by 1 for each new message
        #      - Use the transmit() function of the network interface to send the packet

        window_space = self.window_size - len(self.inflight)
        available_sequence_number = len(self.inflight) + self.next_up
        for i in range (window_space):
            new_packet = Packet(sent_timestamp=current_time, sequence_number = available_sequence_number, retransmission_flag=False, ack_flag=False)
            self.network_interface.transmit(new_packet)
            self.inflight.append(new_packet)
            available_sequence_number += 1

        # TODO: STEP 4 - Return
        #  - Return the largest in-order sequence number
        #      - That is, the sequence number such that it, and all sequence numbers before, have been ACKed



        return (self.next_up - 1)
