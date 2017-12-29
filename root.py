'''
testing
mosquitto_sub -v -h localhost -t '#'
mosquitto_sub -v -h localhost -t "world/fff/+/clients" -T "world/fff/all/#"
mosquitto_sub -v -h localhost -t "world/fff/all/clients"
'''




## libs
import sys
import requests
import paho.mqtt.publish as mqttpublish
import notify2


## checks
if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit()


## conditionals to get from enviorment later
notifyme = True

# init notifications
notify2.init('freifunkapi2mqtt')


## helpfunctions

# https://stackoverflow.com/a/20988982
def is_int_able(intablestring):
    '''
    trys to convert a str to number via int()
    '''
    try:    
        int(intablestring)
        return True
    except ValueError:
        return False


## funtions

def get_node_ids(username):
    '''
    fetch node ids for given username
    '''
    # request api for user owned routers
    resp_userinfo = requests.get("https://monitoring.freifunk-franken.de/api/routers_by_nickname/{}".format(username))
    
    node_ids = []
    
    if resp_userinfo.ok:
        # generate node tuple
        nodes = resp_userinfo.json()['nodes']
        for node in nodes:
            #dict['name''oid']
            node_ids.append(node['oid'])
    else:
        print('userinfo error')
    
    return(node_ids)
    
    
def fetch_and_publish_nodeinfo(node_id):
    '''
    fetches infos about the node and publishes it to mqtt
    returns clients
    '''
    resp_nodeinfo = requests.get("https://monitoring.freifunk-franken.de/routers/{}?json".format(node_id))
    
    if resp_nodeinfo.ok:
        #dict:["clients""status""hostname""position_comment"]
        #"world/fff/clients/nodenumber"
        mqttpublish.single("world/fff/{}/clients".format(node_id), int(resp_nodeinfo.json()["clients"]), hostname="localhost")
        
    else:
        print("nodeinfo error")
    
    return(int(resp_nodeinfo.json()["clients"]))
    
    
    

if __name__ == "__main__":

    node_ids = get_node_ids('wu')

    clients = []

    for node_id in node_ids:
        clients.append(fetch_and_publish_nodeinfo(node_id))

    mqttpublish.single("world/fff/all/clients", sum(clients), hostname="localhost")

    if notifyme:
        n = notify2.Notification('current freifunk clients', str(sum(clients)))
        n.show()


