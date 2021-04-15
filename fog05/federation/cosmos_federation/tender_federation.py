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

import base64
import requests
#import asyncio
# import websockets
import json
from os.path import expanduser

HOME_DIR = expanduser("~")
edge_federation_path = HOME_DIR+"/edge_federation/"

DESC_FOLDER = '../descriptors'
net_desc = ['net.json']
descs_d1 = ['gw.json','radius.json','ap1.json']
descs_d2 = ['ap2.json']

d1_n1 = 'dc02633d-491b-40b3-83be-072748142fc4' #fog02
d1_n2 = 'c9f23aef-c745-4f58-bd59-3603fc1721b6' #fog01
d2_n1 = '1e03d6b9-908e-44e6-9fc2-3282e38c442d' #fog03




result_path= "../../../results/"
record = {}
data = "\"name\""
abci_IP = ""

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


def readChainEntries():
    read_string = "ssh "+node_IP_address+"query blog list-user\""
    try:
        output_stream = os.popen(read_string).read()
        error = False
    except:
        error = True
        print("Blockchain unreachable")
    if not error:
        return output_stream

def readChainEntry(id):
    read_string = "ssh "+node_IP_address+"query blog show-user "+ str(id) + "\""
    try:
        output_stream = os.popen(read_string).read()
        error = False
    except:
        error = True
        print("Blockchain unreachable")
    if not error:
        return output_stream

def getEntriesNumber():
    output_stream = readChainEntries()
    return int(str(output_stream).split("total: ")[1].split("\n")[0].split("\"")[1])

def getLastEntry():
    # chainData = readChainEntries()
    max_id = getEntriesNumber()
    last_entry_data = readChainEntry(max_id-1)
    last_entry = str(last_entry_data).split("name: ")[1].split("\n")[0]
    last_entry_creator = str(last_entry_data).split("creator: ")[1].split("\n")[0]
    return last_entry, last_entry_creator, max_id

def getEntry(id):
    last_entry_data = readChainEntry(id)
    last_entry = str(last_entry_data).split("name: ")[1].split("\n")[0]
    return last_entry


def sendTransaction(data):
    tx_string = json.dumps(data)
    print(tx_string)
    tx_string = "ssh "+node_IP_address+"tx blog create-user " + tx_string + " --from alice -y\""
    try:
        output_stream = os.system(tx_string)
        error = False
    except:
        error = True
        print("Blockchain unreachable")

def getMatchingEntry(matching_data):
    output_stream = ReadChainEntries()
    output_stream = str(output_stream)
    matching_index = output_stream.find(str(matching_data))
    if matching_index != -1:
        matching_id_index = output_stream.find("id", matching_index-50)
        id = int(str(output_stream[matching_id_index:(matching_id_index+10)]).split("id: ")[1].split("\n")[0].split("\"")[1])
        return getEntry(id), id
    else:
        print("No entry found")
        return "No entry", -1

def getUserAddress():
    read_string = "ssh "+node_IP_address+"keys show alice\""
    try:
        output_stream = os.popen(read_string).read()
        error = False
    except:
        error = True
        print("Blockchain unreachable")
    if not error:
        address = str(output_stream).split("address: ")[1].split("\n")[0]
        return address

def startProfiling(node_id, state):
    start_measure_string = "none"
    local_measure_string = "screen -d -m python3 "+ edge_federation_path +"measure.py "+str(state)
    if int(node_id) == 37:
        start_measure_string = "ssh netcom@163.117.140.34 \"screen -d -m python /home/netcom/measure.py "+str(state)+"\""
    elif int(node_id) == 245:
        start_measure_string = "ssh netcom@163.117.140.25 \"screen -d -m python /home/netcom/measure.py "+str(state)+"\""
    else: 
        start_measure_string = "ssh uc3m@163.117.140.35 \"screen -d -m python /home/uc3m/measure.py "+str(state)+"\""
    if start_measure_string != "none":
        output_stream = os.system(start_measure_string)
        output_stream = os.system(local_measure_string)
        print("Measure profiling started")

def stopProfiling(node_id):
    stop_measure_string = "none"
    local_measure_string = "killall screen"
    if int(node_id) == 37:
        stop_measure_string = "ssh netcom@163.117.140.34 \"killall screen\""
    elif int(node_id) == 245:
        stop_measure_string = "ssh netcom@163.117.140.25 \"killall screen\""
    else: 
        stop_measure_string = "ssh uc3m@163.117.140.35 \"killall screen\""
    if stop_measure_string != "none":
        output_stream = os.system(stop_measure_string)
        output_stream = os.system(local_measure_string)
        print("Measure profiling stopped")

