import random
import sys
import os
import json 
import time
from web3 import Web3, HTTPProvider, IPCProvider
from web3.contract import ConciseContract
import json
from web3.providers.rpc import HTTPProvider

from web3 import Web3
web3= Web3(Web3.WebsocketProvider("ws://163.117.140.69:7545"))

abi_path = "../smart-contracts/build/contracts/"

print('Coinbase account: ',web3.eth.coinbase)
print('\nAccounts: ',web3.eth.accounts)

with open(abi_path+"Federation.json") as c_json:
    contract_json = json.load(c_json)

contract_abi = contract_json["abi"]
contract_address = Web3.toChecksumAddress('0xc76d33f788a17fe014b9E8D00505FA51F9804f97')

Federation_contract = web3.eth.contract(abi= contract_abi, address = contract_address)

coinbase = web3.eth.coinbase
eth_address = web3.eth.accounts

#### GETH COMMANDS:
# web3.fromWei(web3.eth.getBalance(web3.eth.coinbase));
# web3.eth.sendTransaction({from:web3.eth.coinbase,to:web3.eth.accounts[2], value:web3.toWei(10, "ether")});
# {'uuid': '6cc2aa30-1dcf-4c93-a57e-433fd0bd498e', 'name': 'net1', 'net_type': 'ELAN', 'is_mgmt': False, 'port': 4789, 'vni': 1170838, 'mcast_addr': '239.0.202.79'}
# from web3.auto.gethdev import w3
# >>> w3.is_encodable('bytes2', b'12')

print("Etherbase:", coinbase)
# input("\nGet info of Operator (ENTER)")

service_id = 'service1'
service_requirements = 'ip=10.0.0.4'
service_endpoint_consumer= '192.168.213.10'
e_uuid_1 = "6cc2aa30-1dcf-4c93"
e_uuid_2 = "-a57e-433fd0bd498e"
e_name = "net1"
e_net_type = "ELAN"
e_is_mgmt = False

e2_uuid_1 = "aaaaaabb-cccc-dddd"
e2_uuid_2 = "-a57e-433fd0bd498e"
e2_name = "net2"
e2_net_type = "ELAN"
e2_is_mgmt = False

service_consumer_address= coinbase

service_provider_address = [eth_address[0], eth_address[1], eth_address[2]]
service_endpoint_provider = '192.168.213.11'
federated_host= '10.0.0.4'
service_price = 5
bid_index = 0
winner = coinbase

debug_txt = input("\nUse service_id:")
service_id = debug_txt
print("\nSERVICE ID used:", service_id)
operator_index = 0
debug_txt = input("\nRegister accounts as OPERATORS? (Y/n)")
if debug_txt == 'y' or debug_txt == 'Y':
    for address in service_provider_address:
        operator_string = 'AD'+str(operator_index)
        tx_hash = Federation_contract.functions.addOperator(Web3.toBytes(text=operator_string)).transact({'from': address})
        operator_index+=1


info = Federation_contract.functions.getOperatorInfo(web3.eth.coinbase).call()

print("\n\n",web3.toText(info))

debug_txt = input("\nCreate Service anouncement? (Y/n)")
# print(service_provider_address[int(debug_txt)])
# print("\n\tDEBUG:", debug_txt)
# print("\n\tAnnounce service ------>\n")
if debug_txt == 'y' or debug_txt == 'Y':
    new_service = \
    Federation_contract.functions.AnnounceService(\
    _requirements= web3.toBytes(text = service_requirements),\
    _id = web3.toBytes(text = service_id),\
    endpoint_uuid_1= web3.toBytes(text = e_uuid_1),\
    endpoint_uuid_2= web3.toBytes(text = e_uuid_2),\
    endpoint_name= web3.toBytes(text = e_name),\
    endpoint_net_type= web3.toBytes(text = e_net_type),\
    endpoint_is_mgmt= e_is_mgmt).transact({'from':coinbase})


debug_txt = input("\nPrint emited event (ENTER)")
block = web3.eth.getBlock('latest')
blocknumber = block['number']
print("\nLatest block:",blocknumber)
event_filter = Federation_contract.events.ServiceAnnouncement.createFilter(fromBlock=web3.toHex(blocknumber-30))
new_event = event_filter.get_all_entries()
for event in new_event:
    serviceid = web3.toText(event['args']['id'])
    print(serviceid)

print(new_event)

debug_txt = input("\nCheck service state? (Y/n)")
if debug_txt == 'y' or debug_txt == 'Y':
    new_service_anouncement = Federation_contract.functions.GetServiceState(_id = web3.toBytes(text= service_id)).call()
    print("\n",new_service_anouncement)

debug_txt = input("\nPlace bid? Use account (1 or 2)")
if debug_txt == '1' or debug_txt == '2':
    Federation_contract.functions.PlaceBid(_id= web3.toBytes(text= service_id), _price= service_price,\
    endpoint_uuid_1= web3.toBytes(text = e2_uuid_1), \
    endpoint_uuid_2= web3.toBytes(text = e2_uuid_2),\
    endpoint_name= web3.toBytes(text = e2_name),\
    endpoint_net_type= web3.toBytes(text = e2_net_type),\
    endpoint_is_mgmt= e2_is_mgmt).transact({'from':service_provider_address[int(debug_txt)]})

