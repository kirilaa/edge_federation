from fog05 import FIMAPI
from fog05_sdk.interfaces.FDU import FDU
import paho.mqtt.client as mqtt
import uuid
import json
import sys
import os
import time
import math
from time import gmtime, strftime
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

################### MQTT ###################################

ap_x = float(30.4075826699)
ap_y = float(-7.67201633367)

def compute_distance(x,y):
    distance = float((x-ap_x)*(x-ap_x) + (y-ap_y)*(y-ap_y))
    return math.sqrt(distance)

MQTT_IP="192.168.122.3"
MQTT_PORT=1883
MQTT_TOPIC="/experiment/location"
robot_connected = False
mqtt_federation_trigger = False
mqtt_federation_usage = False
entered_in_the_close_range = False

start_federation_distance = float(6.0)

def on_connect(client, userdata, flags, rc):

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global entered_in_the_close_range
    global mqtt_federation_trigger
    global start_federation_distance
    print('received message: \n%s over topic: %s' % (msg,
        MQTT_TOPIC))
    print('received message %s' % str(msg.payload))


    # Check for byte encoding just in case
    if type(msg.payload) == bytes:
        message = json.loads(msg.payload.decode("UTF-8"))
    else:
        message = json.loads(msg.payload)

    if "center" in message and len(message["center"])>0:
        distance = compute_distance(float(message["center"][0]), float(message["center"][1]))
        print("Distance:", distance)
        #MQTT_MSG=json.dumps({"center": [x1,y1],"radius":  3});
        #Customer ap coordinates: x: 30.4075826699 y: -7.67201633367
        if distance < start_federation_distance:
            # entered_in_the_close_range = True
            print("Triggered Federation!")
            mqtt_federation_trigger = True
        # elif entered_in_the_close_range == True and distance > start_federation_distance:
        else:
            mqtt_federation_trigger = False
    
    if "connected" in message:
        print("Robot connection message")
        if message["connected"] == True:
            print("Robot connected True")
            robot_connected = True
        else:
            print("Robot connected False")
            robot_connected = False

#___________________________________________________________

measurement = {}
start_measured = False
result_path= "../../results/"

def measure(label):
    if label == 'start':
        measurement["start"] = time.time()
    elif label == 'end':
        measurement["end"] = time.time() - measurement['start']
        result_string = strftime("%H%M", gmtime()) + "_"+ measurement['domain']
        result_file = result_path+"result"+ result_string +'.json'
        with open(result_file, 'w') as result_json:
            json.dump(measurement, result_json)
    elif label == '':
        measurement[int(time.time())] = time.time() - measurement['start']
        print("Time without label registered")
    else:
        measurement[label] = time.time()-measurement['start']


####### README ######
#
#  Update n1 and n2 according to your node ids in the two domains.
#
DESC_FOLDER = 'descriptors'
net_desc = ['net.json']
descs_d1 = ['fdu_dhcp.json','ap1.json']
descs_d2 = ['ap2.json']

d1_n1 = 'dc02633d-491b-40b3-83be-072748142fc4' #fog02
d1_n2 = 'c9f23aef-c745-4f58-bd59-3603fc1721b6' #fog03
d2_n1 = '1e03d6b9-908e-44e6-9fc2-3282e38c442d' #fog01

IP1 = "163.117.139.226"
IP2 = "163.117.139.70"

def restartBrainMachine():
    stream = os.popen('virsh list')
    virsh_list = stream.read()
    virsh_list = virsh_list.split("brain_kiril")
    if len(virsh_list) == 2 and "running" in virsh_list[1]:
        stream = os.popen('virsh shutdown brain_kiril')
        print("Brain is shutting down")
        shutdown = False
        while shutdown == False:
            stream = os.popen('virsh list')
            virsh_list = stream.read()
            virsh_list = virsh_list.split("brain_kiril")
            if len(virsh_list) == 1:
                shutdown = True
        stream = os.popen('virsh start brain_kiril')
        virsh_started = stream.read()
        print("Brain has started")
        
    

def generateServiceId():
    time_string = strftime("%H%M", gmtime())
    service_id = "service"+ time_string
    return service_id

def read_file(filepath):
    with open(filepath, 'r') as f:
        data = f.read()
    return data

def read(filepath):
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

def net_deploy(network_desc,api,node):
    for d in network_desc:
        path_d = os.path.join(DESC_FOLDER,d)
        net_d = json.loads(read(path_d))
        n_uuid = net_d.get('uuid')
        # input("Press enter to create network")
        net_info = get_net_info(api,net_d['uuid'])
        if net_info is None:
            api.network.add_network(net_d)
        net_info = get_net_info(api,net_d['uuid'])
        print('Net info {}'.format(net_info))
        # input('press enter to network creation')
        api.network.add_network_to_node(net_info['uuid'], node)
        time.sleep(1)