def setBlockchainNodeIP(node_id):
    global abci_IP
    if int(node_id) == 37:
        abci_IP = "163.117.140.34"
    elif int(node_id) == 245:
        abci_IP = "163.117.140.25"
    else: 
        abci_IP = "163.117.140.35"

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
            print('info : {}'.format(info))
            if n in info:
                time.sleep(1)
                i_ids=info[n]
                for iid in i_ids:
                    print('Terminating iid : {}'.format(iid))
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
        print('networks : {}'.format(nets))
        for n in nets:
            net_uuid=n['uuid']
            print('net_id : {}'.format(net_uuid))
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

def decodeData(data):
    decoded= base64.b64decode(data)
    return decoded.decode('ascii')

def encodeData(data):
    encoded = data.encode('ascii')
    return encoded.b64encode(encoded)

def queryChain(key):
    global abci_IP
    key = "\"" + str(key) +"\""
    PARAMS ={'data':key}
    url = "http://"+abci_IP+":26657/abci_query"
    r = requests.get(url=url, params=PARAMS)
    response = r.json()
    response = response['result']['response']['value']
    # print(response)
    if response is not None:
        response = decodeData(response)
    return response

def decode(value, stateCount):
    if value is not None:
        split_string = str(stateCount) + "_"
        value = value.split(split_string)[1]
        return value
    else:
        return value

def encode(value, stateCount):
    return str(stateCount)+"_"+value if value is not None else None

def writeChain(key,value):
    global abci_IP
    data_string = "\"" + str(key)+"="+str(value) +"\""
    PARAMS ={'tx':data_string}
    url = "http://"+abci_IP+":26657/broadcast_tx_commit"
    r = requests.post(url=url, data=PARAMS)
    response = r.json()
    if not 'error' in response:
        return True
    else:
        return False

def queryStatus():
    global abci_IP
    r = requests.get(url="http://"+abci_IP+":26657/status")
    response = r.json()
    return response

def latestBlock():
    r = queryStatus() 
    return r['result']['sync_info']['latest_block_height']


def setStateCount():
    stateCount = queryChain("stateCount")
    print("Inside state count")
    if stateCount is None:
        stateCount=int(0)
        # print "inside none"
        success = writeChain("stateCount", str(stateCount))
        if success:
            return stateCount
        else:
            return -1
    else:
        # print "inside else"
        stateCount = int(stateCount)
        stateCount = stateCount + 1
        success = writeChain("stateCount", str(stateCount))
        if success:
            return stateCount
        else:
            return -1    


def deploy_provider(winning_ip_address, net_uuid, provider_domain):
    
    consumer_domain = FIMAPI(winning_ip_address)
    net_info = get_net_info(consumer_domain,net_uuid)
    # Create network based on the descriptor
    # Get info if the network is created
    # print(net_d['uuid'], net_d['net_type'])
    
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
    # a = FIMAPI(IP1)
    # Get the nodes from the domain 
    # print('Deploying consumer nodes')
    nodes = fog_05.node.list()
    if len(nodes) == 0:
        print('No nodes')
        exit(-1)
    # Print the nodes from the domain
    # print('Nodes:')
    # for n in nodes:
    #     print('UUID: {}'.format(n))
    # measurement["domain"] = 'consumer'
        
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

