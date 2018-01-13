# py_freifunk_api

## test

sudo apt-get install mosquitto mosquitto-clients
sudo apt-get install python3-pip


## mqtt test
mosquitto_sub -v -h localhost -t '#'
mosquitto_sub -v -h localhost -t "world/fff/+/+/clients" -T "world/fff/+/all/#"
mosquitto_sub -v -h localhost -t "world/fff/+/all/clients"

