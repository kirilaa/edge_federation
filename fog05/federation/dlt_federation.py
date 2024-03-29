from fog05 import FIMAPI
from fog05_sdk.interfaces.FDU import FDU
import uuid
import json
import sys
import os
import time
from web3 import Web3, HTTPProvider, IPCProvider
from web3.contract import ConciseContract

blockchain_ip = "163.117.140.69"
blockchain_port = "7545"
web3= Web3(Web3.WebsocketProvider("ws://"+blockchain_ip+":"+blockchain_port))
abi_path = "../../smart-contracts/build/contracts/"
with open(abi_path+"Federation.json") as c_json:
    contract_json = json.load(c_json)

contract_abi = contract_json["abi"]
contract_address = Web3.toChecksumAddress('0xc76d33f788a17fe014b9E8D00505FA51F9804f97')

Federation_contract = web3.eth.contract(abi= contract_abi, address = contract_address)

coinbase = web3.eth.coinbase
eth_address = web3.eth.accounts
block_address = ""
service_id = ""


####### README ######
#
#  Update n1 and n2 according to your node ids in the two domains.
#

n1 = 'dc02633d-491b-40b3-83be-072748142fc4' #fog02
n2 = '1e03d6b9-908e-44e6-9fc2-3282e38c442d' #fog01

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

def filterOutBytes(string):
    result = string.split('\x00')
    if len(result)>0:
        return result[0]
    else:
        return string

def packNetData(net_info):
    net = {}
    uuid = net_info['uuid'].split('-')
    if len(uuid)< 6:
        net["uuid_1"] = uuid[0] + "-" + uuid[1] + "-" + uuid[2]
        net["uuid_2"] = uuid[3] + "-" + uuid[4]
    net['name'] = net_info['name']+';'+net_info['net_type']+';'+str(net_info['port'])+';'+str(net['vni'])
    print("Packed OK") if Web3.is_encodable('bytes32', Web3.toBytes(text= net['name'])) else print("Packing failed!")
    net['net_type'] = net_info['mcast_addr']
    net['is_mgmt'] = net_info['is_mgmt']
    return net

def UnpackNetData(service_info):
    net_info ={}
    net_info['uuid'] = filterOutBytes(web3.toText(service_info[2]))+ "-" + filterOutBytes(web3.toText(service_info[3]))
    raw_string = filterOutBytes(web3.toText(service_info[4]))
    net_info['name'] = raw_string.split(';')[0]
    net_info['net_type'] = raw_string.split(';')[1]
    net_info['port'] = raw_string.split(';')[2]
    net_info['vni'] = raw_string.split(';')[3]
    net_info['mcast_addr'] = filterOutBytes(web3.toText(service_info[5]))
    net_info['is_mgmt'] = service_info[6]

    return net_info
    
def RegisterDomain(domain_name):
    tx_hash = Federation_contract.functions.addOperator(Web3.toBytes(text=domain_name)).transact({'from': block_address})
    return tx_hash

def AnnounceService(net_info, service_id):
    need_of = "hostapd"
    uuid = net_info['uuid'].split('-')
    if len(uuid)< 6:
        e_uuid_1 = uuid[0] + "-" + uuid[1] + "-" + uuid[2]
        e_uuid_2 = uuid[3] + "-" + uuid[4]
    print("Service announced with id: ",service_id )
    new_service = Federation_contract.functions.AnnounceService(\
    _requirements= web3.toBytes(text = need_of),\
    _id = web3.toBytes(text = service_id),\
    endpoint_uuid_1= web3.toBytes(text = e_uuid_1),\
    endpoint_uuid_2= web3.toBytes(text = e_uuid_2),\
    endpoint_name= web3.toBytes(text = net_info["name"]),\
    endpoint_net_type= web3.toBytes(text = net_info["net_type"]),\
    endpoint_is_mgmt= net_info["is_mgmt"]).transact({'from':block_address})
    block = web3.eth.getBlock('latest')
    blocknumber = block['number']
    #event_filter = Federation_contract.events.NewBid.createFilter(fromBlock=web3.toHex(blocknumber), argument_filters={'_id':web3.toBytes(text= service_id)})
    event_filter = Federation_contract.events.NewBid.createFilter(fromBlock=web3.toHex(blocknumber))
    return event_filter

def GetBidInfo(bid_index, service_id):
    bid_info = Federation_contract.functions.GetBid(_id= web3.toBytes(text= service_id), bider_index= bid_index, _creator=block_address).call()
    return bid_info

def ChooseProvider(bid_index, service_id):
    chosen_provider = Federation_contract.functions.ChooseProvider(_id= web3.toBytes(text= service_id), bider_index= bid_index).transact({'from':block_address})

def GetServiceState(serviceid):
    service_state = Federation_contract.functions.GetServiceState(_id = web3.toBytes(text= serviceid)).call()
    #print("Service State: ",service_state)
    return service_state

