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
from web3.providers.rpc import HTTPProvider
from web3.contract import ConciseContract
from web3.middleware import geth_poa_middleware

DESC_FOLDER = '../descriptors'
net_desc = ['net.json']
descs_d1 = ['gw.json','radius.json','ap2.json']
descs_d2 = ['ap1.json']

d1_n1 = 'dc02633d-491b-40b3-83be-072748142fc4' #fog02
d1_n2 = '1e03d6b9-908e-44e6-9fc2-3282e38c442d' #fog01
d2_n1 = 'c9f23aef-c745-4f58-bd59-3603fc1721b6' #fog03

federation_ContractAddress = "0x38B1Fc2FC3AE46D3f94ACEAa16e48E7e2141Ad63"

node_IP_address = ''
coinbase = ''
Federation_contract = {}
web3 = {}
abi_path = "../../../smart-contracts/build/contracts/"

result_path= "../../../results/"
record = {}

ap_x = float(30.4075826699)
ap_y = float(-7.67201633367)

MQTT_IP="192.168.122.3"
MQTT_PORT=1883
MQTT_TOPIC="/experiment/location"
robot_connected = False
mqtt_federation_trigger = False
mqtt_federation_usage = False
entered_in_the_close_range = False

start_federation_distance = float(4.0)

#___________________________________________________________

def compute_distance(x,y):
    distance = float((x-ap_x)*(x-ap_x) + (y-ap_y)*(y-ap_y))
    return math.sqrt(distance)

def on_connect(client, userdata, flags, rc):

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global entered_in_the_close_range
    global mqtt_federation_trigger
    global start_federation_distance
    global robot_connected
    print('received message: \n%s over topic: %s' % (msg,
        MQTT_TOPIC))
    # print('received message %s' % str(msg.payload))


    # Check for byte encoding just in case
    if type(msg.payload) == bytes:
        message = json.loads(msg.payload.decode("UTF-8"))
    else:
        message = json.loads(msg.payload)

    if "center" in message and len(message["center"])>0:
        distance = compute_distance(float(message["center"][0]), float(message["center"][1]))
        print("Distance:", distance)
        
        if distance < start_federation_distance:
            print("Triggered Federation!")
            mqtt_federation_trigger = True
        
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


def ConfigureWeb3():
    global node_IP_address
    global coinbase
    global Federation_contract
    global web3 
    # global abi_path
    socket_string = "ws://"+node_IP_address+":7545"
    # Configure the web3 interface to the Blockchain and SC
    web3= Web3(Web3.WebsocketProvider(socket_string))
    # web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    with open(abi_path+"Federation.json") as c_json:
        contract_json = json.load(c_json)

    contract_abi = contract_json["abi"]
    contract_address = Web3.toChecksumAddress(federation_ContractAddress)
    Federation_contract = web3.eth.contract(abi= contract_abi, address = contract_address)
    coinbase = web3.eth.coinbase

def RegisterDomain(host_id):
    operator_string = 'AD'+str(host_id)
    print("Registering:", operator_string)
    try:
        tx_hash = Federation_contract.functions.addOperator(Web3.toBytes(text=operator_string)).transact({'from': coinbase})
        return True
    except:
        return False

def isRegistered(host_id):
    operator_string = 'AD'+str(host_id)
    print("Is Registered?:", operator_string)
    # if host_id == 30:
    #     operator_string = 'AD0'
    try:
        print("Already registered: ", web3.toText(Federation_contract.functions.getOperatorInfo(coinbase).call()))
        return True
    except:
        return False

def startProfiling(node_id, state):
    start_measure_string = "none"
    if int(node_id) == 37:
        start_measure_string = "ssh netcom@163.117.140.34 \"screen -d -m python /home/netcom/measure.py "+str(state)+"\""
    elif int(node_id) == 245:
        start_measure_string = "ssh netcom@163.117.140.25 \"screen -d -m python /home/netcom/measure.py "+str(state)+"\""
    else: 
        start_measure_string = "ssh uc3m@163.117.140.35 \"screen -d -m python /home/uc3m/measure.py "+str(state)+"\""
    if start_measure_string != "none":
        output_stream = os.system(start_measure_string)
        print("Measure profiling started")

def stopProfiling(node_id):
    stop_measure_string = "none"
    if int(node_id) == 37:
        stop_measure_string = "ssh netcom@163.117.140.34 \"killall screen\""
    elif int(node_id) == 245:
        stop_measure_string = "ssh netcom@163.117.140.25 \"killall screen\""
    else: 
        stop_measure_string = "ssh uc3m@163.117.140.35 \"killall screen\""
    if stop_measure_string != "none":
        output_stream = os.system(stop_measure_string)
        print("Measure profiling stopped")

