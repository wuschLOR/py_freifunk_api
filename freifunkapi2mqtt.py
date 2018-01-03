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
import notify2

## config

FREIFUNKFRANKEN_USER_NODE_QUERRY_URL = "https://monitoring.freifunk-franken.de/api/routers_by_nickname/{}"
FREIFUNKFRANKEN_NODE_QUERRY_URL      = "https://monitoring.freifunk-franken.de/routers/{}?json"
#            lacation/type/user/node_id/dataform
MQTT_PATH = "world/fff/{}/{}/{}"
MQTT_HOST = 'localhost'
NOTIFICATIONS_TITLE = 'freifunkapi2mqtt'
NOTIFICATIONS_FLUFF = 'current freifunk clients for {}'

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
    def __init__(self, oid, name, ipv6_fe80_addr, mac):
        # main info
        self.oid              = int(oid)
        self.name             = name
        self.ipv6_fe80_addr   = ipv6_fe80_addr
        self.mac              = mac
        # extended info
        self.user             = None
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

    def extend_with_node_api_response(self, node_api_response):
        node_api_response_json = node_api_response.json()
        self.user             = node_api_response_json['user']
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
    def __init__(self, 
                 username, 
                 api_url_user_nodes=FREIFUNKFRANKEN_USER_NODE_QUERRY_URL, 
                 api_url_nodes=FREIFUNKFRANKEN_NODE_QUERRY_URL):
        # main
        self.username = username
        self.nodes=[]
        self.node_count = 0
        self.client_count= 0
        self.api_url_user_nodes = api_url_user_nodes
        self.api_url_nodes = api_url_nodes
        # conditionals    
        self.notifications_status = False
        self.mqtt_status = False
            
    def init_notifications(self, 
                           notifications_title=NOTIFICATIONS_TITLE, 
                           notifications_fluff=NOTIFICATIONS_FLUFF):
        self.notifications_title  = notifications_title
        self.notifications_fluff  = notifications_fluff
        notify2.init(self.notifications_title)
        self.notifications_status = True
        
    def init_mqtt(self,
                  mqtt_host=MQTT_HOST, 
                  mqtt_path=MQTT_PATH):
        self.mqtt_host = MQTT_HOST
        self.mqtt_path = mqtt_path            
        self.mqtt_status = True

    def fetch_user_node_data(self):
        user_node_api_response = requests.get(self.api_url_user_nodes.format(self.username))
        user_node_api_response_json = user_node_api_response.json()
        nodes_list = user_node_api_response_json['nodes']
        for node_item in nodes_list:
            node = Node(oid            = node_item['oid'],
                        name           = node_item['name'],
                        ipv6_fe80_addr = node_item['ipv6_fe80_addr'],
                        mac            = node_item['mac'])
            self.nodes.append(node)
            
        self.node_count=len(self.nodes)
        
    def publish_clients(self):
        total_clients=sum(node.clients for node in self.nodes if node.clients is not None)
        if self.mqtt_status:
            mqttpublish.single(self.mqtt_path.format(self.username,'all','clients'), 
                               total_clients, 
                               hostname=self.mqtt_host)
            for i in range(0,len(self.nodes)):
                mqttpublish.single(self.mqtt_path.format(self.username,self.nodes[i].oid,'clients'), 
                                self.nodes[i].clients, 
                                hostname=self.mqtt_host)                
            
        if self.notifications_status:
            n = notify2.Notification('current freifunk clients for {}'.format(self.username), 
                                     str(total_clients))
            n.show()
            for i in range(0,len(self.nodes)):
                pass

    def update_nodes(self):
        for i in range(0,len(self.nodes)):
            node_api_response = requests.get(self.api_url_nodes.format(self.nodes[i].oid))
            self.nodes[i].extend_with_node_api_response(node_api_response)

            

    

if __name__ == "__main__": 
    
    users = ['wu','wuex']

    # init notifications

    fff_wu=FreifunkClient('wu')
    fff_wu.init_mqtt()
    fff_wu.init_notifications()
    fff_wu.fetch_user_node_data()
    fff_wu.update_nodes()
    fff_wu.publish_clients()
    
    
    
    ## old
    '''
    for user in users:
        
        node_ids = get_node_ids(user)

        clients = []

        for node_id in node_ids:
            clients.append(fetch_and_publish_node_api_response(node_id))

        mqttpublish.single(MQTT_PATH.format('TEST','all','clients'), sum(clients), hostname="localhost")

        if notifyme:
            n = notify2.Notification('current freifunk clients for {}'.format(user), str(sum(clients)))
            n.show()

    '''
'''
import freifunkapi2mqtt                        
fff=freifunkapi2mqtt.FreifunkClient('wu')      
fff.init_mqtt()
fff.init_notifications()
fff.fetch_user_node_data()
fff.update_nodes()
fff.publish_clients()
'''