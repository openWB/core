#!/bin/bash
OPENWBBASEDIR=/var/www/html/openWB
OPENWB_USER=openwb
OPENWB_GROUP=openwb

if (($(id -u) != 0)); then
	echo "this script has to be run as user root or with sudo"
	exit 1
fi

echo "upgrading openWB 2 in \"${OPENWBBASEDIR}\""

echo "stopping openWB2 system service..."
systemctl stop openwb2.service
echo "done"

echo "create group $OPENWB_GROUP"
# Will do nothing if group already exists:
/usr/sbin/groupadd "$OPENWB_GROUP"
echo "done"

echo "create user $OPENWB_USER"
# Will do nothing if user already exists:
/usr/sbin/useradd "$OPENWB_USER" -g "$OPENWB_GROUP" --create-home
echo "done"

# The user "openwb" is still new and we might need sudo in many places. Thus for now we give the user
# unrestricted sudo. This should be restricted in the future
echo "adding new user to sudoers"
echo "$OPENWB_USER ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/openwb
chmod 440 /etc/sudoers.d/openwb
echo "done"

echo "updating crontab..."
cp "${OPENWBBASEDIR}/data/config/openwb.cron" /etc/cron.d/openwb
echo "installed"

echo "updating openwb2 system service..."
systemctl daemon-reload
systemctl enable openwb2.service
echo "done"

echo "setting permissions in $OPENWBBASEDIR to $OPENWB_USER:$OPENWB_GROUP..."
chown -R "$OPENWB_USER:$OPENWB_GROUP" "$OPENWBBASEDIR"
echo "done"

echo "upgrade to openwb user finished, rebooting..."
/usr/sbin/reboot
