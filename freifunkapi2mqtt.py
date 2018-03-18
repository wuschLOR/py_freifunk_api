"""
put help text here
"""

# checks
import sys

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit()

# libs

import requests
import paho.mqtt.publish as mqttpublish
import notify2
import time
import threading
import logging

# logging

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# file logging
fh = logging.FileHandler('spam.log')
fh.setLevel(logging.ERROR)
# logger shell output
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# set formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# 'application' code
logger.debug('debug message')
logger.info('info message')
logger.warn('warn message')
logger.error('error message')
logger.critical('critical message')


# config
logger.info('reading config')

FREIFUNKFRANKEN_USER_NODE_QUERRY_URL = "https://monitoring.freifunk-franken.de/api/routers_by_nickname/{}"
FREIFUNKFRANKEN_NODE_QUERRY_URL = "https://monitoring.freifunk-franken.de/routers/{}?json"
#            lacation/type/user/node_id/dataform
MQTT_PATH = "world/fff/{}/{}/{}"
MQTT_HOST = 'localhost'
NOTIFICATIONS_TITLE = 'freifunkapi2mqtt'
NOTIFICATIONS_FLUFF = 'current freifunk clients for {}'

PULBISHING_CYCLE = 10  # every 5 minutes


# objects
logger.info('defining config')

class Node(object):
    """
    Turns a nodedictionary into a class
    """

    def __init__(self, oid, name, ipv6_fe80_addr, mac):
        # main info
        self.oid = int(oid)
        self.name = name
        self.ipv6_fe80_addr = ipv6_fe80_addr
        self.mac = mac
        # extended info
        self.user = None
        self.hood = None
        self.firmware = None
        self.contact = None
        self.hostname = None
        self.position_comment = None
        self.lat = None
        self.lng = None
        self.status = None
        self.sys_uptime = None
        self.clients = None
        logger.debug("Node init " + str(self.name))

    def extend_with_node_api_response(self, node_api_response):
        node_api_response_json = node_api_response.json()
        self.user = node_api_response_json['user']
        self.hood = node_api_response_json['hood']
        self.firmware = node_api_response_json['firmware']
        self.contact = node_api_response_json['contact']
        self.hostname = node_api_response_json['hostname']
        self.position_comment = node_api_response_json['position_comment']
        self.lat = node_api_response_json['lat']
        self.lng = node_api_response_json['lng']
        self.status = node_api_response_json['status']
        self.sys_uptime = node_api_response_json['sys_uptime']
        self.clients = node_api_response_json['clients']
        logger.debug("Node extended with api response " + str(self.name))

    def is_online(self):
        logger.debug("Node.is_online " + str(self.status == 'online'))
        return self.status == 'online'

    def has_clients(self):
        logger.debug("Node.has " + str(self.clients > 0))
        return self.clients > 0


class FreifunkClient(object):
    """
    Client for FFF Node requestes and publishing
    """

    def __init__(self,
                 username,
                 api_url_user_nodes=FREIFUNKFRANKEN_USER_NODE_QUERRY_URL,
                 api_url_nodes=FREIFUNKFRANKEN_NODE_QUERRY_URL,
                 pulbishing_cycle=PULBISHING_CYCLE):
        # vars
        self.username = username
        self.api_url_user_nodes = api_url_user_nodes
        self.api_url_nodes = api_url_nodes
        self.pulbishing_cycle = pulbishing_cycle

        # main
        self.nodes = []
        self.node_count = 0
        self.client_count = 0
        self.notifications_status = False
        self.mqtt_status = False
        logger.debug("FreifunkClient init " + str(self.username))

    def init_notifications(self,
                           notifications_title=NOTIFICATIONS_TITLE,
                           notifications_fluff=NOTIFICATIONS_FLUFF):
        """
        set the notifications variables and inititates the notifications module
        """
        self.notifications_title = notifications_title
        self.notifications_fluff = notifications_fluff
        notify2.init(self.notifications_title)
        self.notifications_status = True
        logger.debug("FreifunkClient init_notifications " + str(self.username))

    def init_mqtt(self, mqtt_host=MQTT_HOST, mqtt_path=MQTT_PATH):
        """
        set the mqtt variables
        """
        self.mqtt_host = MQTT_HOST
        self.mqtt_path = mqtt_path
        self.mqtt_status = True
        logger.debug("FreifunkClient init_mqtt " + str(self.username))

    def fetch_user_node_data(self):
        """
        make api call and populate self.nodes with Nodes
        """
        user_node_api_response = requests.get(
            self.api_url_user_nodes.format(self.username))
        user_node_api_response_json = user_node_api_response.json()
        nodes_list = user_node_api_response_json['nodes']
        for node_item in nodes_list:
            node = Node(
                oid=node_item['oid'],
                name=node_item['name'],
                ipv6_fe80_addr=node_item['ipv6_fe80_addr'],
                mac=node_item['mac'])
            self.nodes.append(node)

        self.node_count = len(self.nodes)
        logger.debug("FreifunkClient fetch_user_node_data " + str(self.node_count))

    def publish_clients(self):
        """
        publishes client data to the enabled destinations
        * mqtt
        * notifications
        """
        if self.mqtt_status:
            mqttpublish.single(
                self.mqtt_path.format(self.username, 'all', 'clients'),
                self.client_count,
                hostname=self.mqtt_host)
            for i in range(0, len(self.nodes)):
                mqttpublish.single(
                    self.mqtt_path.format(self.username, self.nodes[i].oid,
                                          'clients'),
                    self.nodes[i].clients,
                    hostname=self.mqtt_host)

        if self.notifications_status:
            n = notify2.Notification('current freifunk clients for {}'.format(
                self.username), str(self.client_count))
            n.show()
            for i in range(0, len(self.nodes)):
                pass

        logger.debug("FreifunkClient publish_clients " + str(self.client_count))

    def update_nodes(self):
        """
        cycles throug nodes and overides current data with requested data
        """
        for i in range(0, len(self.nodes)):
            node_api_response = requests.get(
                self.api_url_nodes.format(self.nodes[i].oid))
            self.nodes[i].extend_with_node_api_response(node_api_response)

        self.client_count = sum(
            node.clients for node in self.nodes if node.clients is not None)

        logger.debug("FreifunkClient update_nodes " + str(self.self.nodes))

    def _continuous_publishing(self):
        """
        just triggers an update_nodes and then a publish_clients
        intended for threaded use
        """
        while True:
            try:
                self.update_nodes()
                self.publish_clients()
            except:
                pass
            logger.debug("FreifunkClient _continuous_publishing cycle")
            time.sleep(self.pulbishing_cycle)


    def continuous_publishing_threaded(self):
        """
        strats a thread with _continuous_publishing
        """
        threading.Thread(target=self._continuous_publishing).start()
        logger.debug("FreifunkClient continuous_publishing_threaded started")

if __name__ == "__main__":

    logger.info("starting __main__")
    users = ['wu', 'wuex', 'backspace']

    # create clients ready for threading
    fffcl = []

    for usr in users:
        cl = FreifunkClient(usr)
        cl.init_mqtt()
        #cl.init_notifications()
        cl.fetch_user_node_data()

        fffcl.append(cl)

    # run threads
    for cl in fffcl:
        cl.continuous_publishing_threaded()
