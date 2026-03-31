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
    unacked_nums = set()

    while True:
        # parse packet
        addr, data = recv_monitor.recv(max_packet_size)
        if data is None:
            continue
        packet_num = int.from_bytes(data[0:4], byteorder='big')
        finished = int.from_bytes(data[4], byteorder='big')
        packet_data = data[5:]

        # the next packet
        if packet_num == base + 1015:
            base = packet_num

            while base in unacked_nums:
                unacked_nums.remove(base)
                base += 1015

            ack_packet = base.to_bytes(4, byteorder='big') + (-1).to_bytes(4, byteorder='big')
            recv_monitor.send(addr, ack_packet)

        # OOO packet
        if packet_num > base + 1015:
            unacked_nums.add(packet_num)
            ack_packet = base.to_bytes(4, byteorder='big') + packet_num.to_bytes(4, byteorder='big')
            recv_monitor.send(addr, ack_packet)
        
        # duplicate packet
        else:
            ack_packet = base.to_bytes(4, byteorder='big') + (-1).to_bytes(4, byteorder='big')
            recv_monitor.send(addr, ack_packet)

        # write packet to file
        with open(write_dest,"ab") as file:
            file.seek(packet_num)
            file.write(packet_data)

        #end if final packet received
        if finished == 1:
            recv_monitor.recv_end(write_dest, sender_id)

        