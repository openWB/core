#!/bin/bash
# backup some files before fetching new release
# module soc_eq
cp modules/soc_eq/soc_eq_acc_lp1 /tmp/soc_eq_acc_lp1
cp modules/soc_eq/soc_eq_acc_lp2 /tmp/soc_eq_acc_lp2

# fetch new release from GitHub
sudo git fetch origin
sudo git reset --hard origin/$1

# set permissions
cd /var/www/html/
sudo chown -R pi:pi openWB 
sudo chown -R www-data:www-data /var/www/html/openWB/web/backup
sudo chown -R www-data:www-data /var/www/html/openWB/web/tools/upload

# restore saved files after fetching new release
# module soc_eq
sudo cp /tmp/soc_eq_acc_lp1 /var/www/html/openWB/modules/soc_eq/soc_eq_acc_lp1
sudo cp /tmp/soc_eq_acc_lp2 /var/www/html/openWB/modules/soc_eq/soc_eq_acc_lp2

sleep 2

# now treat system as in booting state
sudo reboot now