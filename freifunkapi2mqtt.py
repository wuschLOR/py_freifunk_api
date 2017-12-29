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


## funtions

def get_node_ids(username):
    '''
    fetch node ids for given username
    '''
    # request api for user owned routers
    user_api_response = requests.get(FREIFUNKFRANKEN_USER_NODE_QUERRY_URL.format(username))
    user_api_response_json = user_api_response.json()
    
    node_ids = []
    
    if user_api_response.ok:
        # generate node tuple
        nodes = user_api_response_json['nodes']
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
        mqttpublish.single("world/fff/{}/clients".format(node_id), int(resp_node_api_response.json()["clients"]), hostname="localhost")
        
    else:
        print("node_api_response error")
    
    return(int(resp_node_api_response.json()["clients"]))
    

    

    
## objects

class Node(object):
    """
    Turns a dictionary into a class
    """
    def __init__(self, node_api_response):
        node_api_response_json = node_api_response.json()
        self.id               = node_api_response_json['id']
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

    

if __name__ == "__main__":
    
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

        mqttpublish.single("world/fff/all/clients", sum(clients), hostname="localhost")

        if notifyme:
            n = notify2.Notification('current freifunk clients for {}'.format(user), str(sum(clients)))
            n.show()


