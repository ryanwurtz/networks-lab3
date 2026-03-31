#!/usr/bin/env python3
from monitor import Monitor
import sys
import configparser
import socket

if __name__ == '__main__':
    print("Sender starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    send_monitor = Monitor(config_path, 'sender')
    
    #PARSE CONFIG FILE
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    # Network Configs
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
    prop_delay = float(cfg.get('network', 'PROP_DELAY'))
    link_bandwidth = int(cfg.get('network', 'LINK_BANDWIDTH'))
    # Node configs
    file_to_send = cfg.get('nodes', 'file_to_send')
    # Recevier Configs
    receiver_id = int(cfg.get('receiver','id'))

    #PARAMETER SETTING
    ideal_transmission_delay = (max_packet_size / link_bandwidth) + prop_delay
    timeout_period = ideal_transmission_delay * 10
    send_monitor.socketfd.settimeout(timeout_period)

    #FILE TRANSMISSION LOOP
    file = open(file_to_send, "rb")

    finished = False
    packet_num = 0
    while not finished:
        #grab data from file
        data = file.read(1017)
        data_len = len(data)

        if data_len < 1017:
            finished = True
        
        #build packet
        header0 = data_len.to_bytes(2, byteorder='big')
        header1 = finished.to_bytes(1, byteorder='big')
        packet = header0 + header1 + data
        
        #send and wait for ack
        ack = False
        while not ack:
            send_monitor.send(receiver_id, packet)
            try:
                addr, recv_data = send_monitor.recv(max_packet_size)
                if recv_data is None:
                    continue
                ack_num = int.from_bytes(recv_data[:2], byteorder='big')
                if ack_num == packet_num:
                    ack = True
                #else:
                    #print(f"Bad ack on packet {packet_num}")
                    #print(f"Data received: {recv_data}")
            except socket.timeout:
                continue
                #print(f"Timeout on packet {packet_num}")

        packet_num += 1

    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
    file.close()
    send_monitor.send_end(receiver_id)