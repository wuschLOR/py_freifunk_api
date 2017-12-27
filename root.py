## checks

import sys

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit()


## libs

import requests
import json


## helpfunctions

# https://stackoverflow.com/a/20988982
def is_int_able(x):
  try:
     int(x)
     return True
  except ValueError:
     return False


## script

# request api for user owned routers
resp_userinfo= requests.get("https://monitoring.freifunk-franken.de/api/routers_by_nickname/wu")

# generate router tuple

nodes = resp_userinfo.json()['nodes']

node_ids = []

for node in nodes:
    #print (node['name'])
    #print (node['oid'])
    node_ids.append(node['oid'])


print(node_ids)

# gen clientcount

clients = []

for node_id in node_ids:
    #print(node_id)
    
    resp_nodeinfo = requests.get("https://monitoring.freifunk-franken.de/routers/{}?json".format(node_id))
    
    clients.append(int(resp_nodeinfo.json()["clients"]))

    #print(resp_nodeinfo.json()["clients"])
    #print(resp_nodeinfo.json()["status"])
    #print(resp_nodeinfo.json()["hostname"])
    #print(resp_nodeinfo.json()["position_comment"])
    
    
print(clients)
print(sum(clients))