def setBlockchainNodeIP(node_id):
    global node_IP_address
    if int(node_id) == 37:
        node_IP_address = "163.117.140.34"
    elif int(node_id) == 245:
        node_IP_address = "163.117.140.25"
    else: 
        node_IP_address = "163.117.140.35"

def measure(label):
    global record
    global result_path
    record[label] = time.time()
    if label == 'start':
        ip= getIPaddress()
        host_id = str(ip).split(".")[3]
        result_string = strftime("%H%M", gmtime()) + "_"+host_id
        startProfiling(host_id, result_string)

    if label == 'end':
        ip= getIPaddress()
        host_id = str(ip).split(".")[3]
        result_string = strftime("%H%M", gmtime()) + "_"+host_id
        stopProfiling(host_id)
        result_file = result_path + result_string +'.json'
        with open(result_file, 'w') as result_json:
            json.dump(record, result_json)

def getIPaddress():
    stream = os.popen('ip a | grep \"global dynamic\"').read()
    stream = stream.split('inet ',1)
    ip_address = stream[1].split('/',1)
    ipaddress = ip_address[0]
    return str(ipaddress)

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
    else:
        stream = os.popen('virsh start brain_kiril')
        virsh_started = stream.read()
        print("Brain has started")
        
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
    net['name'] = net_info['name']+';'+net_info['net_type']+';'+str(net_info['port']))
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
    
def SetFog05(ip_addr):
    a = FIMAPI(ip_addr)
    nodes = a.node.list()
    failed_fog05 = False
    if len(nodes) == 0:
        print('No nodes, Fog05 failed')
        failed_fog05 = True
        # exit(-1)
    # Print the nodes from the domain
    return a, failed_fog05

def setServiceID():
    #Configure the domain variables

    timestamp = int(time.time())
    service_id = str(timestamp)
    return service_id

def AnnounceService(net_info, service_id, trusty='untrusty'):
    if trusty == 'untrusty':
        net_info = packNetData(net_info)
        new_service = Federation_contract.functions.AnnounceService(\
        _requirements= web3.toBytes(text = trusty),\
        _id = web3.toBytes(text = service_id),\
        endpoint_uuid_1= web3.toBytes(text = net_info["uuid_1"]),\
        endpoint_uuid_2= web3.toBytes(text = net_info["uuid_2"]),\
        endpoint_name= web3.toBytes(text = net_info["name"]),\
        endpoint_net_type= web3.toBytes(text = net_info["net_type"]),\
        endpoint_is_mgmt= net_info["is_mgmt"]).transact({'from':coinbase})
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
        endpoint_is_mgmt= net_info["is_mgmt"]).transact({'from':coinbase})
    block = web3.eth.getBlock('latest')
    blocknumber = block['number']
    #event_filter = Federation_contract.events.NewBid.createFilter(fromBlock=web3.toHex(blocknumber), argument_filters={'_id':web3.toBytes(text= service_id)})
    event_filter = Federation_contract.events.NewBid.createFilter(fromBlock=web3.toHex(blocknumber))
    return event_filter

def GetBidInfo(bid_index, service_id):
    bid_info = Federation_contract.functions.GetBid(_id= web3.toBytes(text= service_id), bider_index= bid_index, _creator=coinbase).call()
    return bid_info

def ChooseProvider(bid_index, service_id):
    chosen_provider = Federation_contract.functions.ChooseProvider(_id= web3.toBytes(text= service_id), bider_index= bid_index).transact({'from':coinbase})

def GetServiceState(serviceid):
    service_state = Federation_contract.functions.GetServiceState(_id = web3.toBytes(text= serviceid)).call()
    #print("Service State: ",service_state)
    return service_state

def GetServiceInfo(service_id, is_provider):
    service_info  = Federation_contract.functions.GetServiceInfo(_id = web3.toBytes(text= service_id),\
                    provider= is_provider, call_address= coinbase).call()
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
    endpoint_is_mgmt= False).transact({'from':coinbase})
    block = web3.eth.getBlock('latest')
    blocknumber = block['number']
    print("\nLatest block:",blocknumber)
    event_filter = Federation_contract.events.ServiceAnnouncementClosed.createFilter(fromBlock=web3.toHex(blocknumber))
    return event_filter

def CheckWinner(service_id):
    state = GetServiceState(service_id)
    result = False
    if state == 1:
        result = Federation_contract.functions.isWinner(_id= web3.toBytes(text= service_id), _winner= coinbase).call()
        print("Am I a Winner? ", result)
    return result

def ServiceDeployed(service_id):
    result = Federation_contract.functions.ServiceDeployed(info= web3.toBytes(text= "hostapd"), _id= web3.toBytes(text= service_id)).transact({'from':coinbase})

