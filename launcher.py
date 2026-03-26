#!/usr/bin/env python
import os
import sys
import subprocess
import time

# -- Absolute Path Setup --
ROOT          = os.path.dirname(os.path.abspath(__file__))
EMULATOR_DIR  = os.path.join(ROOT, "Emulator")
# Handles the space in "Student Code"
STUDENT_DIR   = os.path.join(ROOT, "Student Code", "stop_and_go")
CONFIG_DIR    = os.path.join(ROOT, "TestConfig")

processes = []

def run_bg(title, cwd, cmd_list):
    """Runs a process in the background and keeps it alive (Windows only)."""
    print(f"  [+] Starting {title}...")
    
    # creationflags=subprocess.CREATE_NEW_PROCESS_GROUP replaces os.setpgrp for Windows
    proc = subprocess.Popen(
        cmd_list,
        cwd=cwd,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    processes.append((title, proc))

def main():
    if len(sys.argv) < 2:
        print("Usage: python launcher.py config1.ini")
        sys.exit(1)

    # We take the first argument. If it's a list, we take the first element.
    arg = sys.argv[1]
    conf_name = arg if isinstance(arg, list) else arg
    
    abs_config = os.path.abspath(os.path.join(CONFIG_DIR, conf_name))
    
    if not os.path.isfile(abs_config):
        print(f"Error: Config not found at {abs_config}")
        sys.exit(1)

    print(f"Root: {ROOT}")
    print(f"Config: {conf_name}\n")

    # 1. Emulator (using "python" instead of "python3" for Windows)
    run_bg("Emulator", EMULATOR_DIR, ["python", "emulator.py", abs_config])
    time.sleep(2)

    # 2. Receiver
    run_bg("Receiver", STUDENT_DIR, ["python", "receiver_stop_and_go.py", abs_config])
    time.sleep(1)

    # 3. Sender
    run_bg("Sender", STUDENT_DIR, ["python", "sender_stop_and_go.py", abs_config])

    print("\n" + "="*45)
    print(" ALL PROCESSES RUNNING IN BACKGROUND ")
    print(" Press Ctrl+C to stop all processes.")
    print("="*45)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTerminating processes...")
        # Cleanly kill the processes when Ctrl+C is pressed
        for title, proc in processes:
            proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()