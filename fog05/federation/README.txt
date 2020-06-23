For federation experiment.


Install two separated fog05 domain.

Each domain has its own Zenoh.


Use the attached debian files for the agent and the networking plugin.

Install the python3 api and sdk from github.


git clone https://github.com/gabrik/api-python -b feature-detailed-vxlan-interface-creation
git clone https://github.com/gabrik/sdk-python -b feature-detailed-vxlan-interface-creation
pip3 install sphinx pyangbind
cd sdk-python && make && sudo make install && cd ..
cd api-python && sudo make install && cd ..


Then start fog05 in the two domain as usual (via systemd)


Usage of the lf_federation.py script.

This script creates a network and a container in the first domain, then gets the network information from the first domain and creates a client container connected to the same network for the first domain.
You need to update the n1 and n2 variables in the file.


Usage:
    python3 lf_federation.py <first zenoh> <second zenoh> <first fdu descriptor> <second fdu descriptor> <network descriptor>

Example:
python3 lf.py 127.0.0.1:7447 192.168.100.156:7447 fdu_dhcp.json fdu_client.json net.json


