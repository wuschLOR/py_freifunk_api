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

## script

# request api for user owned routers
resp_userinfo = requests.get("https://monitoring.freifunk-franken.de/api/routers_by_nickname/wu")

if resp_userinfo.ok:
    # generate router tuple
    nodes = resp_userinfo.json()['nodes']
    node_ids = []
    
    for node in nodes:
        #dict['name''oid']
        node_ids.append(node['oid'])

    clients = []

    for node_id in node_ids:
        #print(node_id)
        resp_nodeinfo = requests.get("https://monitoring.freifunk-franken.de/routers/{}?json".format(node_id))
        if resp_nodeinfo.ok:
            #dict:["clients""status""hostname""position_comment"]
            clients.append(int(resp_nodeinfo.json()["clients"]))
            #"world/fff/clients/nodenumber"
            mqttpublish.single("world/fff/{}/clients".format(node_id), int(resp_nodeinfo.json()["clients"]), hostname="localhost")
        else:
            print("nodeinfo error")

    mqttpublish.single("world/fff/all/clients", sum(clients), hostname="localhost")
    n = notify2.Notification('current freifunk clients', str(sum(clients)))
    n.show()
else:
    print('userinfo error')