def container_deploy(descs,api):
    for d in descs:
        path_d = os.path.join(DESC_FOLDER,d)
        fdu_d = FDU(json.loads(read(path_d)))
        # input('press enter to onboard descriptor')
        measure('on_board_'+d)
        res = api.fdu.onboard(fdu_d)
        e_uuid = res.get_uuid()
        # input('Press enter to define')
        inst_info = api.fdu.define(e_uuid)
        print(inst_info.to_json())
        instid = inst_info.get_uuid()
        measure('configure_'+d)
        # input('Press enter to configure')
        api.fdu.configure(instid)
        measure('start_'+d)
        # input('Press enter to start')
        api.fdu.start(instid)
        measure('info_'+d)
        # input('Press get info')
        info = api.fdu.instance_info(instid)
        print(info.to_json())

def packNetData(net_info):
    net = {}
    uuid = net_info['uuid'].split('-')
    if len(uuid)< 6:
        net["uuid_1"] = uuid[0] + "-" + uuid[1] + "-" + uuid[2]
        net["uuid_2"] = uuid[3] + "-" + uuid[4]
    net['name'] = net_info['name']+';'+net_info['net_type']+';'+str(net_info['port'])+';'+str(net_info['vni'])
    net_name_bytes = web3.toBytes(text= net['name'])
    print("Packed OK") if web3.is_encodable(_type= 'bytes32', value= net_name_bytes) else print("Packing failed!")
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

def AnnounceService(net_info, service_id, trusty):
    if trusty == 'untrusty':
        net_info = packNetData(net_info)
        new_service = Federation_contract.functions.AnnounceService(\
        _requirements= web3.toBytes(text = trusty),\
        _id = web3.toBytes(text = service_id),\
        endpoint_uuid_1= web3.toBytes(text = net_info["uuid_1"]),\
        endpoint_uuid_2= web3.toBytes(text = net_info["uuid_2"]),\
        endpoint_name= web3.toBytes(text = net_info["name"]),\
        endpoint_net_type= web3.toBytes(text = net_info["net_type"]),\
        endpoint_is_mgmt= net_info["is_mgmt"]).transact({'from':block_address})
    else:
        uuid = net_info['uuid'].split('-')
        if len(uuid)< 6:
            e_uuid_1 = uuid[0] + "-" + uuid[1] + "-" + uuid[2]
            e_uuid_2 = uuid[3] + "-" + uuid[4]
        print("Service announced with id: ",service_id )
        new_service = Federation_contract.functions.AnnounceService(\
        _requirements= web3.toBytes(text = trusty),\
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
    requirement = filterOutBytes(web3.toText(service_info[1]))
    if requirement == 'untrusty':
        net_d_info = UnpackNetData(service_info)
        net_d_info["privacy"] = requirement
    else:
        net_d_info = {"uuid": (filterOutBytes(web3.toText(service_info[2]))+ "-" + filterOutBytes(web3.toText(service_info[3]))),\
                "name": filterOutBytes(web3.toText(service_info[4])), \
                "net_type": filterOutBytes(web3.toText(service_info[5])), \
                "is_mgmt": service_info[6],
                "privacy": requirement}
        
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
    endpoint_uuid_2= web3.toBytes(text = "ready"),\
    endpoint_name= web3.toBytes(text = "04:f0:21:4f:fe:0a"),\
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

def consumer(trusty):
    global mqtt_federation_trigger
    global robot_connected
    #Configure measurements
    measurement["domain"] = 'consumer'
    # measure('start')
    # Access the fog05 domain web socket
    a = FIMAPI(IP1)
    # Get the nodes from the domain 
    nodes = a.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)
    # Print the nodes from the domain
    print('Nodes:')
    for n in nodes:
        print('UUID: {}'.format(n))

    # measure('net_deploy_1')
    # # input('Press to deploy net on consumer domain')
    # time.sleep(1)
    # net_deploy(net_desc,a,d1_n1)
    # measure('net_deploy_2')
    # time.sleep(1)
    # net_deploy(net_desc,a,d1_n2)
    # time.sleep(1)
    # # input('Press to deploy containers on consumer domain')
    # container_deploy(descs_d1,a)
    path_d = os.path.join(DESC_FOLDER,net_desc[0])
    net_d = json.loads(read(path_d))
    time.sleep(1)
    net_info = get_net_info(a,net_d['uuid'])
    # measure('collect_net_info')
    # restartBrainMachine()
    # measure("brain_start")

