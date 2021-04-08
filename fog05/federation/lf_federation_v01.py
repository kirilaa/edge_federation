from fog05 import FIMAPI
from fog05_sdk.interfaces.FDU import FDU
import uuid
import json
import sys
import os
import time

####### README ######
#
#  Update n1 and n2 according to your node ids in the two domains.
#

DESC_FOLDER = 'descriptors'
net_desc = ['net.json']
descs_d1 = ['fdu_dhcp.json','ap1.json']
descs_d2 = ['ap2.json']

d1_n1 = 'dc02633d-491b-40b3-83be-072748142fc4' #fog02
d1_n2 = '1e03d6b9-908e-44e6-9fc2-3282e38c442d' #fog01
d2_n1 = 'c9f23aef-c745-4f58-bd59-3603fc1721b6' #fog03



def read(filepath):
    with open(filepath, 'r') as f:
        data = f.read()
    return data


def get_net_info(api, netid):
    time.sleep(1)
    nets = api.network.list()
    print(nets)
    ni = [x for x in nets if x['uuid'] == netid]
    if len(ni) > 0:
        return ni[0]
    return None

def net_deploy(network_desc,api,node):
    for d in network_desc:
        path_d = os.path.join(DESC_FOLDER,d)
        net_d = json.loads(read(path_d))
        n_uuid = net_d.get('uuid')
        input("Press enter to create network")
        net_info = get_net_info(api,net_d['uuid'])
        if net_info is None:
            api.network.add_network(net_d)
        net_info = get_net_info(api,net_d['uuid'])
        print('Net info {}'.format(net_info))
        input('press enter to network creation')
        api.network.add_network_to_node(net_info['uuid'], node)
        time.sleep(1)

def container_deploy(descs,api):
    for d in descs:
        path_d = os.path.join(DESC_FOLDER,d)
        fdu_d = FDU(json.loads(read(path_d)))
        input('press enter to onboard descriptor')
        res = api.fdu.onboard(fdu_d)
        e_uuid = res.get_uuid()
        input('Press enter to define')
        inst_info = api.fdu.define(e_uuid)
        print(inst_info.to_json())
        instid = inst_info.get_uuid()
        input('Press enter to configure')
        api.fdu.configure(instid)
        input('Press enter to start')
        api.fdu.start(instid)
        input('Press get info')
        info = api.fdu.instance_info(instid)
        print(info.to_json())


def main(ip, ip2):
    a = FIMAPI(ip)

    a2 = FIMAPI(ip2)

    nodes = a.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)

    print('Nodes:')
    for n in nodes:
        print('UUID: {}'.format(n))

    input('Press to deploy net on consumer domain')
    net_deploy(net_desc,a,d1_n1)
    net_deploy(net_desc,a,d1_n2)
    input('Press to deploy containers on consumer domain')
    container_deploy(descs_d1,a)
   

    input('Press to move client to second domain')
    for d in net_desc:
        path_d = os.path.join(DESC_FOLDER,d)
        net_d = json.loads(read(path_d))
        net_info = get_net_info(a,net_d['uuid'])
        print(net_info)
        print(a2)
        input('Press to create federated vxlan to second domain')
        a2.network.add_network(net_info)
        net_info2 = get_net_info(a2,net_info['uuid'])
        print(net_info2)
        print('Net info {}'.format(net_info2))
        a2.network.add_network_to_node(net_info2['uuid'], d2_n1)


    input('press enter to onboard on provider domain')
  
    container_deploy(descs_d2,a2)
    
    print("bye")
    
    exit(0)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('[Usage] {} <first yaks ip:port>  <second yaks ip:port> '.format(
            sys.argv[0]))
        exit(0)
    main(sys.argv[1], sys.argv[2])
