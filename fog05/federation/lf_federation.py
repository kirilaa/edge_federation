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


def main(ip, ip2, fdufile, fdu2, netfile):
    a = FIMAPI(ip)

    a2 = FIMAPI(ip2)

    nodes = a.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)

    print('Nodes:')
    for n in nodes:
        print('UUID: {}'.format(n))

    fdu_d = FDU(json.loads(read_file(fdufile)))
    second_fdu_d = FDU(json.loads(read_file(fdu2)))

    net_d = json.loads(read_file(netfile))

    n_uuid = net_d.get('uuid')



    n1 = '22a3296a-61d2-469f-9c16-aad648575798' #fos1
    n2 = '3e2552e6-4e79-463d-a252-464884a27847' #fos2

    input("Press enter to create network")
    a.network.add_network(net_d)
    net_info = get_net_info(a,net_d['uuid'])
    print('Net info {}'.format(net_info))


    input('press enter to network creation')
    a.network.add_network_to_node(net_info['uuid'], n1)

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


    # input('press enter to onboard second descriptor')
    # res = a.fdu.onboard(second_fdu_d)
    # s_e_uuid = res.get_uuid()
    # input('Press enter to define')
    # s_inst_info = a.fdu.define(s_e_uuid)
    # print(s_inst_info.to_json())
    # s_instid = s_inst_info.get_uuid()

    # input('Press enter to configure')
    # a.fdu.configure(s_instid)

    # input('Press enter to start')
    # a.fdu.start(s_instid)


    # input('Press enter to stop')
    # a.entity.stop(e_uuid, n1, i_uuid)
    # input('Press enter to clean')
    # a.entity.clean(e_uuid, n1, i_uuid)
    # input('Press enter to undefine')
    # a.entity.undefine(e_uuid, n1)

    # input('Press enter to migrate')
    input('Press get info')
    info = a.fdu.instance_info(instid)
    print(info.to_json())

    # input('Press get info')
    # info = a.fdu.instance_info(s_instid)
    # print(info.to_json())


    input('Press to move client to second domain')
    net_info = get_net_info(a,net_d['uuid'])
    input('Press to create federated vxlan to second domain')
    a2.network.add_network(net_info)

    net_info2 = get_net_info(a2,net_info['uuid'])
    print('Net info {}'.format(net_info2))
    a2.network.add_network_to_node(net_info2['uuid'], n2)

    # input('remove client from first domain')
    # a.fdu.terminate(s_instid)
    # a.fdu.offload(s_e_uuid)

    input('press enter to onboard second descriptor')
    res = a2.fdu.onboard(second_fdu_d)
    s_e_uuid = res.get_uuid()
    input('Press enter to define')
    s_inst_info = a2.fdu.define(s_e_uuid)
    print(s_inst_info.to_json())
    s_instid = s_inst_info.get_uuid()

    input('Press enter to configure')
    a2.fdu.configure(s_instid)

    input('Press enter to start')
    a2.fdu.start(s_instid)

    input('Press get info')
    info = a2.fdu.instance_info(s_instid)
    print(info.to_json())



    #res = a.entity.migrate(e_uuid, i_uuid, n1, n2)
    #print('Res is: {}'.format(res))
    input('Press enter to terminate')

    a.fdu.terminate(instid)
    a.fdu.offload(e_uuid)
    a2.fdu.terminate(s_instid)
    a2.fdu.offload(s_e_uuid)
    input("Press enter to remove network")
    a.network.remove_network_from_node(n_uuid, n1)
    a.network.remove_network(n_uuid)

    exit(0)


if __name__ == '__main__':
    if len(sys.argv) < 6:
        print('[Usage] {} <first yaks ip:port>  <second yaks ip:port> <path to fdu descripto> <path to second fdu descriptor> <path to net descriptor>'.format(
            sys.argv[0]))
        exit(0)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
