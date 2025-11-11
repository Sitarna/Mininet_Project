
# Define Python interpreter
PYTHON = python3

.PHONY: run controller topology

help:
	@echo "Makefile:"
	@echo "  make run         - Start controller + topology"
	@echo "  make controller  - Start only the Ryu controller"
	@echo "  make topology    - Start only the Mininet topology"
	@echo "  make kill        - Close all xterms and clean up Mininet"


# Open xterm for the Ryu controller
controller:
	xterm -hold -e "sudo -E ~/venv-ryu39/bin/ryu-manager --ofp-tcp-listen-port 6653 ./src/sdn_controller.py --verbose" &

# Open xterm for the topology script
topology:
	xterm -hold -e "sudo -E python3 src/topology.py" &

# Run controller, topolog
run: controller topology

kill:
	killall xterm
	sudo mn -c



