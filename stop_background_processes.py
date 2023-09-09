import psutil
import os
import webbrowser
# List of processes to exclude from termination
excluded_processes = ['python.exe', 'code.exe']  # Add more as needed

# Get the list of all running processes
all_processes = psutil.process_iter()

# Terminate processes that are not in the excluded_processes list
for process in all_processes:
    try:
        process_info = process.as_dict(attrs=['pid', 'name'])
        process_name = process_info['name'].lower()
        process_pid = process_info['pid']

        if process_name not in excluded_processes:
            print(f"Terminating process: {process_name} (PID: {process_pid})")
            psutil.Process(process_pid).terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

