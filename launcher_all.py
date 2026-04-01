#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import configparser
import csv
import re

# -- Absolute Path Setup --
ROOT          = os.path.dirname(os.path.abspath(__file__))
EMULATOR_DIR  = os.path.join(ROOT, "Emulator")
STUDENT_DIR   = os.path.join(ROOT, "Student Code", "stop_and_go")
CONFIG_DIR    = os.path.join(ROOT, "TestConfig")

def parse_log_val(regex, text, default="N/A"):
    """Helper to extract values from the log text using regex."""
    match = re.search(regex, text)
    return match.group(1) if match else default

def main():
    if len(sys.argv) < 2:
        print("Usage: python launcher.py <config_file.ini>")
        sys.exit(1)

    conf_name = sys.argv[1]
    abs_config = os.path.abspath(os.path.join(CONFIG_DIR, conf_name))
    
    if not os.path.isfile(abs_config):
        print(f"Error: Config not found at {abs_config}")
        sys.exit(1)

    results = []
    print(f"[*] Starting Automated Batch Run for {conf_name}")

    # Define the temporary config file path OUTSIDE the loop
    temp_config = os.path.join(CONFIG_DIR, f"temp_run_{conf_name}")

    # Loop 5 times sequentially to preserve Goodput integrity
    for i in range(1, 6):
        print(f"\n=============================================")
        print(f" RUN {i} OF 5")
        print(f"=============================================")
        
        # Read the base config to make a unique temporary config
        cfg = configparser.RawConfigParser(allow_no_value=True)
        cfg.read(abs_config)
        
        # Set unique output files so runs don't overwrite each other
        sender_log = os.path.join(ROOT, f"sender_run{i}.log")
        recv_log = os.path.join(ROOT, f"receiver_run{i}.log")
        emu_log = os.path.join(ROOT, f"emulator_run{i}.log")
        out_file = os.path.join(ROOT, f"output_run{i}.txt")
        
        if cfg.has_section('sender'): cfg.set('sender', 'log_file', sender_log)
        if cfg.has_section('receiver'): cfg.set('receiver', 'log_file', recv_log)
        if cfg.has_section('receiver'): cfg.set('receiver', 'write_location', out_file)
        if cfg.has_section('emulator'): cfg.set('emulator', 'log_file', emu_log)
        
        # Write to the temp config we defined above
        with open(temp_config, 'w') as f:
            cfg.write(f)
            
        # 1. Start Emulator
        print("  [+] Starting Emulator...")
        emu_proc = subprocess.Popen(["python", "emulator.py", temp_config], cwd=EMULATOR_DIR)
        time.sleep(2)
        
        # 2. Start Receiver
        print("  [+] Starting Receiver...")
        recv_proc = subprocess.Popen(["python", "receiver_stop_and_go.py", temp_config], cwd=STUDENT_DIR)
        time.sleep(1)
        
        # 3. Start Sender
        print("  [+] Starting Sender...")
        send_proc = subprocess.Popen(["python", "sender_stop_and_go.py", temp_config], cwd=STUDENT_DIR)
        
        print(f"  [*] Waiting for transmission to finish...")
        # This acts as our block. It pauses the script until the sender naturally exits!
        send_proc.wait() 
        
        # Give the emulator and receiver 2 seconds to flush their final logs to the disk
        time.sleep(2) 
        
        # Cleanly terminate the remaining processes
        recv_proc.terminate()
        emu_proc.terminate()
        
        print("  [+] Run complete. Parsing logs...")
        
        # Extract data into a dictionary
        run_data = {'Run': i, 'Config': conf_name}
        
        try:
            with open(sender_log, 'r') as f:
                stext = f.read()
                run_data['File Size'] = parse_log_val(r'File Size\s*:\s*(\d+)', stext)
                run_data['Sent Bytes'] = parse_log_val(r'Total Bytes Transmitted\s*:\s*(\d+)', stext)
                run_data['Overhead'] = parse_log_val(r'Overhead\s*:\s*(\d+)', stext)
                run_data['Sent Packets'] = parse_log_val(r'Number of Packets sent\s*:\s*(\d+)', stext)
                run_data['Sender Time'] = parse_log_val(r'Total Time\s*:\s*([\d.]+)', stext)
                run_data['Goodput'] = parse_log_val(r'Goodput\s*:\s*([\d.]+)', stext)
        except FileNotFoundError:
            print("  [!] Sender log not found.")
            
        try:
            with open(recv_log, 'r') as f:
                rtext = f.read()
                run_data['Correct'] = parse_log_val(r'File transmission correct\s*:\s*(\w+)', rtext)
                run_data['Recv Packets'] = parse_log_val(r'Number of Packets Received\s*:\s*(\d+)', rtext)
                run_data['Recv Bytes'] = parse_log_val(r'Total Bytes Transmitted\s*:\s*(\d+)', rtext)
                run_data['Recv Time'] = parse_log_val(r'Total Time\s*:\s*([\d.]+)', rtext)
        except FileNotFoundError:
            print("  [!] Receiver log not found.")
            
        results.append(run_data)

    # 4. Write everything to a CSV
    csv_filename = os.path.join(ROOT, f"results_{conf_name.replace('.ini', '')}.csv")
    print(f"\n[*] Writing results to {csv_filename}...")
    
    headers = ['Run', 'Config', 'Correct', 'File Size', 'Goodput', 'Sender Time', 'Recv Time', 
               'Sent Packets', 'Recv Packets', 'Sent Bytes', 'Recv Bytes', 'Overhead']
               
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in results:
            # Fills any missing data with 'N/A' to keep the CSV clean
            writer.writerow({k: row.get(k, 'N/A') for k in headers}) 
            
    print("[+] CSV successfully generated!")

    # 5. Clean up the temporary files
    print("[*] Sweeping up temporary log and text files...")
    if os.path.exists(temp_config):
        os.remove(temp_config)
        
    for i in range(1, 6):
        files_to_delete = [
            os.path.join(ROOT, f"sender_run{i}.log"),
            os.path.join(ROOT, f"receiver_run{i}.log"),
            os.path.join(ROOT, f"emulator_run{i}.log"),
            os.path.join(ROOT, f"output_run{i}.txt")
        ]
        for f_path in files_to_delete:
            if os.path.exists(f_path):
                os.remove(f_path)
                
    print("[+] Directory clean. All done!")

if __name__ == "__main__":
    main()