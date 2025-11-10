# install: sudo apt install iperf3 -y
# mininet> xterm gcs &
#
#iperf3 -s -J -p 5201
"""
From Flavio:

Measure – While active, the server runs lightweight tests and collects
KPIs (RTT/latency, jitter p95, loss, goodput).
Report / Teardown – KPIs are exposed via API (JSON/CSV).
The link can be removed on request.

- API (illustrative)
- POST /provision {"template":"X"} – create the Virtual QoS Link.
- POST /measure {"duration":60} – run KPI collection.
- GET /report – fetch results.
- POST /teardown – remove rules.
"""
import sys
import json
import shlex
import subprocess
from pathlib import Path
from measure import get_kpi, create_folder
from measure import ping, run_iperf3, create_folder
import time


# integrate with Ryu later
# Everything in provison is temporary schould work with ryu
def provision(template: str):
    """Provision {"template":"X"} – create the Virtual QoS Link"""
    print(f"[API] Creating the Virtual QoS Link with template: {template}")
    
    Path("current_template.txt").write_text(template)

    time.sleep(1)
    print(f"[API] Link provisioned with template {template}")
    
    return 0


def measure(duration: int = 60, host_name: str = 'UAV_1'):
    """POST /measure {"duration":60} – run KPI collection."""
 
    get_kpi(duration, host_name)
    
    print("[API] KPI measurement completed.")

def report():
    """GET /report – fetch results."""

    print("[API] Fetching KPI report...")
    folder_path = create_folder(0)
    data = Path(folder_path / "kpi_results.txt").read_text()
    print("\n \n \n")
    print(data)

# should be canged with ryu
def teardown():
    """Remove QoS rules."""
    
    print("[API] Tearing down QoS link...")
    Path("current_template.txt").unlink(missing_ok=True)
    print("[API] Link removed.")


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