def deploy_provider(net_d, provider_domain):
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
        net_info = json.loads(net_d)
        
    # Create network based on the descriptor
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
    container_deploy(descs_d2,provider_domain)
    return provider_domain

def deploy_consumer(fog_05):
    nodes = fog_05.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)
    
        
    time.sleep(1)
    net_deploy(net_desc,fog_05,d1_n1)
    time.sleep(1)
    net_deploy(net_desc,fog_05,d1_n2)
    time.sleep(1)
    container_deploy(descs_d1,fog_05)
    path_d = os.path.join(DESC_FOLDER,net_desc[0])
    net_d = json.loads(read(path_d))
    time.sleep(1)
    net_info = get_net_info(fog_05,net_d['uuid'])
    restartBrainMachine()
    print("Deployment finished")
    return net_info

def ConnectRobotToAP(AccessPointName):
    MQTT_MSG=json.dumps({"mac": AccessPointName})
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

def consumer(net_info, mqtt_federation_usage):
########## FEDERATION STARTS HERE ###########################################################
    service_id = setServiceID()
    print("SERVICE ID to be used: ", service_id)
    # net_info["net_type"] = ip_addr
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
    measure("federation_start")
    start = time.time()
    trusty = "untrusty"
    bids_event = AnnounceService(net_info, service_id, trusty)
    newService_event = ServiceAnnouncementEvent()
    check_event = newService_event.get_all_entries()
    # if len(check_event) > 0:
        # measure('federation_announced')
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
                measure("BidProviderChosen")
                bid_info = GetBidInfo(int(bid_index-1), service_id)
                print(bid_info)
                ChooseProvider(int(bid_index)-1, service_id)
                # measure('provider_deploys')
                break
    serviceDeployed = False
    while serviceDeployed == False:
        serviceDeployed = True if GetServiceState(service_id) == 2 else False
    serviceDeployedInfo = GetServiceInfo(service_id, False)
    end = time.time()
    print(serviceDeployedInfo)
    print("SERVICE FEDERATED!")
    print("Time it took:", int(end-start))
    measure('RobotConnecting')
########## FEDERATION FINISH HERE ###########################################################
    if mqtt_federation_usage:
        ConnectRobotToAP(serviceDeployedInfo["name"])
    else:
        input('Press enter to exit (cointainers and networks not terminated)')

def provider(fog_05):
    provider_domain = fog_05
    
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
            measure('announcementReceived')
            print("OPEN = ", len(open_services))
            newService = True
    service_id = open_services[-1]
    measure('BidIPsent')
    winnerChosen_event = PlaceBid(service_id)
    winnerChosen = False
    while winnerChosen == False:
        new_events = winnerChosen_event.get_all_entries()
        for event in new_events:
            event_serviceid = web3.toText(event['args']['_id'])
            if event_serviceid == service_id:
                measure('winnerDomainReceived')
                winnerChosen = True
                break
    am_i_winner = CheckWinner(service_id)
    if am_i_winner == True:
        measure('deployFedService')
        net_d = GetServiceInfo(service_id, True)
        provider_domain = deploy_provider(net_d, provider_domain)
        measure('fedServiceRunning')
        ServiceDeployed(service_id)
        return True
    else:
        print("I am not a Winner")
        return False
    

if __name__ == '__main__':
    ip_addr = getIPaddress()
    print("NODE IP address:",ip_addr)
    host_id = str(ip_addr).split(".")[3]
    setBlockchainNodeIP(host_id) 

    fog_05 = SetFog05(ip_addr)

    ConfigureWeb3()

    while not isRegistered(host_id):
        time.sleep(4)
        RegisterDomain(host_id)
    
    mqtt_usage = False
#CONSUMER:::::::::::::::::::::::::::::::::::::::::::::::
    if len(sys.argv)>1:
        if len(sys.argv) > 2 and sys.argv[2] == "mqtt":
            mqtt_usage = True
        if failed_fog05:
            print("Exiting because of failed Fog05")
            exit(-1)
        measure('start')
        net_info = deploy_consumer(fog_05)
        net_info["net_type"] = ip_addr
        consumer(net_info, mqtt_usage)
        question = input("Terminate the service?")
        if question != "no":
            remove_containers(fog_05)
            remove_net(fog_05,d1_n1)
            remove_net(fog_05,d1_n2)

#PROVIDER:::::::::::::::::::::::::::::::::::::::::::::::
    else:
        measure("start")
        running = provider(fog_05)
        if running:
            print("FEDERATED SERVICE IS RUNNING")
            question = input("Terminate the service?")
            if question != "no":
                remove_containers(fog_05)
                remove_net(fog_05,d2_n1)

    measure('end')    
    exit(0)

    
