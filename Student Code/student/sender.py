#!/usr/bin/env python3
from monitor import Monitor
import sys
import configparser
import time
import threading

# cross thread variables
in_flight = {}
base = 0

def ack_receiver():
        while True:
            # receive & decode ack packet
            addr, recv_data = send_monitor.recv(max_packet_size)
            if recv_data is None:
                continue
            ack_num = int.from_bytes(recv_data[:4], byteorder='big')
            opt_ack_num = int.from_bytes(recv_data[4:8], byteorder='big')

            # update base
            if ack_num > base:
                base = ack_num

            # clear packets from cumulative ack
            for sequence_num in in_flight.keys():
                if sequence_num < ack_num:
                    in_flight.pop(sequence_num)

            # clear sack packet
            if not opt_ack_num == -1 and opt_ack_num in in_flight:
                in_flight.pop(sequence_num)
            
if __name__ == '__main__':
    print("Sender starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    send_monitor = Monitor(config_path, 'sender')
    
    #PARSE CONFIG FILE
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
    prop_delay = float(cfg.get('network', 'PROP_DELAY'))
    link_bandwidth = int(cfg.get('network', 'LINK_BANDWIDTH'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    receiver_id = int(cfg.get('receiver','id'))
    window_size = int(cfg.get('sender', 'window_size'))

    #PARAMETER SETTING
    timeout_period = (max_packet_size / link_bandwidth) + prop_delay * 10
    packet_size = 1015

    # ack thread
    recv_thread = threading.Thread(target=ack_receiver,args=())
    recv_thread.start()

    # transmitter thread
    file = open(file_to_send, "rb")
    finished = False
    last_sent = 0

    while not finished and len(in_flight):
        # put as many packets in flight as we can
        while (last_sent < base + (window_size * packet_size)) and not finished:
            # build packet
            data = file.read(packet_size)
            seq_num = file.tell()
            if len(data) < packet_size:
                finished = True
            packet = seq_num.to_bytes(4, byteorder='big') + finished.to_bytes(1, byteorder='big') + data
        
            # fire away
            send_monitor.send(receiver_id, packet)
            in_flight[seq_num] = {"packet": packet, "sent_time": time.time()}
            last_sent = seq_num

        # check timeouts and resend if necessary
        cur_time = time.time()
        for sequence, packet_info in in_flight.items():
            if cur_time - packet_info["sent_time"] > timeout_period:
                send_monitor.send(receiver_id, packet_info["packet"])
                packet_info["sent_time"] = cur_time


    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
    file.close()
    send_monitor.send_end(receiver_id)