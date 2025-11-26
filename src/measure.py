#Will take measures of the network
import json
import subprocess
import time
import sys
import os
from pathlib import Path
from scapy.all import rdpcap, UDP
import numpy as np
from collections import defaultdict

def create_folder(c: int = 2):
    #create data if data does not exist
    base_dir = Path("/home/mininet/Mininet_Project/data")
    base_dir.mkdir(exist_ok=True)
    i = 1
    while True:
        folder_path = base_dir / f"KPI_information{i}"
        if not os.path.exists(folder_path):
            if c == 1:
                # creates a new folder
                folder_path.mkdir()
                return folder_path;
                    
            elif c == 0:
                # return name of latest created folder
                return base_dir / f"KPI_information{i-1}"   
            break
    
        else:
            i += 1  
    
def ping(duration: int = 60, host_name: str = 'UAV_1', folder_path: str = 'data'):
    template = Path("../src/current_template.txt").read_text().strip()
    output_file = folder_path / f"{host_name}_ping.txt"   
    kpi_file = folder_path / "kpi_results.txt"

    print(f"ping")
    all_output = []  
    new_lines = []   
    new_lines.append(f"=======  KPI MEASUREMENTS {host_name} with QoS Template: {template}  =======")

    # ping gcs with ip 10.0.0.254
    cmd = ["ping", "-c", str(duration), "10.0.0.254"]
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
    template = Path("../src/current_template.txt").read_text().strip()

    # Set bandwidth based on template
    print("Running the iperf with template {}".format(template))
    
    if template == "X":
        bw = "128k"   # 128 kbps
        pkt_len = "100"
    elif template == "Y":
        bw = "4M"     # 4 Mbps
        pkt_len = "512"
    else:
        bw = "1M"
        pkt_len = "512"
    try:
        # Run iperf3 client command
        result = subprocess.run(["iperf3", "-c", "10.0.0.1", "-u", "-b", bw, "-t", str(duration),
        "-i", "1", "-p", "5201", "--len", pkt_len, "-J"], capture_output=True, text=True, check=False)

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

def analyze_mavlink(folder_path: str = 'data'):
    pcap_file = "/home/mininet/Mininet_Project/MAVLink/mavlink.pcap"

    # Read packets
    packets = rdpcap(pcap_file)
    mav_packets = []

    for pkt in packets:

        # Only accept UDP packets (MAVLink runs on UDP)
        if UDP not in pkt:
            continue

        payload = bytes(pkt[UDP].payload)

        # MAVLink v1/v2 frames must be >= 6 bytes
        if len(payload) < 6:
            continue

        # MAVLink v1: 0xFE   MAVLink v2: 0xFD
        if payload[0] not in (0xFE, 0xFD):
            continue

        ts = float(pkt.time)
        seq = payload[2]

        # Extract message ID
        msgid = payload[5] if payload[0] == 0xFE else payload[6]

        mav_packets.append((ts, seq, msgid, payload))

    if not mav_packets:
        print("No valid MAVLink packets found")
        return None

    # Loss calculation
    last_seq = None
    lost = 0
    total = len(mav_packets)

    for ts, seq, msgid, payload in mav_packets:
        if last_seq is not None:
            diff = (seq - last_seq) % 256
            if diff > 1:
                lost += diff - 1
        else:
            last_seq = seq

    loss_rate = (lost / total) * 100 if total else 0

    # Per-message timing
    times_by_msg = defaultdict(list)
    for ts, seq, msgid, payload in mav_packets:
        times_by_msg[msgid].append(ts)

    rates_hz = {}
    jitter_s = {}
    for msgid, t in times_by_msg.items():
        if len(t) >= 2:
            diffs = np.diff(t)
            rates_hz[msgid] = 1 / np.mean(diffs)
            jitter_s[msgid] = float(np.std(diffs))

    # Bandwidth (kbps)
    total_bytes = sum(len(payload) for ts, seq, msgid, payload in mav_packets)
    duration = mav_packets[-1][0] - mav_packets[0][0]
    
    if duration > 0:
        bandwidth_kbps = (total_bytes * 8 / 1000) / duration 
    else:
        bandwidth_kbps = 0

    # General MAVLink timing
    all_times = [ts for ts, seq, msgid, payload in mav_packets]
    diffs_all = np.diff(all_times)
    avg_interval = np.mean(diffs_all) * 1000  # convert to ms
    overall_jitter = np.std(diffs_all) * 1000  # convert to ms

    # Save results
    new_lines = []
    new_lines.append("\n\n========= MAVLink KPI RESULTS =========\n")
    new_lines.append(f"Total packets: {total}")
    new_lines.append(f"Lost packets: {lost}")
    new_lines.append(f"Packet loss: {loss_rate:.2f}%")
    new_lines.append(f"Total bandwidth: {bandwidth_kbps:.2f} kbps")
    new_lines.append(f"Average interval: {avg_interval:.6f} ms")
    new_lines.append(f"Overall jitter: {overall_jitter:.6f} ms\n")

    kpi_file = folder_path / "kpi_results.txt"
    with kpi_file.open("a") as f:
        f.write("\n".join(new_lines) + "\n\n")

        f.write("---- Message Rates (Hz) ----\n")
        for msgid, rate in rates_hz.items():
            f.write(f"MSG {msgid}: {rate:.2f} Hz\n")

        f.write("\n---- Message Jitter (s) ----\n")
        for msgid, j in jitter_s.items():
            f.write(f"MSG {msgid}: {j:.6f} s\n")

    return total, lost, loss_rate, bandwidth_kbps, avg_interval, overall_jitter, rates_hz, jitter_s


def get_kpi(duration: int = 60, host_name: str = 'UAV_1', folder:bool = True):
    
    while True:
        #answer = input("Do you want to create a new folder? (y/n): ").strip().lower()
        answer = folder
        if answer == True:
            folder_path = create_folder(1)
            break
        elif answer == False:
            folder_path = create_folder(0)
            break
        else:
            print("Please write 'True' or 'False'.")

    print(f"printing in folder: {folder_path}")
   
    avg_latency, ping_loss = ping(duration, host_name, folder_path)
    path = run_iperf3(duration, host_name, folder_path)
    goodput, pps, udp_jitter = calculate_kpis_from_iperf3(host_name, folder_path, path)
    analyze_mavlink(folder_path)
    template = Path("../src/current_template.txt").read_text().strip()
    
    # --- Define SLA targets for templates ---
    if(template == "X"):
         SLA_TARGETS = {"latency_ms": 100, "udp_jitter_ms": 30, "packet_loss_pct": 0.5, "goodput_mbps": 0.128}
    elif(template == "Y"):   
         SLA_TARGETS = {"latency_ms": 150, "udp_jitter_ms": 50, "packet_loss_pct": 1.0, "goodput_mbps": 2.0}
    else:
        print("cant find template")
    
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
    new_lines.append("\n ========= KPI SUMMARY =========")
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
            

