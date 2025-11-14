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
    
    for i in range(repeat):
        print(f"\n=== Running scenario '{scenario['scenario_name']}, iteration {i+1} ===n")
        for step in scenario.get("templates", []):
            template = step['template']
            duration = step['duration']
            
            print(f"\n[TEST] Applying template: {template} for {duration}s±n")
            provision(template)
            
            for host in hosts:
                print(f"[TEST] Measuring KPIs for {host}")
                measure(duration, host)
        
        print("\n[TEST] All templates applied, fetchng report...")
        report()
        teardown()
        print("\n[TEST] Scenario completed.\n")
    
if __name__ == "__main__":
    scenario_file = "scenario1.yaml"
    scenario = load_scenario(scenario_file)
    run_scenario(scenario)