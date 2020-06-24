pragma solidity >=0.4.21 <0.7.0;
pragma experimental ABIEncoderV2;

contract Federation {

    enum ServiceState {Open, Closed, Deployed}
    struct Operator {
        bytes32 name;
        bool registered;
    }

    struct Endpoint {
        bytes32 uuid_1;
        bytes32 uuid_2;
        bytes32 name;
        bytes32 net_type;
        bool is_mgmt;
    }

    struct Service {
        address creator;
        bytes32 endpoint_consumer;
        bytes32 id;
        address provider;
        bytes32 endpoint_provider;
        bytes32 req_info;
        ServiceState state;
    }

    struct Bid {
        address bid_address;
        uint price;
        bytes32 endpoint_provider;
    }

    mapping(bytes32 => uint) public bidCount;
    mapping(bytes32 => Bid[]) public bids;
    mapping(bytes32 => Service) public service;
    mapping(bytes32 => Endpoint) public endpoints;
    mapping(address => Operator) public operator;

    event OperatorRegistered(address operator, bytes32 name);
    event ServiceAnnouncement(bytes32 requirements, bytes32 id);
    event NewBid(bytes32 _id, uint256 max_bid_index);
    event ServiceAnnouncementClosed(bytes32 _id);
    event ServiceDeployedEvent(bytes32 _id);

    function addOperator(bytes32 name) public {
        Operator storage current_operator = operator[msg.sender];
        require(name.length > 0, "Name is not valid");
        require(current_operator.registered == false, "Operator already registered");
        current_operator.name = name;
        current_operator.registered = true;
        emit OperatorRegistered(msg.sender, name);
    }

    function getOperatorInfo(address op_address) public view returns (bytes32 name) {
        Operator storage current_operator = operator[op_address];
        require(current_operator.registered == true, "Operator is not registered with this address. Please register.");
        return current_operator.name;
	}

    function AnnounceService(bytes32 _requirements, bytes32 _id,
                            bytes32 endpoint_uuid_1, bytes32 endpoint_uuid_2, bytes32 endpoint_name,
                            bytes32 endpoint_net_type, bool endpoint_is_mgmt) public returns(ServiceState) {
        Operator storage current_operator = operator[msg.sender];
        Service storage current_service = service[_id];
        require(current_operator.registered == true, "Operator is not registered. Can not bid. Please register.");
        require(current_service.id != _id, "Service ID for operator already exists");
        bytes32 endpoint_keccak = keccak256(abi.encodePacked(endpoint_uuid_1,
                                 endpoint_uuid_2, endpoint_name, endpoint_net_type, endpoint_is_mgmt));
        endpoints[endpoint_keccak] = Endpoint(endpoint_uuid_1, endpoint_uuid_2, endpoint_name, endpoint_net_type, endpoint_is_mgmt);
        service[_id] = Service(msg.sender, endpoint_keccak, _id, msg.sender,  endpoint_keccak, _requirements, ServiceState.Open);
        emit ServiceAnnouncement(_requirements, _id);
        return ServiceState.Open;
    }

    function UpdateEndpoint(address call_address, bool provider, bytes32 _id,
                            bytes32 endpoint_uuid_1, bytes32 endpoint_uuid_2, bytes32 endpoint_name,
                            bytes32 endpoint_net_type, bool endpoint_is_mgmt) public returns (bool) {
        Operator storage current_operator = operator[call_address];
        Service storage current_service = service[_id];
        bytes32 endpoint_keccak = keccak256(abi.encodePacked(endpoint_uuid_1,
                                 endpoint_uuid_2, endpoint_name, endpoint_net_type, endpoint_is_mgmt));
        require(current_operator.registered == true, "Operator is not registered. Can not look into. Please register.");
        require(current_service.state >= ServiceState.Open, "Service is closed or not exists");
        if(provider == true) {
                require(current_service.state >= ServiceState.Closed, "Service is still open or not exists");
                require(current_service.provider == call_address, "This domain is not a winner");
                endpoints[endpoint_keccak] = Endpoint(endpoint_uuid_1, endpoint_uuid_2, endpoint_name, endpoint_net_type, endpoint_is_mgmt);
                service[_id].endpoint_provider = endpoint_keccak;
                return true;
        }
        else {
                require(current_service.creator == call_address, "This domain is not a creator");
                endpoints[endpoint_keccak] = Endpoint(endpoint_uuid_1, endpoint_uuid_2, endpoint_name, endpoint_net_type, endpoint_is_mgmt);
                service[_id].endpoint_consumer = endpoint_keccak;
                return true;
        }
    }
        
    function GetServiceState(bytes32 _id) public view returns (ServiceState) {
        // Service storage current_service = service[_id];
        // require(service[_id].creator == _creator, "Service not exists");
        // assert(service[_id].state == ServiceState.Open);
        return service[_id].state;
    }

    function GetServiceInfo(bytes32 _id, bool provider, address call_address)
    public view returns (bytes32, bytes32, bytes32, bytes32, bytes32, bytes32, bool) {
        Operator storage current_operator = operator[call_address];
        Service storage current_service = service[_id];
        
        require(current_operator.registered == true, "Operator is not registered. Can not look into. Please register.");
        require(current_service.state >= ServiceState.Closed, "Service is still open or not exists");
        if(provider == true) {
                require(current_service.provider == call_address, "This domain is not a winner");
                Endpoint storage current_endpoint = endpoints[current_service.endpoint_consumer];
                return(current_service.id, current_service.req_info,
                       current_endpoint.uuid_1, current_endpoint.uuid_2,
                       current_endpoint.name, current_endpoint.net_type,
                       current_endpoint.is_mgmt);
        }
        else {
                require(current_service.creator == call_address, "This domain is not a creator");
                Endpoint storage current_endpoint = endpoints[current_service.endpoint_provider];
                return(current_service.id, current_service.req_info,
                       current_endpoint.uuid_1, current_endpoint.uuid_2,
                       current_endpoint.name, current_endpoint.net_type,
                       current_endpoint.is_mgmt);
            }
    }
    
      function GetEndpoint(bytes32 endpoint_id, address call_address)
      public view returns (bytes32, bytes32, bytes32, bytes32, bool) {
        Operator storage current_operator = operator[call_address];
        Endpoint storage current_endpoint = endpoints[endpoint_id];
        require(current_operator.registered == true, "Operator is not registered. Can not look into. Please register.");
        require(current_endpoint.name != "", "Endpoint not exists");
        return(current_endpoint.uuid_1, current_endpoint.uuid_2,
               current_endpoint.name, current_endpoint.net_type, current_endpoint.is_mgmt);
    }

    function PlaceBid(bytes32 _id, uint32 _price,
                     bytes32 endpoint_uuid_1, bytes32 endpoint_uuid_2, bytes32 endpoint_name,
                     bytes32 endpoint_net_type, bool endpoint_is_mgmt) public returns (uint256) {
        Operator storage current_operator = operator[msg.sender];
        Service storage current_service = service[_id];
        require(current_operator.registered == true, "Operator is not registered. Can not bid. Please register.");
        require(current_service.state == ServiceState.Open, "Service is closed or not exists");
        bytes32 endpoint_keccak = keccak256(abi.encodePacked(endpoint_uuid_1,
                                 endpoint_uuid_2, endpoint_name, endpoint_net_type, endpoint_is_mgmt));
        endpoints[endpoint_keccak] = Endpoint(endpoint_uuid_1, endpoint_uuid_2, endpoint_name, endpoint_net_type, endpoint_is_mgmt);
        uint256 max_bid_index = bids[_id].push(Bid(msg.sender, _price, endpoint_keccak));
        // uint256 max_bid_index = 0;
        // uint256 max_bid_index = bids[_id].push(Bid(msg.sender, _price, _endpoint));
        bidCount[_id] = max_bid_index;
        emit NewBid(_id, max_bid_index);
        return max_bid_index;
    }

    function GetBidCount(bytes32 _id, address _creator) public view returns (uint256) {
        Service storage current_service = service[_id];
        require(current_service.id == _id, "Service not exists");
        require(current_service.creator == _creator, "Only service creator can look into the information");
        return bidCount[_id];
    }

    function GetBid(bytes32 _id, uint256 bider_index, address _creator) public view returns (address, uint, uint256, bytes32) {
        Service storage current_service = service[_id];
        Bid[] storage current_bid_pool = bids[_id];
        require(current_service.id == _id, "Service not exists");
        require(current_service.creator == _creator, "Only service creator can look into the information");
        require(bids[_id].length > 0, "No bids for requested Service");
        return (current_bid_pool[bider_index].bid_address, current_bid_pool[bider_index].price,
               bider_index, current_bid_pool[bider_index].endpoint_provider);
        // return bids[_id];
    }

    function ChooseProvider(bytes32 _id, uint256 bider_index) public returns (bool) {
        Service storage current_service = service[_id];
        Bid[] storage current_bid_pool = bids[_id];
        require(current_service.id == _id, "Service not exists");
        require(current_service.creator == msg.sender, "Only service creator can close the announcement");
        require(current_service.state == ServiceState.Open, "Service announcement already closed");

        current_service.state = ServiceState.Closed;
        // address bid_address_= current_bid_pool[bider_index].bid_address;
        service[_id].provider = current_bid_pool[bider_index].bid_address;
        service[_id].endpoint_provider = current_bid_pool[bider_index].endpoint_provider;
        emit ServiceAnnouncementClosed(_id);
        return true;
        // return (current_bid_pool[bider_index].bid_address, current_bid_pool[bider_index].price);
    }

    function isWinner(bytes32 _id, address _winner) public view returns (bool) {
        Service storage current_service = service[_id];
        require(current_service.state == ServiceState.Closed, "Service winner not choosen. Service: DEPLOYED or OPEN");
        if(current_service.provider == _winner) {
            return true;
        }
        else {
            return false;
        }
    }

    function ServiceDeployed(bytes32 info, bytes32 _id) public returns (bool) {
        Service storage current_service = service[_id];
        require(current_service.id == _id, "Service not exists");
        require(current_service.provider == msg.sender, "Only service provider can deploy the service");
        require(current_service.state == ServiceState.Closed, "Service winner not choosen. Service: DEPLOYED or OPEN");
        current_service.state = ServiceState.Deployed;
        current_service.req_info = info;
        emit ServiceDeployedEvent(_id);
        return true;
    }


}