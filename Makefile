
# Define Python interpreter
PYTHON = python3

.PHONY: run controller topology

help:
	@echo "Makefile:"
	@echo "If you want to run the program write in your terminal: run"
	@echo "To exit the xterm write in terminal: kill"

# Open xterm for the Ryu controller
controller:
	xterm -hold -e "sudo -E ~/venv-ryu39/bin/ryu-manager --ofp-tcp-listen-port 6653 ./src/sdn_controller.py --verbose" &

# Open xterm for the topology script
topology:
	xterm -hold -e "sudo -E python3 src/topology.py" &

# Run both
run: controller topology

kill:
	killall xterm
	sudo mn -c
