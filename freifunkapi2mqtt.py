'''
testing
mosquitto_sub -v -h localhost -t '#'
mosquitto_sub -v -h localhost -t "world/fff/+/clients" -T "world/fff/all/#"
mosquitto_sub -v -h localhost -t "world/fff/all/clients"
'''

## checks
import sys

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit()


## libs

import requests
import paho.mqtt.publish as mqttpublish


## config

FREIFUNKFRANKEN_USER_NODE_QUERRY_URL = "https://monitoring.freifunk-franken.de/api/routers_by_nickname/{}"
FREIFUNKFRANKEN_NODE_QUERRY_URL      = "https://monitoring.freifunk-franken.de/routers/{}?json"
#            lacation/type/user/node_id/dataform
MQTT_PATH = "world/fff/{}/{}/{}"


## funtions

def get_node_ids(username):
    '''
    fetch node ids for given username
    '''
    # request api for user owned routers
    user_node_api_response = requests.get(FREIFUNKFRANKEN_USER_NODE_QUERRY_URL.format(username))
    user_node_api_response_json = user_node_api_response.json()
    
    node_ids = []
    
    if user_node_api_response.ok:
        # generate node tuple
        nodes = user_node_api_response_json['nodes']
        for node in nodes:
            #dict['name''oid']
            node_ids.append(node['oid'])
    else:
        print('userinfo error')
    
    return(node_ids)
    
    
def fetch_and_publish_node_api_response(node_id):
    '''
    fetches infos about the node and publishes it to mqtt
    returns clients
    '''
    resp_node_api_response = requests.get(FREIFUNKFRANKEN_NODE_QUERRY_URL.format(node_id))
    
    if resp_node_api_response.ok:
        #dict:["clients""status""hostname""position_comment"]
        #"world/fff/clients/nodenumber"
        mqttpublish.single(MQTT_PATH.format('TEST',node_id,'clients'), int(resp_node_api_response.json()["clients"]), hostname="localhost")
        
    else:
        print("node_api_response error")
    
    return(int(resp_node_api_response.json()["clients"]))
    

    

    
## objects

class Node(object):
    """
    Turns a nodedictionary into a class
    """
    def __init__(self, ipv6,mac,name,oid):
        # main info
        self.ipv6             = ipv6
        self.mac              = mac
        self.name             = name
        self.oid              = oid
        # extended info
        self.hood             = None
        self.firmware         = None
        self.contact          = None
        self.hostname         = None
        self.position_comment = None
        self.lat              = None
        self.lng              = None
        self.status           = None
        self.sys_uptime       = None
        self.clients          = None
        '''
        self.hood             = node_api_response_json['hood']
        self.firmware         = node_api_response_json['firmware']
        self.contact          = node_api_response_json['contact']
        self.hostname         = node_api_response_json['hostname']
        self.position_comment = node_api_response_json['position_comment']
        self.lat              = node_api_response_json['lat']
        self.lng              = node_api_response_json['lng']
        self.status           = node_api_response_json['status']
        self.sys_uptime       = node_api_response_json['sys_uptime']
        self.clients          = node_api_response_json['clients']
        '''
    def is_online(self):
        return (self.status == 'online')
    
    def has_clients(self):
        return (self.clients>0)

class User(object):
    '''user_node_api_response_json
    Turns a userdictionary into classuser_node_api_response_json
    '''
    def __init__(self):
        pass

class FreifunkClient(object):
    '''
    Client for data management 
    '''
    def __init__(self, username, api_url_user_nodes=None, api_url_nodes=None):
        self.username = username
        if api_url_user_nodes:
            self.api_url_user_nodes = api_url_user_nodes
        else:
            self.api_url_user_nodes = FREIFUNKFRANKEN_USER_NODE_QUERRY_URL
        
        if api_url_nodes:
            self.api_url_nodes = api_url_nodes
        else:
            self.api_url_nodes = FREIFUNKFRANKEN_NODE_QUERRY_URL
            
    def fetch_user_node_data(self):
        user_node_api_response = requests.get(self.api_url_user_nodes.format(self.username))
        user_node_api_response_json = user_node_api_response.json()
        return(user_node_api_response_json)
    
    def fetch_node_data(self, node_id):
        node_api_response = requests.get(self.api_url_nodes.format(node_id))
        node_api_response_json = node_api_response.json()
        return(node_api_response_json)

    
    def fetch_nodes(self):
        self.nodes=[]
        for nodeid in self.node_ids:
            seld.nodes.append(self.fetch_node_data(node_id))
            

    

if __name__ == "__main__":
    
#import freifunkapi2mqtt
#fff=freifunkapi2mqtt.FreifunkClient('wu')
#fff.fetch_user_data()

    
    
    
    import notify2
    
    ## conditionals to get from enviorment later
    notifyme = True
    users = ['wu','wuex']

    # init notifications
    notify2.init('freifunkapi2mqtt')

    
    for user in users:
        
        node_ids = get_node_ids(user)

        clients = []

        for node_id in node_ids:
            clients.append(fetch_and_publish_node_api_response(node_id))

        mqttpublish.single(MQTT_PATH.format('TEST','all','clients'), sum(clients), hostname="localhost")

        if notifyme:
            n = notify2.Notification('current freifunk clients for {}'.format(user), str(sum(clients)))
            n.show()


