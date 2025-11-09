#Will take measures of the network
#mininet> UAV_1 iperf3 -c 10.0.0.1 -u -b 10M -t 2 -J


import json
import subprocess
import time
import sys
import os
from pathlib import Path

def create_folder(c: int = 2):
    #create data if data does not exist
    base_dir = Path("data")
    base_dir.mkdir(exist_ok=True)
    i = 1
    while True:
        folder_path = base_dir / f"KPI_information{i}"
        if not os.path.exists(folder_path):
            if c == 1:
                # creates a new folder
                folder_path.mkdir()
                print(f"Created folder: {folder_path}")
                return folder_path;
                    
            elif c == 2:
                # return name of latest created folder
                return base_dir / f"KPI_information{i-1}"   
            break
    
        else:
            i += 1
    
    
def ping(duration: int = 60, host_name: str = 'UAV_1', folder_path: str = 'data'):
    
    output_file = folder_path / f"{host_name}_ping.txt"   
    kpi_file = folder_path / "kpi_results.txt"

    print(f"ping")
    all_output = []  
    new_lines = []   
    new_lines.append(f"=========   KPI MEASUREMENTS {host_name}  ==========")
    new_lines.append("KPI: Latency, Jitter, Packet loss, Goodput\n")
    
    # ping gcs with ip 10.0.0.1
    cmd = ["ping", "-c", str(duration), "10.0.0.1"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)

    # Add full ping output to all_output
    all_output.append("----- Raw ping output -----")
    all_output.append(result.stdout)
    all_output.append("----- Parsed KPI values -----")

    change_name = {
        "min": "fastest packet",
        "avg": "average latency",
        "max": "slowest packet",
        "mdev": "  ping jitter"
    }
    
    #parsing the ping output
    for line in result.stdout.splitlines():
        # Extract summary stats
        if "packets transmitted" in line:
            #splits the lines by ,
            parts = [p.strip() for p in line.split(",")]
            for part in parts:
                if "transmitted" in part:
                    key, value = "packets transmitted", part.split()[0]
                elif "received" in part:
                    key, value = "packets received", part.split()[0]
                elif "packet loss" in part:
                    key, value = "packet loss", part.split()[0]
                elif "time" in part:
                    key, value = "time", part.split()[1]
                else:
                    continue
                entry = f"{key} = {value}"
                new_lines.append(entry)
                all_output.append(entry)

        # Extract latency/jitter
        elif line.startswith("rtt min/avg/max"):
            _, values_part = line.split("=")
            values = values_part.strip().replace(" ms", "").split("/")
            for label, value in zip(change_name.values(), values):
                entry = f"{label} = {value} ms"
                new_lines.append(entry)
                all_output.append(entry)

    print("done with ping")
    all_output.append("done with ping\n")

    # Save KPI results
    with kpi_file.open("a") as f:
        f.write("\n".join(new_lines))

    # Save raw output
    with output_file.open("a") as f:
        f.write("\n".join(all_output) + "\n\n")

def run_iperf3(duration: int = 60, host_name: str = 'UAV_1', folder_path: str = 'data'):
    print("run_iperf3")
    try:
        # Run iperf3 client command
        result = subprocess.run(["iperf3", "-c", "10.0.0.1", "-u","-b", "1M","-t", str(duration),"-p", "5201","-J"],
            capture_output=True,text=True,check=False)
        output = json.loads(result.stdout)
        path = folder_path / "iperf.txt"

        # Save JSON to file with indentation
        with open(path, "w") as file:
            json.dump(output, file, indent=4)
            
    except subprocess.CalledProcessError as e:
        print("Error running iperf3:")
        print(e.stderr)
    
    print("run_iperf3 done")
    host_name = host_name
    calculate_kpis_from_iperf3(host_name, folder_path, path)
    
def calculate_kpis_from_iperf3(host_name: str = 'UAV_1', folder_path: str = 'data', path: str = 'data/output.txt'):
    
    #load JSON data
    with open(path, "r") as f:
        data = json.load(f)

    # Check if intervals exist
    intervals = data.get("intervals", [])
    if not intervals:
        print("No interval data available")
        return

    total_bytes = 0
    total_seconds = 0
    total_packets = 0

    for interval in intervals:
        sum_info = interval.get("sum", {})
        total_bytes += sum_info.get("bytes", 0)
        total_seconds += sum_info.get("seconds", 0)
        total_packets += sum_info.get("packets", 0)

    # Goodput in Mbps
    goodput_mbps = (total_bytes * 8) / total_seconds / 1_000_000 if total_seconds > 0 else 0

    # Packets per second
    pps = total_packets / total_seconds if total_seconds > 0 else 0

    # Jitter
    jitter = data.get("end", {}).get("sum", {}).get("jitter_ms", "Could not find jitter")
    
    new_lines = []
    new_lines.append(f"\nGoodput: {goodput_mbps:.2f} Mbps")
    new_lines.append(f"Packets per second: {pps:.2f} pps")
    new_lines.append(f"UDP Jitter: {jitter} ms")
    
    kpi_file = folder_path / "kpi_results.txt"
    with kpi_file.open("a") as f:
        f.write("\n".join(new_lines) + "\n\n")

    
