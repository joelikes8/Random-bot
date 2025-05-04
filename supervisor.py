import subprocess
import sys
import os
import signal
import time

processes = []

def signal_handler(sig, frame):
    print("\nShutting down all processes...")
    for proc in processes:
        if proc.poll() is None:  # If the process is still running
            proc.terminate()
    sys.exit(0)

def main():
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting Discord Bot + Web Application")
    
    # Open a log file for capturing output
    with open("supervisor.log", "a") as log_file:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n\n=== Starting services at {current_time} ===\n")
        
        # Start the Discord bot with output redirection
        bot_process = subprocess.Popen(
            [sys.executable, "run_bot.py"],
            stdout=log_file,
            stderr=log_file
        )
        processes.append(bot_process)
        print("Started Discord bot process")
        log_file.write("Started Discord bot process\n")
        
        # Start the web server using gunicorn with output redirection
        web_process = subprocess.Popen(
            ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "main:app"],
            stdout=log_file,
            stderr=log_file
        )
        processes.append(web_process)
        print("Started web server process")
        log_file.write("Started web server process\n")
        
        # Log that everything started
        log_file.write("All processes started successfully\n")
        log_file.flush()
    
    # Keep the script running
    try:
        while True:
            time.sleep(5)  # Check less frequently to reduce overhead
            
            # Check if any process has terminated
            for proc in processes:
                if proc.poll() is not None:
                    print(f"Process exited with code {proc.poll()}")
                    # Terminate all processes and exit
                    signal_handler(None, None)
                    
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