########## FEDERATION STARTS HERE ###########################################################
    measure('start')
    service_id = generateServiceId()
    print("SERVICE ID to be used: ", service_id)
    if trusty == 'trusty':
        net_info["net_type"] = IP1
    print(net_info)
    if mqtt_federation_usage:
        #Configure Mqtt
        client = mqtt.Client(None, clean_session=True)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_IP, MQTT_PORT, 60)
        client.loop_start()
        print("Waiting for Federation request via MQTT\n")
        while mqtt_federation_trigger == False:
            # print(".")
            time.time()
        print("continued")
        client.loop_stop()
    else: 
        print("\nSERVICE_ID:",service_id)
        debug_txt = input("\nCreate Service anouncement....(ENTER)")
    start = time.time()
    bids_event = AnnounceService(net_info, service_id, trusty)
    measure('request_federation')
    newService_event = ServiceAnnouncementEvent()
    check_event = newService_event.get_all_entries()
    if len(check_event) > 0:
        measure('federation_announced')
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
                measure('choosing_provider')
                bid_info = GetBidInfo(int(bid_index-1), service_id)
                print(bid_info)
                ChooseProvider(int(bid_index)-1, service_id)
                measure('provider_deploys')
                break
    serviceDeployed = False
    while serviceDeployed == False:
        serviceDeployed = True if GetServiceState(service_id) == 2 else False
    measure('federation_completed')
    serviceDeployedInfo = GetServiceInfo(service_id, False)
    end = time.time()
    print(serviceDeployedInfo)
    print("SERVICE FEDERATED!")
    print("Time it took:", int(end-start))
########## FEDERATION FINISH HERE ###########################################################
    if mqtt_federation_usage:
        MQTT_MSG=json.dumps({"mac": serviceDeployedInfo["name"]})
        client.publish("/experiment/allocation",MQTT_MSG)
        measure('robot_migration')
        client.subscribe("/robot/connection")
        client.loop_start()
        print("Robot connecting to the new AP.....")
        while robot_connected == False:
            time.time()
        measure('robot_connected')
        client.loop_stop()
        print("Robot has connected!") 
    measure('end')
    input('Press enter to exit (cointainers and networks not terminated)')
    # input('Press enter to terminate')
    # a.fdu.terminate(instid)
    # a.fdu.offload(e_uuid)
    # input("Press enter to remove network")
    # a.network.remove_network_from_node(n_uuid, n1)
    # a.network.remove_network(n_uuid)
    
    exit(0)

def provider():
    measurement["domain"] = 'provider'
    # a = FIMAPI(ip)
    provider_domain = FIMAPI(IP2)
    # a2 = FIMAPI('163.117.139.226')
    # Get the nodes from the domain 
    # nodes = provider_domain.node.list()
    # if len(nodes) == 0:
    #     print('No nodes')
    #     exit(-1)
    # # Print the nodes from the domain
    # print('Nodes:')
    # for n in nodes:
    #     print('UUID: {}'.format(n))
    
    # # Load the FDU (descriptors)
    # path_d = os.path.join(DESC_FOLDER,descs_d2[0])
    # fdu_d = FDU(json.loads(read(path_d)))

    # debug_txt = input("\nBegin listening?")
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
            measure('start')
            print("OPEN = ", len(open_services))
            newService = True
    service_id = open_services[-1]
    measure('bid_placed')
    winnerChosen_event = PlaceBid(service_id)
    winnerChosen = False
    while winnerChosen == False:
        new_events = winnerChosen_event.get_all_entries()
        for event in new_events:
            event_serviceid = web3.toText(event['args']['_id'])
            if event_serviceid == service_id:
                measure('winner_choosen')
                winnerChosen = True
                break
    am_i_winner = CheckWinner(service_id)
    if am_i_winner == True:
        measure('deployment_start')
        net_d = GetServiceInfo(service_id, True)