debug_txt = input("\nCheck for bidders (ENTER)")
block = web3.eth.getBlock('latest')
blocknumber = block['number']
print("\nLatest block:",blocknumber)
event_filter = Federation_contract.events.NewBid.createFilter(fromBlock=web3.toHex(blocknumber-30))
new_event = event_filter.get_all_entries()
print("\nBiders for service (",service_id,"): \n")
for event in new_event:
    bid_index = int(event['args']['max_bid_index'])
    print(web3.toText(event['args']['_id']), event['args']['max_bid_index'])


debug_txt = input("\nGet Bid-info for index: (default=skip, For All= all)")
try:
    val = int(debug_txt)
    if int(debug_txt) <= bid_index:
        bid_info = Federation_contract.functions.GetBid(_id= web3.toBytes(text= service_id), bider_index= int(debug_txt), _creator=coinbase).call()
        print(bid_info)
except:
    if debug_txt == 'all':
        for index in range(bid_index):
            bid_info = Federation_contract.functions.GetBid(_id= web3.toBytes(text= service_id), bider_index= index, _creator=coinbase).call()
            print(bid_info)
            print(web3.toText(bid_info[-1]))

debug_txt = input("\nChoose Provider [index]: (default=skip)")
try:
    index = int(debug_txt)
    if index <= bid_index:
        chosen_provider = Federation_contract.functions.ChooseProvider(_id= web3.toBytes(text= service_id), bider_index= index).transact({'from':coinbase})
        print(chosen_provider)
except:
    print("Skipped")

debug_txt = input("\nCheck for Provider choosen (ENTER)")
block = web3.eth.getBlock('latest')
blocknumber = block['number']
print("\nLatest block:",blocknumber)
event_filter = Federation_contract.events.ServiceAnnouncementClosed.createFilter(fromBlock=web3.toHex(blocknumber-30))
new_event = event_filter.get_all_entries()
print("\nProviders choosen for service:\n")
for event in new_event:
    print(web3.toText(event['args']['_id']))

debug_txt = input("\nWho is winner? (ENTER)")
service_state = Federation_contract.functions.GetServiceState(_id = web3.toBytes(text= service_id)).call()
if service_state == 1:
    for is_winner in service_provider_address:
        result = Federation_contract.functions.isWinner(_id= web3.toBytes(text= service_id), _winner= is_winner).call()
        print("\n",is_winner, ":\t:",result)
        if result:
            winner = is_winner
            print("\t WINNER")
elif service_state == 0:
    print("\nService is still OPEN")
else:
    print("\nService is already DEPLOYED")

debug_txt = input("\nCheck service details as winner or creator? (ENTER= winner, c = consumer, w = winner)")
service_state = Federation_contract.functions.GetServiceState(_id = web3.toBytes(text= service_id)).call()
if service_state >= 1:
    use_address = coinbase if debug_txt == 'consumer' else winner
    is_provider = False if debug_txt == 'consumer' else True
    service_info_id = []
    # service_info_id, service_info_endpoint, service_info_req  = Federation_contract.functions.GetServiceInfo(_id = web3.toBytes(text= service_id), provider= is_provider).transact({'from':use_address})
    service_info_id  = Federation_contract.functions.GetServiceInfo(_id = web3.toBytes(text= service_id), provider= is_provider, call_address= use_address).call()
    print("\nService Info:", service_info_id, len(service_info_id))  
    for info in service_info_id:
        try:
            print("\n", web3.toText(info))
        except:
             print("\n", info)
    # print("\nService Info:", web3.toText(service_info_id), web3.toText(service_info_endpoint), web3.toText(service_info_req))  
else:
    print("\nService is still OPEN")
# else:
    # print("\nService is already DEPLOYED")

debug_txt = input("\nDeploy Service.... (ENTER)")
service_state = Federation_contract.functions.GetServiceState(_id = web3.toBytes(text= service_id)).call()
if service_state == 1 and winner != coinbase:
    result = Federation_contract.functions.ServiceDeployed(info= web3.toBytes(text= federated_host), _id= web3.toBytes(text= service_id)).transact({'from':winner})
elif service_state == 0:
    print("\nService is still OPEN")
else:
    print("\nService is already DEPLOYED")


debug_txt = input("\nService is deployed? (ENTER)")
service_state = Federation_contract.functions.GetServiceState(_id = web3.toBytes(text= service_id)).call()
if service_state == 1:
    print("\nService is CLOSED, but not deployed")
elif service_state == 0:
    print("\nService is still OPEN")
else:
    print("\nService is already DEPLOYED")


debug_txt = input("\nUpdate endpoint (ENTER)")
service_state = Federation_contract.functions.GetServiceState(_id = web3.toBytes(text= service_id)).call()
if service_state == 2 and winner != coinbase:
    result = Federation_contract.functions.UpdateEndpoint(call_address= winner,\
    provider= True, _id= web3.toBytes(text= service_id),\
    endpoint_uuid_1= web3.toBytes(text = e_uuid_1), \
    endpoint_uuid_2= web3.toBytes(text = e2_uuid_2),\
    endpoint_name= web3.toBytes(text = e_name),\
    endpoint_net_type= web3.toBytes(text = e2_net_type),\
    endpoint_is_mgmt= e2_is_mgmt).transact({'from':winner})
    time.sleep(5)
    service_info_id  = Federation_contract.functions.GetServiceInfo(_id = web3.toBytes(text= service_id), provider= False, call_address= coinbase).call()
    print("\nService Info:", service_info_id, len(service_info_id))  
    for info in service_info_id:
        print("\n", info)
elif service_state == 0:
    print("\nService is still OPEN")
else:
    print("\nService is already DEPLOYED")



# print("\nEVENTS:\n")
# print(event_filter)
# for event in event_filter.get_all_entries():
#     print(event)