def consumer(net_info, mqtt_federation_usage, ip_addr):
########## FEDERATION STARTS HERE ###########################################################
    stateCount = setStateCount()
    
    print("SERVICE ID to be used: ", str(stateCount))
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
        # print("\nSERVICE_ID:",service_id)
        debug_txt = input("\nCreate Service anouncement....(ENTER)")
    measure("federation_start")
    start = time.time()
    newBid = encode("newBid",stateCount)
    while queryChain(newBid) is not None:
        time.sleep(0.1)
    print("Bid received")
    newBidIP = encode("newBidIp",stateCount)
    while queryChain(newBidIP) is None:
        time.sleep(0.5)
    print("IP received")   
    destIP = decode(queryChain(newBidIP), stateCount)
    if destIP is not None:
        print("Destination IP:", destIP)
        destIP = str(destIP)
    srcIP = encode("newBidSrcIP", stateCount)
    ipAndNetInfo = ip_addr+";"+net_info['uuid']
    src_ip_addr = encode(ipAndNetInfo,stateCount)
    measure("BidProviderChosen")
    chosen_BidIP = encode("choosenBidDstIP", stateCount)
    chosen_BidDestIP = encode(destIP, stateCount)
    if writeChain(chosen_BidIP, chosen_BidDestIP):
        print("Chosen Dest IP address written.\n",destIP)
    if writeChain(srcIP, src_ip_addr):
        measure("BidSrcIPadded")
        print("Source IP address added.\n",ip_addr)
    serviceRunning = encode("serviceRunning", stateCount)
    print("Waiting for confirmation of service running\n")
    while queryChain(serviceRunning) is None:
        time.sleep(0.1)
          
    end = time.time()
    # print(bid_ip_address)
    print("SERVICE FEDERATED!")
    print("Time it took:", int(end-start))
    
    measure('RobotConnecting')
########## FEDERATION FINISH HERE ###########################################################
    if mqtt_federation_usage:
        ConnectRobotToAP(net_info["name"])
    else:
        input('Press enter to exit (cointainers and networks not terminated)')

def provider(fog_05, host_id, ip_addr):
    provider_domain = fog_05
    stateCount = queryChain("stateCount")
    while stateCount == queryChain("stateCount"):
        time.sleep(0.5)

    measure("announcementReceived"+str(int(stateCount)%2))          
    stateCount = int(queryChain("stateCount"))
    placeBid_key = encode("newBid",stateCount)
    placeBid_value = str(host_id)

    if not writeChain(placeBid_key, placeBid_value):
        placeBid_value = str(placeBid_value)
    print("Bid placed")
    newBidIP = encode("newBidIp",stateCount)
    destIP = ip_addr
    ip_addr = encode(ip_addr, stateCount)
    if int(queryChain(placeBid_key))== int(placeBid_value):
        # measure("DstIPplaced")
        measure("BidIPsent") 
        writeChain(newBidIP,ip_addr)
        print("IP address delivered")
    choosenBidDstIP = encode("choosenBidDstIP", stateCount)
    while queryChain(choosenBidDstIP) is None:
        time.sleep(0.5)
    measure("winnerDomainReceived") 
    print("The elected provider IP received")
    providerIP = decode(queryChain(choosenBidDstIP), stateCount)
    print("Destinatio IP: ", str(providerIP))
    print("hostIP: ", str(destIP))
    
    if str(providerIP) == str(destIP):
        newSrcIP = encode("newBidSrcIP", stateCount)
        while queryChain(newSrcIP) is None:
            time.sleep(0.5)
        print("New Src IP received")
        srcIP = decode(queryChain(newSrcIP), stateCount)
        print("RECEIVED:", srcIP)
        winning_ip_address = srcIP.split(";")[0]
        winning_uuid = srcIP.split(";")[1]
        print("Winning IP:", winning_ip_address)
        print("Winning UUID:", winning_uuid)
        measure("deployFedService")
        provider_domain = deploy_provider(winning_ip_address, winning_uuid, provider_domain)
        measure("fedServiceRunning")
        serviceRunning = encode("serviceRunning", stateCount)
        serviceRunning_true = encode("True", stateCount)
        if writeChain(serviceRunning, serviceRunning_true):
            print("Notification for service running \n",serviceRunning)
        return True
    else:
        return False



if __name__ == '__main__':
    ip_addr = getIPaddress()
    print("NODE IP address:",ip_addr)
    host_id = str(ip_addr).split(".")[3]
    setBlockchainNodeIP(host_id) 

    fog_05, failed_fog05 = SetFog05(ip_addr)

    status = queryStatus()
    if len(status) == 0:
        sys.exit()

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
        consumer(net_info, mqtt_usage, ip_addr)
        question = input("Terminate the service?")
        if question != "no":
            remove_containers(fog_05)
            remove_net(fog_05,d1_n1)
            remove_net(fog_05,d1_n2)

#PROVIDER:::::::::::::::::::::::::::::::::::::::::::::::
    else:
        measure("start")
        running = provider(fog_05, host_id, ip_addr)
        if running:
            print("FEDERATED SERVICE IS RUNNING")
            question = input("Terminate the service?")
            if question != "no":
                remove_containers(fog_05)
                remove_net(fog_05,d2_n1)

    measure('end')    
    exit(0)

    
