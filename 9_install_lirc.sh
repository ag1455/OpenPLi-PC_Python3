#!/bin/bash

# If your system has two devices /dev/lirc0 and /dev/lirc1 (for example, a built-in IR-receiver in the card card)
# then you can add a rule to /etc/udev/rules.d/99-lirc-symlinks.rules:
# KERNELS=="serial_ir.0", SUBSYSTEM=="lirc", DRIVERS=="serial_ir", ATTRS{driver_override}=="(null)", SYMLINK+="lirc_serial"
# and use "/dev/lirc_serial" in your *.lircd.conf.
# You also need to disable the uinput service by command:
# systemctl mask lircd-uinput.service
# and then reboot the system.

release=$(lsb_release -a 2>/dev/null | grep -i release | awk ' { print $2 } ')
CONF="/etc/lirc"

if [[ "$release" = "24.04" ]]; then
	apt install -y lirc-doc liblirc-client0t64 liblirc0t64 lirc lirc-x xfonts-75dpi

	cp -rfv pre/lirc/lircd.conf.d/MyRemote.lircd.conf.example /etc/lirc/lircd.conf.d/MyRemote.lircd.conf
	cp -rfv pre/lirc/lirc_options.conf.example /etc/lirc/lirc_options.conf
	cp -fv pre/99-lirc-symlinks.rules /etc/udev/rules.d

	if [[ -f $CONF/lircd.conf.d/devinput.lircd.conf ]]; then
		mv -b $CONF/lircd.conf.d/devinput.lircd.conf /etc/lirc/lircd.conf.d/devinput.lircd.conf.dist
	fi
	if [[ -f $CONF/irexec.lircrc ]]; then
		mv -b $CONF/irexec.lircrc $CONF/irexec.lircrc.dist
	fi
	if [[ -f $CONF/irexec.lircrc ]]; then
		rm -f $CONF/irexec.lircrc
	fi

	systemctl enable lircd.socket
	systemctl start lircd.socket
	systemctl enable lircmd.service
	systemctl start lircmd.service
	systemctl mask lircd-uinput.service
	systemctl daemon-reload
	systemctl start lircd
	systemctl restart lircd

	echo ""
	echo "NOW THE SYSTEM WILL BE RESTARTED!"
	echo ""

	sleep 2
	reboot # Need to restart system!
fi