########## FEDERATED SERVICE DEPLOYEMENT HERE ###########################################################
        print(net_d)
        if net_d['privacy'] == "trusty": 
            print("Trusty federation")
            # a2 = FIMAPI(net_d["net_type"])
            measure('trusty_info_get')
            consumer_domain = FIMAPI(net_d["net_type"])
            net_info = get_net_info(consumer_domain,net_d['uuid'])
            print(consumer_domain.network.list())
            print('Net info {}'.format(net_info))
        else:
            measure('untrusty_info_get')
            print("Untrusty federation")
            net_info = net_d
            
        # Create network based on the descriptor
        # input("Press enter to create network")
        # Get info if the network is created
        print(net_d['uuid'], net_d['net_type'])
        
        measure('net_deploy')
        provider_domain.network.add_network(net_info)
        # Add the created network to the node (n1)
        # input('press enter to network creation')
        measure('net_add')
        time.sleep(1)
        provider_domain.network.add_network_to_node(net_info['uuid'], d2_n1)

        measure('container_deploy')
        time.sleep(1)
        # input('press enter to onboard on provider domain')
        container_deploy(descs_d2,provider_domain)
    
        # #  On-board the FDU
        # input('press enter to onboard descriptor')
        # res = a.fdu.onboard(fdu_d)
        # # Get the identifier of the on-boarded FDU
        # e_uuid = res.get_uuid()
        # # Define an instance of the on-boarded FDU
        # input('Press enter to define')
        # inst_info = a.fdu.define(e_uuid)
        # # Get the ID of the defined FDU instance
        # print(inst_info.to_json())
        # instid = inst_info.get_uuid()

        # # Configure the defined FDU instance
        # input('Press enter to configure')
        # a.fdu.configure(instid)

        # # Start the configured FDU instance
        # input('Press enter to start')
        # a.fdu.start(instid)
        # # Get the info of the started FDU instance
        # input('Press get info')
        # info = a.fdu.instance_info(instid)
        # print(info.to_json())

######################### UNTIL HERE ####################################################################
        measure('deployment_finished')
        ServiceDeployed(service_id)
    else:
        print("I am not a Winner")
    measure('end')
    # input('Press enter to exit (cointainers and networks not terminated)')
    print('EXIT (cointainers and networks not terminated)')

    # provider_domain.fdu.terminate(instid)
    # provider_domain.fdu.offload(e_uuid)
    exit(0)

if __name__ == '__main__':
    print("Blockchin addresses:", eth_address)
    print(sys.argv)
    if len(sys.argv) < 2:
        print('[Usage] {} <flag_consumer_or_provider> <trusty|untrusty> -register(optional)'.format(
            sys.argv[0]))
        exit(0)
    if len(sys.argv) == 4:
        if sys.argv[3] == 'mqtt':
            mqtt_federation_usage = True
    if sys.argv[1] == 'consumer':
        block_address = coinbase
        domain_name = "AD1"
        print(sys.argv[1], sys.argv[2])
        try:
            print("Registering....")
            tx_hash = RegisterDomain(domain_name)
        except ValueError as e:
            print(e)
        finally:
            print("Starting consumer domain....")
            if sys.argv[2] == 'trusty' or sys.argv[2] == 'untrusty':
                consumer(sys.argv[2])
            else:
                print("Please use \'trusty\' or \'untrusty\' for the argument {}" .format(sys.argv[2]))
                exit(0)
    elif sys.argv[1] == 'provider':
        block_address = eth_address[1]
        domain_name = "AD2"
        try:
            print("Registering....")
            tx_hash = RegisterDomain(domain_name)
        except ValueError as e:
            print(e)
        finally:
            print("Starting provider domain....")
            provider()
    else:
        exit(0)

    # if sys.argv[1] == 'consumer' and len(sys.argv) <= 4:
    #     block_address = coinbase
    #     if len(sys.argv) == 3 and sys.argv[3] == "-register":
    #         print(sys.argv[1], sys.argv[2])
    #         domain_name = "AD1"
    #         try:
    #             print("Registering....")
    #             tx_hash = RegisterDomain(domain_name)
    #         except ValueError as e:
    #             print(e)
    #         finally:
    #             print("Starting consumer domain....")
    #             consumer(sys.argv[2])
    #     elif sys.argv[2] == 'trusty' or sys.argv[2] == 'untrusty':
    #         print("Starting consumer domain....")
    #         consumer(sys.argv[2])
    #     else:
    #         print('[Usage] {} <flag_consumer_or_provider> <trusty|untrusty> -register(optional)'.format(sys.argv[0]))
    #         exit(0)
    # elif sys.argv[1] == 'provider':
    #     block_address = eth_address[1]
    #     if len(sys.argv) >= 2 and sys.argv[2] == "-register":
    #         domain_name = "AD2"
    #         try:
    #             print("Registering....")
    #             tx_hash = RegisterDomain(domain_name)
    #         except ValueError as e:
    #             print(e)
    #         finally:
    #             print("Starting provider domain....")
    #             provider()
    #     else:
    #         print("Starting provider domain....")
    #         provider()