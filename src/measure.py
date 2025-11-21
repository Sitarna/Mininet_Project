#Will take measures of the network
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
                    
            elif c == 0:
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
    
    avg_latency = None
    packet_loss = None
    
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
                    #key, value = "packet loss", part.split()[0]
                    key, value = "packet loss", part.split()[0].replace("%", "")
                    packet_loss = float(value)
                elif "time" in part:
                    key, value = "time", part.split()[1]
                else:
                    continue
                entry = f"{key} = {value}"
                new_lines.append(entry)
                all_output.append(entry)

        # Extract latency/jitter
        elif line.startswith("rtt min/avg/max"):
            # Split and clean up values
            values_part = line.split("=", 1)[1]
            values = values_part.strip().replace(" ms", "").split("/")

            # Map labels to values safely
            for label, value in zip(change_name.values(), values):
                entry = f"{label} = {value} ms"
                new_lines.append(entry)
                all_output.append(entry)

                # Capture average latency
                if label == "average latency":
                    avg_latency = float(value)

    # Save KPI results
    with kpi_file.open("a") as f:
        f.write("\n".join(new_lines))

    # Save raw output
    with output_file.open("a") as f:
        f.write("\n".join(all_output) + "\n\n")
        
    return avg_latency, packet_loss

def run_iperf3(duration: int = 60, host_name: str = 'UAV_1', folder_path: str = 'data'):
    print("run_iperf3")
    # Read template
    template = Path("current_template.txt").read_text().strip()

    # Set bandwidth based on template
    if template == "X":
        bw = "128k"   # 128 kbps 
    elif template == "Y":
        bw = "4M"     # 4 Mbps
    else:
        bw = "1M"
    try:
        # Run iperf3 client command
        result = subprocess.run(["iperf3", "-c", "10.0.0.1", "-u", "-b", bw, "-t", str(duration),
        "-i", "1", "-p", "5201", "--len=512", "-J"], capture_output=True, text=True, check=False)

        if result.stdout.strip() == "":
            print("iperf3 returned no output!")
            print("stderr:", result.stderr)
        
        output = json.loads(result.stdout)
        path = folder_path / "iperf.txt"

        # Save JSON to file with indentation
        with open(path, "w") as file:
            json.dump(output, file, indent=4)
            
    except subprocess.CalledProcessError as e:
        print("Error running iperf3:")
        print(e.stderr)
    
    print("run_iperf3 done")
    return path
    
def calculate_kpis_from_iperf3(host_name: str = 'UAV_1', folder_path: str = 'data', path: str = 'data/output.txt'):
    
    #load JSON data
    with open(path, "r") as f:
        data = json.load(f)

    # Check if intervals exist
    intervals = data.get("intervals", [])
    if not intervals:
        print("No interval data available")
    
    total_bytes = 0
    total_seconds = 0
    total_packets = 0
    
    data_sum = data.get("end", {}).get("sum", {})
    total_bytes = data_sum.get("bytes", 0)
    total_seconds = data_sum.get("seconds", 1)
    total_packets = data_sum.get("packets", 0)
    udp_jitter = data_sum.get("jitter_ms", 0)
    packet_loss_pct = data_sum.get("lost_percent", 0)
    goodput = (total_bytes * 8) / total_seconds / 1_000_000  # To create Mbps
    pps = total_packets / total_seconds
    


    new_lines = []
    new_lines.append(f"\nGoodput: {goodput:.2f} Mbps")
    new_lines.append(f"Packets per second: {pps:.2f} pps")
    new_lines.append(f"UDP Jitter: {udp_jitter} ms")
    
    # Save KPI results
    kpi_file = folder_path / "kpi_results.txt"
    with kpi_file.open("a") as f:
        f.write("\n".join(new_lines) + "\n\n")
        
    return goodput, pps, udp_jitter

def get_kpi(duration: int = 60, host_name: str = 'UAV_1'):
    
#    while True:
#        print("Do you want to create a new folder? (y/n): ", end="")
#        answer = input().strip().lower()

#        if answer in ('y', 'yes'):
#            folder_path = create_folder(1)
#            break
#        elif answer in ('n', 'no'):
#            folder_path = create_folder(0)
#            break
#        else:
#            print("Please write 'y' or 'n'.")
    folder_path = create_folder(1)
    print(f"created folder: {folder_path}")
            
   
    avg_latency, ping_loss = ping(duration, host_name, folder_path)
    path = run_iperf3(duration, host_name, folder_path)
    goodput, pps, udp_jitter = calculate_kpis_from_iperf3(host_name, folder_path, path)
    template = Path("current_template.txt").read_text().strip()
    
     # --- Define SLA targets for templates ---
    SLA_TARGETS = {
        "X": {"latency_ms": 100, "udp_jitter_ms": 30, "packet_loss_pct": 0.5, "goodput_mbps": 0.128},
        "Y": {"latency_ms": 150, "udp_jitter_ms": 50, "packet_loss_pct": 1.0, "goodput_mbps": 2.0}
    }[template]
    
    # UDP packet loss from iperf3
    with open(path, "r") as f:
        iperf_data = json.load(f)
    packet_loss = iperf_data.get("end", {}).get("sum", {}).get("lost_percent", 0)

    # SLA evaluation
    if (avg_latency <= SLA_TARGETS["latency_ms"]
        and udp_jitter <= SLA_TARGETS["udp_jitter_ms"]
        and packet_loss <= SLA_TARGETS["packet_loss_pct"]
        and goodput >= SLA_TARGETS["goodput_mbps"]):
        result = "Does comply with your SLA rules"
    else:
        result = "Does NOT comply with your SLA rules"

    #Write KPI Summary
    new_lines = []
    new_lines.append("========= KPI SUMMARY =========")
    new_lines.append(f"QoS Template: {template} \n")
    new_lines.append(f"From PING: ")
    new_lines.append(f"Average latency: {avg_latency:.2f} ms")
    new_lines.append(f"Ping packet loss: {ping_loss:.2f}% \n")

    new_lines.append(f"From IPERF3 (UDP stream):")
    new_lines.append(f"Goodput: {goodput:.2f} Mbps")
    new_lines.append(f"UDP Jitter: {udp_jitter:.2f} ms")
    new_lines.append(f"UDP Packet Loss: {packet_loss:.2f}%")

    new_lines.append(f"SLA compliance: {result} \n")
    new_lines.append(f"Your target: latency <= {SLA_TARGETS['latency_ms']} ms, "
                 f"jitter <= {SLA_TARGETS['udp_jitter_ms']} ms, "
                     f"loss <= {SLA_TARGETS['packet_loss_pct']}%, "
                     f"goodput >= {SLA_TARGETS['goodput_mbps']} Mbps")

    new_lines.append(f"Your result:  latency={avg_latency:.2f} ms, jitter={udp_jitter:.2f} ms, "
                     f"loss={packet_loss:.2f}%, goodput={goodput:.2f} Mbps")

    # Save KPI summary
    kpi_file = folder_path / "kpi_results.txt"
    with kpi_file.open("a", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n\n")
            