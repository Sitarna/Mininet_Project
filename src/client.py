# install: sudo apt install iperf3 -y
# mininet> xterm gcs &
# iperf3 -s
"""
- API (illustrative)
- POST /provision {"template":"X"} – create the Virtual QoS Link.
- POST /measure {"duration":60} – run KPI collection.
- GET /report – fetch results.
- POST /teardown – remove rules.
"""

import json
import subprocess
import time
import sys
from pathlib import Path
import os


def create_folder(c: int = 2):
    #create folder
    base_dir = Path("data")
    base_dir.mkdir(exist_ok=True)
    i = 1
    while True:
        folder_path = base_dir / f"KPI_information{i}"
        if not os.path.exists(folder_path):
            if c == 1:
                folder_path.mkdir()
                print(f"Created folder: {folder_path}")
                return folder_path;
                    
            elif c == 2:
                return base_dir / f"KPI_information{i-1}"   
            break
    
        else:
            i += 1
    
    
# integrate with Ryu later
def provision(template: str):
    """Provision {"template":"X"} – create the Virtual QoS Link"""
    print(f"[API] Creating the Virtual QoS Link with template: {template}")
    
    Path("current_template.txt").write_text(template)

    time.sleep(1)
    print(f"[API] Link provisioned with template {template}")
    return {"status": "ok", "template": template}


def measure(duration: int = 60, host_name: str = 'UAV_1'):
    """Run KPI measurement between GCS and UAV"""
    print(f"[API] Measuring KPIs for {duration}s...")
    new_lines = []
    new_lines.append(f"=========   KPI MESURMENTS {host_name}  ===========")
    new_lines.append("KPI: Latency, Jitter, Packet loss, Goodput \n")
    new_lines.append("ping test (RTT + loss)")
    
    # ping test (RTT + loss)
    cmd = ["ping", "-c", str(duration), "10.0.0.1"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        
    name_map = {
    "min": "fastest packet",
    "avg": "avrage Latency",
    "max": "slowest packet",
    "mdev":"        Jitter"
    }

    for line in result.stdout.splitlines():
        if line.startswith("rtt min/avg/max"):
            labels_part, values_part = line.split("=")
            labels = labels_part.strip().split()[1].split("/")      
            values = values_part.strip().replace(" ms", "").split("/")
            new_lines.extend([f"{name_map[label]} = {value} ms" for label, value in zip(labels, values)])
        
        elif "packets transmitted" in line:
            parts = [part.strip() for part in line.split(",")]
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
                    key, value = part, ""
                new_lines.append(f"{key} = {value}")
        else:
            new_lines.append(line)
            

    while True:
            print("Do you want to create a new folder? (y/n): ", end="")
            answer = input().strip().lower()

            if answer in ('y', 'yes'):
                folder_path = create_folder(1)
                break
            elif answer in ('n', 'no'):
                folder_path = create_folder(2)
                break
            else:
                print("Please write 'y' or 'n'.")
        

    kpi_file = folder_path / "kpi_results.txt"
    with kpi_file.open("a") as f:
        f.write("\n".join(new_lines) + "\n\n")


    print("[API] KPI measurement completed.")
    return {"status": "ok", "duration": duration}


def report():
    """Return KPI report as JSON."""
    print("[API] Fetching KPI report...")
    folder_path = create_folder(2)
    data = Path(folder_path / "kpi_results.txt").read_text()
    print(data)
    return report


def teardown():
    """Remove QoS rules."""
    print("[API] Tearing down QoS link...")
    Path("current_template.txt").unlink(missing_ok=True)
    print("[API] Link removed.")
    return {"status": "ok"}


def main():
#   in terminal:
#   UAV_1 python3 src/client.py provision
#   UAV_1 python3 src/client.py measure 2 "UAV_1"
#   UAV_1 python3 src/client.py report
#   UAV_1 python3 src/client.py teardown
#
#
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "provision":
            template = sys.argv[2] if len(sys.argv) > 2 else "X"
            provision(template)
        elif cmd == "measure":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            host_name = sys.argv[3] if len(sys.argv) > 3 else "UAV_1"
            measure(duration, host_name)

        elif cmd == "report":
            report()
        elif cmd == "teardown":
            teardown()
        else:
            print(f"Unknown command {cmd}")
    else:
        print("ERROR")
        print("you have to write: host python3 client.py [provision|measure|report|teardown] [args] [host]")
        
    
        


if __name__ == "__main__":
    main()
