#!/usr/bin/env python3
from monitor import Monitor
import sys

# Config File
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

    #FILE SETUP
    open(write_dest, 'wb').close()

    #RECEIVE LOOP
    last_packet_received = False
    exp_packet_num = 0

    while True:
        #receive packet
        addr, data = recv_monitor.recv(max_packet_size)
        if data is None:
            continue
        
        #parse packet
        packet_num = int.from_bytes(data[2:4], byteorder='big')
        finished = int.from_bytes(data[4:5], byteorder='big')
        packet_data = data[5:]

        #write data if any
        if packet_num == exp_packet_num:
            with open(write_dest,"ab") as file:
                file.write(packet_data)
            exp_packet_num += 1

            #end if final packet received
            if finished == 1:
                recv_monitor.recv_end(write_dest, sender_id)

        #send ack
        ack_packet = packet_num.to_bytes(2, byteorder='big')
        recv_monitor.send(addr, ack_packet)