import sys
import json
import shlex
import subprocess
from pathlib import Path
from .measure import get_kpi, create_folder
from .measure import ping, run_iperf3, create_folder
import time

def provision(template: str):
    """Provision {"template":"X"} – create the Virtual QoS Link"""
    print(f"[API] Creating the Virtual QoS Link with template: {template}")
    
    Path("../src/current_template.txt").write_text(template)
    

    #time.sleep(1)
    print(f"[API] Link provisioned with template {template}")
    
    return 0

def measure(duration: int = 60, host_name: str = 'UAV_1', scenario=None):
    """POST /measure {"duration":60} – run KPI collection."""
 
    get_kpi(duration, host_name, scenario)
    
    print("[API] KPI measurement completed.")

def report():
    """GET /report – fetch results."""

    print("[API] Fetching KPI report...")
    folder_path = create_folder(0)
    data = Path(folder_path / "kpi_results.txt").read_text()
    print("\n \n \n")
    print(data)

def teardown():
    """Remove QoS rules."""
    
    print("[API] Tearing down QoS link...")
    Path("../src/current_template.txt").unlink(missing_ok=True)
    print("[API] Link removed.")

def main():
#   in terminal:
#   UAV_1 python3 src/client.py provision X
#   UAV_1 python3 src/client.py measure 2 "UAV_1" True
#   UAV_1 python3 src/client.py report
#   UAV_1 python3 src/client.py teardown
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "provision":
            template = sys.argv[2] if len(sys.argv) > 2 else "X"
            provision(template)
        elif cmd == "measure":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            host_name = sys.argv[3] if len(sys.argv) > 3 else "UAV_1"
            folder = sys.argv[4]
            measure(duration, host_name, folder)

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
