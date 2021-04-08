from fog05 import FIMAPI
from fog05_sdk.interfaces.FDU import FDU
import uuid
import json
import sys
import os
import time

DESC_FOLDER = '.'

n1 = 'dc02633d-491b-40b3-83be-072748142fc4' #fog02
n2 = '1e03d6b9-908e-44e6-9fc2-3282e38c442d' #fog01

d1_n1 = 'dc02633d-491b-40b3-83be-072748142fc4' #fog02
d1_n2 = '1e03d6b9-908e-44e6-9fc2-3282e38c442d' #fog01
d2_n1 = 'c9f23aef-c745-4f58-bd59-3603fc1721b6' #fog03

def read_file(filepath):
    with open(filepath, 'r') as f:
        data = f.read()
    return data


def remove_containers(a):
    fdus={}

    nodes = a.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)

    print('Nodes:')
    for n in nodes:
        print('UUID: {}'.format(n))
        discs = a.fdu.list()
        for d_id in discs:
            print('d_id: '+ str(d_id))
            info = a.fdu.instance_list(d_id)
            print ('info : {}'.format(info))
            if n in info:
                time.sleep(1)
                i_ids=info[n]
                for iid in i_ids:
                    print ('Terminating iid : {}'.format(iid))
                    #a.fdu.terminate(iid)
                    #a.fdu.offload(d_id)
                    a.fdu.stop(iid)
                    time.sleep(1)
                    a.fdu.clean(iid)
                    time.sleep(1)
                    a.fdu.undefine(iid)
                    time.sleep(1)
                    a.fdu.offload(d_id)
                    time.sleep(1)


def remove_net(a,node_id):
    nets = a.network.list()
    if nets:
        print ('networks : {}'.format(nets))
        for n in nets:
            net_uuid=n['uuid']
            print ('net_id : {}'.format(net_uuid))
            a.network.remove_network_from_node(net_uuid, node_id)
            a.network.remove_network(net_uuid)


def main(ip1,ip2):
    a1 = FIMAPI(ip1)
    a2 = FIMAPI(ip2)
    remove_containers(a2)
    remove_net(a2,n2)
    remove_containers(a1)
    remove_net(a1,n1)
    

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('[Usage] {} <ip:port domain1> <ip:port domain2>'.format(
            sys.argv[0]))
        exit(0)
    main(sys.argv[1],sys.argv[2])
