sudo service mosquitto stop
sudo rm /var/lib/mosquitto/mosquitto.db
sudo service mosquitto start
sudo service mosquitto_local stop
sudo rm /var/lib/mosquitto_local/mosquitto.db
sudo service mosquitto_local start
sudo rm /etc/mosquitto/mosquitto_local.conf
./runs/atreboot.sh