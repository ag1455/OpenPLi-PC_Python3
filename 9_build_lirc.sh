#!/bin/bash

# Script for install patched lirc-0.10.1. Get repeats again.

# If your system has two devices /dev/lirc0 and /dev/lirc1 (for example, a built-in IR-receiver in the card card)
# then you can add a rule to /etc/udev/rules.d/99-lirc-symlinks.rules:
# KERNELS=="serial_ir.0", SUBSYSTEM=="lirc", DRIVERS=="serial_ir", ATTRS{driver_override}=="(null)", SYMLINK+="lirc_serial"
# and use "/dev/lirc_serial" in your *.lircd.conf.
# You also need to disable the uinput service by command:
# systemctl mask lircd-uinput.service
# and then reboot the system.

PKG="lirc-0.10.1"
DIR="lirc_build"
CONF="/etc/lirc"
release=$(lsb_release -a 2>/dev/null | grep -i release | awk ' { print $2 } ')

dpkg -r liblirc-dev liblirc0 liblircclient-dev lirc lirc-doc lirc-x

if [[ "$release" = "22.04" ]]; then
	pip install --upgrade websockets
	pip uninstall PyCrypto
	pip install -U PyCryptodome

	apt install -y dh-exec dh-python doxygen expect libftdi1-dev libsystemd-dev libudev-dev libusb-dev man2html-base portaudio19-dev python3-dev python3-setuptools socat setserial xsltproc
	wget http://ftp.de.debian.org/debian/pool/main/d/debhelper/dh-systemd_13.2.1_all.deb
	dpkg -i dh-systemd_13.2.1_all.deb
	rm -f dh-systemd_13.2.1_all.deb
	dpkg -i pre/lirc/*.deb

	mkdir $DIR
	cd $DIR
	if [ -d $PKG ]; then
		rm -fr $PKG
	fi
	wget https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/lirc/0.10.1-6/lirc_0.10.1.orig.tar.gz
	tar -xvf lirc_0.10.1.orig.tar.gz
	rm -vf lirc_0.10.1.orig.tar.gz
	cd ..
	cp -v patches/lirc-python3.10.patch $DIR/$PKG
	cd $DIR/$PKG
	patch -p1 < lirc-python3.10.patch
	rm -f *.patch
	chmod 755 debian/install
	chmod 755 debian/pbuilder-test
	chmod 755 debian/lirc-old2new
	chmod 755 debian/postrm
	cd ..
	tar -cvzf lirc_0.10.1-6.orig.tar.gz $PKG
	cd $PKG
	dpkg-buildpackage -b -d -uc -us
	cd ..
		dpkg -i *.deb
	cd ..
else
	echo "                                           "
	echo "              NOT SUPPORT!                 "
	echo "                                           "
fi

cp -rfv pre/lirc/lircd.conf.d /etc
cp -rfv pre/lirc/lirc_options.conf.example /etc
cp -fv pre/99-lirc-symlinks.rules /etc/udev/rules.d

if [ -f $CONF/lircd.conf.d/devinput.lircd.conf ]; then
	mv -b $CONF/lircd.conf.d/devinput.lircd.conf /etc/lirc/lircd.conf.d/devinput.lircd.conf.dist
fi
if [ -f $CONF/irexec.lircrc ]; then
	mv -b $CONF/irexec.lircrc $CONF/irexec.lircrc.dist
fi
if [ -f $CONF/irexec.lircrc ];then
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

#reboot