def GetServiceInfo(service_id, is_provider):
    service_info  = Federation_contract.functions.GetServiceInfo(_id = web3.toBytes(text= service_id),\
                    provider= is_provider, call_address= block_address).call()
    # if web3.toText(service_info[0]) == service_id:
    requirement = web3.toText(service_info[1])
    net_d_info = {"uuid": (filterOutBytes(web3.toText(service_info[2]))+ "-" + filterOutBytes(web3.toText(service_info[3]))),\
            "name": filterOutBytes(web3.toText(service_info[4])), \
            "net_type": filterOutBytes(web3.toText(service_info[5])), \
            "is_mgmt": service_info[6]}
    return net_d_info
    
def ServiceAnnouncementEvent():
    block = web3.eth.getBlock('latest')
    blocknumber = block['number']
    print("\nLatest block:",blocknumber)
    event_filter = Federation_contract.events.ServiceAnnouncement.createFilter(fromBlock=web3.toHex(blocknumber))
    return event_filter

def PlaceBid(service_id):
    #Function that can be extended to send provider to consumer information
    service_price = 5
    Federation_contract.functions.PlaceBid(_id= web3.toBytes(text= service_id), _price= service_price,\
    endpoint_uuid_1= web3.toBytes(text = "hostapd"), \
    endpoint_uuid_2= web3.toBytes(text = "already"),\
    endpoint_name= web3.toBytes(text = "instansiated"),\
    endpoint_net_type= web3.toBytes(text = "running"),\
    endpoint_is_mgmt= False).transact({'from':block_address})
    block = web3.eth.getBlock('latest')
    blocknumber = block['number']
    print("\nLatest block:",blocknumber)
    event_filter = Federation_contract.events.ServiceAnnouncementClosed.createFilter(fromBlock=web3.toHex(blocknumber))
    return event_filter

def CheckWinner(service_id):
    state = GetServiceState(service_id)
    result = False
    if state == 1:
        result = Federation_contract.functions.isWinner(_id= web3.toBytes(text= service_id), _winner= block_address).call()
        print("Am I a Winner? ", result)
    return result

def ServiceDeployed(service_id):
    result = Federation_contract.functions.ServiceDeployed(info= web3.toBytes(text= "hostapd"), _id= web3.toBytes(text= service_id)).transact({'from':block_address})

def consumer(ip, fdufile, netfile):
    # Access the fog05 domain web socket
    a = FIMAPI(ip)
    # Get the nodes from the domain 
    nodes = a.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)
    # Print the nodes from the domain
    print('Nodes:')
    for n in nodes:
        print('UUID: {}'.format(n))
    
    # Load the FDU (descriptors)
    fdu_d = FDU(json.loads(read_file(fdufile)))
    # Load the network descriptor
    net_d = json.loads(read_file(netfile))
    n_uuid = net_d.get('uuid')

    # Create network based on the descriptor
    input("Press enter to create network")
    a.network.add_network(net_d)
    # Get info if the network is created
    net_info = get_net_info(a,net_d['uuid'])
    print('Net info {}'.format(net_info))
    
    # Add the created network to the node (n1)
    input('press enter to network creation')
    a.network.add_network_to_node(net_info['uuid'], n1)

    #  On-board the FDU
    input('press enter to onboard descriptor')
    res = a.fdu.onboard(fdu_d)
    # Get the identifier of the on-boarded FDU
    e_uuid = res.get_uuid()
    # Define an instance of the on-boarded FDU
    input('Press enter to define')
    inst_info = a.fdu.define(e_uuid)
    # Get the ID of the defined FDU instance
    print(inst_info.to_json())
    instid = inst_info.get_uuid()

    # Configure the defined FDU instance
    input('Press enter to configure')
    a.fdu.configure(instid)

    # Start the configured FDU instance
    input('Press enter to start')
    a.fdu.start(instid)
    # Get the info of the started FDU instance
    input('Press get info')
    info = a.fdu.instance_info(instid)
    print(info.to_json())

########## FEDERATION STARTS HERE ###########################################################
    debug_txt = input("\nUse service_id:")
    service_id = debug_txt
    net_d["net_type"] = ip
    print(net_d)
    # net_d = {"uuid": "6cc2aa30-1dcf-4c93-a57e-433fd0bd498e",\
    #         "name": "net1",\
    #         "net_type": "ELAN",\
    #         "is_mgmt": False
    #         }

    print("\nSERVICE_ID:",service_id)
    debug_txt = input("\nCreate Service anouncement....(ENTER)")
    start = time.time()
    bids_event = AnnounceService(net_d, service_id)
    bidderArrived = False
    while bidderArrived == False:
        new_events = bids_event.get_all_entries()
        for event in new_events:
            event_id = str(web3.toText(event['args']['_id']))
            print(service_id, web3.toText(event['args']['_id']), event['args']['max_bid_index'])
            #if event_id == web3.toText(text= service_id):
            bid_index = int(event['args']['max_bid_index'])
            bidderArrived = True
            if int(bid_index) < 2:
                bid_info = GetBidInfo(int(bid_index-1), service_id)
                print(bid_info)
                ChooseProvider(int(bid_index)-1, service_id)
                break
    serviceDeployed = False
    while serviceDeployed == False:
        serviceDeployed = True if GetServiceState(service_id) == 2 else False
    serviceDeployedInfo = GetServiceInfo(service_id, False)
    end = time.time()
    print(serviceDeployedInfo)
    print("SERVICE FEDERATED!")
    print("Time it took:", int(end-start))
