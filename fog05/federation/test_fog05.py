from fog05 import FIMAPI
from fog05_sdk.interfaces.FDU import FDU
import uuid
import json
import sys
import os

####### README ######
#
#  Update n1 and n2 according to your node ids in the two domains.
#

def read_file(filepath):
    with open(filepath, 'r') as f:
        data = f.read()
    return data


def get_net_info(api, netid):
    nets = api.network.list()
    ni = [x for x in nets if x['uuid'] == netid]
    if len(ni) > 0:
        return ni[0]
    return None


def main(ip, fdufile, netfile):
    a = FIMAPI(ip)
    nodes = a.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)

    print('Nodes:')
    for n in nodes:
        print('UUID: {}'.format(n))

    fdu_d = FDU(json.loads(read_file(fdufile)))
    

    net_d = json.loads(read_file(netfile))

    n_uuid = net_d.get('uuid')



    n1 = '1e03d6b9-908e-44e6-9fc2-3282e38c442d' #fog01
    n2 = 'dc02633d-491b-40b3-83be-072748142fc4' #fog02

    input("Press enter to create network")
    a.network.add_network(net_d)
    net_info = get_net_info(a,net_d['uuid'])
    print('Net info {}'.format(net_info))


    input('press enter to network creation')
    a.network.add_network_to_node(net_info['uuid'], n2)

    input('press enter to onboard descriptor')
    res = a.fdu.onboard(fdu_d)
    e_uuid = res.get_uuid()
    input('Press enter to define')
    inst_info = a.fdu.define(e_uuid)
    print(inst_info.to_json())
    instid = inst_info.get_uuid()

    input('Press enter to configure')
    a.fdu.configure(instid)

    input('Press enter to start')
    a.fdu.start(instid)

    input('Press get info')
    info = a.fdu.instance_info(instid)
    print(info.to_json())


    #res = a.entity.migrate(e_uuid, i_uuid, n1, n2)
    #print('Res is: {}'.format(res))
    input('Press enter to terminate')

    a.fdu.terminate(instid)
    a.fdu.offload(e_uuid)
    input("Press enter to remove network")
    a.network.remove_network_from_node(n_uuid, n2)
    a.network.remove_network(n_uuid)

    exit(0)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('[Usage] {} <first yaks ip:port> <path to fdu descripto> <path to net descriptor>'.format(
            sys.argv[0]))
        exit(0)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
