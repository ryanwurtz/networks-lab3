#!/usr/bin/env python3
from monitor import Monitor
import sys
import configparser

if __name__ == '__main__':
    print("Receiver starting up!")
    config_path = sys.argv[1]

    # Initialize receiver monitor
    recv_monitor = Monitor(config_path, 'receiver')
    
    #PARSE CONFIG FILE
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    sender_id = int(cfg.get('sender', 'id'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    write_dest = cfg.get('receiver','write_location')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))

    #RECEIVE LOOP
    open(write_dest, 'wb').close()
    base = 0
    final_seq_num = -1
    done = False
    unacked_nums = {}

    with open(write_dest,"r+b") as file:
        while True:
            # parse packet
            addr, data = recv_monitor.recv(max_packet_size)
            if data is None:
                continue
            packet_num = int.from_bytes(data[0:4], byteorder='big')
            finished = int.from_bytes(data[4:5], byteorder='big')
            packet_data = data[5:]

            # the next packet
            if packet_num == base:
                base += len(packet_data)

                while base in unacked_nums:
                    base += unacked_nums.pop(base)

                ack_packet = base.to_bytes(4, byteorder='big') + (-1).to_bytes(4, byteorder='big', signed=True)
                recv_monitor.send(addr, ack_packet)

                # write packet to file
                file.seek(packet_num)
                file.write(packet_data)

            # OOO packet
            elif packet_num > base:
                unacked_nums[packet_num] = len(packet_data)
                ack_packet = base.to_bytes(4, byteorder='big') + packet_num.to_bytes(4, byteorder='big')
                recv_monitor.send(addr, ack_packet)

                # write packet to file
                file.seek(packet_num)
                file.write(packet_data)
        
            # duplicate packet
            else:
                ack_packet = base.to_bytes(4, byteorder='big') + (-1).to_bytes(4, byteorder='big', signed=True)
                recv_monitor.send(addr, ack_packet)

            # found end of file
            if finished == 1:
                final_seq_num = packet_num + len(packet_data)

            # end and compare once all packets received
            if base == final_seq_num and not done:
                done = True
                file.close()
                recv_monitor.recv_end(write_dest, sender_id)

        