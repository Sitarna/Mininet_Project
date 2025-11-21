import yaml
import time
from pathlib import Path

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.client import provision, measure, report, teardown



def load_scenario(filepath: str):
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

def run_scenario(scenario):
    hosts = scenario.get("hosts", [])
    repeat = scenario.get("repeat", 1)
    
    print(f"Scenario repeat: {repeat}")
    
    for i in range(repeat):
        print(f"\n=== Running scenario '{scenario['scenario_name']}, iteration {i+1} ===\n")
        for step in scenario.get("templates", []):
            template = step['template']
            duration = step['duration']
            
            print(f"\n[TEST] Applying template: {template} for {duration}s\n")
            provision(template)
            
            for host in hosts:
                print(f"[TEST] Measuring KPIs for {host}")
                measure(duration, host)
                #try:
                report()
                #except TypeError:
                    #print(f"SOme kind of TypeError\n")
                    
        print("\n[TEST] All templates applied, fetching report...")
        
        teardown()
        print("\n[TEST] Scenario completed.\n")
    
if __name__ == "__main__":
    print("STARTING TEST SCRIPT")
    if len(sys.argv) > 1:
        scenario_file = sys.argv[1]
    else:
        print("No scenario file specified.")
        sys.exit(1)
    print("LOADING SCENARIO")
    scenario = load_scenario(scenario_file)
    print("RUNNING SCENARIO")
    run_scenario(scenario)
    print("FINISHED")