########## FEDERATION FINISH HERE ###########################################################

    input('Press enter to terminate')
    a.fdu.terminate(instid)
    a.fdu.offload(e_uuid)
    input("Press enter to remove network")
    a.network.remove_network_from_node(n_uuid, n1)
    a.network.remove_network(n_uuid)
    
    exit(0)

def provider(ip, fdufile, netfile):
    a = FIMAPI(ip)
    # a2 = FIMAPI('163.117.139.226')
    # Get the nodes from the domain 
    nodes = a.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)
    # Print the nodes from the domain
    print('Nodes:')
    for n in nodes:
        print('UUID: {}'.format(n))
    
    # Load the FDU (descriptors)
    fdu_d = FDU(json.loads(read_file(fdufile)))

    debug_txt = input("\nBegin listening?")
    service_id = ''
    print("\nSERVICE_ID:",service_id)
    debug_txt = input("\nStart listening for federation events....(ENTER)")
    newService_event = ServiceAnnouncementEvent()
    newService = False
    open_services = []
    print("Waiting for federation event....")
    while newService == False:
        new_events = newService_event.get_all_entries()
        for event in new_events:
            service_id = web3.toText(event['args']['id'])
            if GetServiceState(service_id) == 0:
                open_services.append(service_id)
        if len(open_services) > 0:
            print("OPEN = ", len(open_services))
            newService = True
    service_id = open_services[-1]
    winnerChosen_event = PlaceBid(service_id)
    winnerChosen = False
    while winnerChosen == False:
        new_events = winnerChosen_event.get_all_entries()
        for event in new_events:
            event_serviceid = web3.toText(event['args']['_id'])
            if event_serviceid == service_id:
                winnerChosen = True
                break
    am_i_winner = CheckWinner(service_id)
    if am_i_winner == True:
        net_d = GetServiceInfo(service_id, True)
########## FEDERATED SERVICE DEPLOYEMENT HERE ###########################################################
        print(net_d)
        if net_d['uuid'] == "6cc2aa30-1dcf-4c93-a57e-433fd0bd498e": 
            print("UUID match")
            a2 = FIMAPI(net_d["net_type"])
        else:
            print("UUID does not match")

        # Create network based on the descriptor
        # input("Press enter to create network")
        # Get info if the network is created
        print(net_d['uuid'], net_d['net_type'])
        print(a2.network.list())
        net_info = get_net_info(a2,net_d['uuid'])
        print('Net info {}'.format(net_info))
        
        a.network.add_network(net_info)
        # Add the created network to the node (n1)
        input('press enter to network creation')
        a.network.add_network_to_node(net_info['uuid'], n2)

        #  On-board the FDU
        input('press enter to onboard descriptor')
        res = a.fdu.onboard(fdu_d)
        # Get the identifier of the on-boarded FDU
        e_uuid = res.get_uuid()
        # Define an instance of the on-boarded FDU
        input('Press enter to define')
        inst_info = a.fdu.define(e_uuid)
        # Get the ID of the defined FDU instance
        print(inst_info.to_json())
        instid = inst_info.get_uuid()

        # Configure the defined FDU instance
        input('Press enter to configure')
        a.fdu.configure(instid)

        # Start the configured FDU instance
        input('Press enter to start')
        a.fdu.start(instid)
        # Get the info of the started FDU instance
        input('Press get info')
        info = a.fdu.instance_info(instid)
        print(info.to_json())

######################### UNTIL HERE ####################################################################
        ServiceDeployed(service_id)
    else:
        print("I am not a Winner")

    input('Press enter to terminate')

    a.fdu.terminate(instid)
    a.fdu.offload(e_uuid)
    exit(0)

if __name__ == '__main__':
    print("Blockchin addresses:", eth_address)
    print(sys.argv)
    if len(sys.argv) < 5:
        print('[Usage] {} <flag_consumer_or_provider> <first yaks ip:port>  <path to fdu descripto> <path to net descriptor> -register(optional)'.format(
            sys.argv[0]))
        exit(0)
    if sys.argv[1] == 'consumer':
        block_address = coinbase
        if len(sys.argv) >= 6 and sys.argv[5] == "-register":
            print(sys.argv[5])
            domain_name = "AD1"
            try:
                print("Registering....")
                tx_hash = RegisterDomain(domain_name)
            except ValueError as e:
                print(e)
            finally:
                print("Starting consumer domain....")
                consumer(sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            print("Starting consumer domain....")
            consumer(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == 'provider':
        block_address = eth_address[1]
        if len(sys.argv) >= 6 and sys.argv[5] == "-register":
            domain_name = "AD2"
            try:
                print("Registering....")
                tx_hash = RegisterDomain(domain_name)
            except ValueError as e:
                print(e)
            finally:
                print("Starting provider domain....")
                provider(sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            print("Starting provider domain....")
            provider(sys.argv[2], sys.argv[3], sys.argv[4])