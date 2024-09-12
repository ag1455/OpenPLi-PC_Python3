#!/bin/bash

# Unfortunately e2pc doesn't work with wayland
#cp -fv /etc/gdm3/custom.conf /etc/gdm3/custom.conf~
#rpl '#WaylandEnable=false' 'WaylandEnable=false' /etc/gdm3/custom.conf

release=$(lsb_release -a 2>/dev/null | grep -i release | awk ' { print $2 } ')

HEADERS="/usr/src/linux-headers-`uname -r`/include/uapi/linux/dvb"
HEADERSL="/usr/src/linux-lowlatency-headers-`uname -r`/include/uapi/linux/dvb"
INCLUDE="/usr/include/linux/dvb"
BUILD_DIR="libs"
INSTALL_E2DIR="/usr/local/e2"
prefix2="/usr/src/OpenPLi-PC_Python3/libs"

if [[ "$release" = "24.04" ]]; then
	prefix1="/usr/local/lib/python3.12/dist-packages"
	prefix3="/home/$(logname)/.venv/e2pc/lib/python3.12/site-packages"
fi

# Copy headers
cp -fv pre/dvb/* $INCLUDE
cp -fv pre/dvb/* $HEADERS
cp -fv pre/dvb/* $HEADERSL

# Download dvb-firmwares
wget --no-check-certificate https://github.com/crazycat69/media_build/releases/download/latest/dvb-firmwares.tar.bz2
tar -xvjf dvb-firmwares.tar.bz2 -C /lib/firmware
rm -f dvb-firmwares.tar.bz2

if [[ -d $BUILD_DIR ]]; then
	rm -rf $BUILD_DIR
fi
if [[ ! -d $INSTALL_E2DIR ]]; then
	mkdir -p $INSTALL_E2DIR/lib/enigma2
fi

mkdir -v $BUILD_DIR
cd $BUILD_DIR

# Build and install libdvbsi++-git:
LB="libdvbsi++1"
PKG="libdvbsi++"
#PKG="libdvbsi-"
echo ""
echo "                    *** Build and install $PKG ***"
echo ""
dpkg -s $PKG-dev | grep -iw ok > /dev/null
if [[ $? -eq 0 ]]; then
	dpkg -r $LB $LB-dbgsym $PKG-dev
else
	echo "$PKG not installed"
fi
if [[ -d $PKG ]]; then
	rm -rf $PKG
fi
git clone https://git.code.sf.net/p/tuxbox-cvs/$PKG
#git clone --depth 1 https://github.com/OpenVisionE2/$PKG.git
cd $PKG
#autoupdate
dpkg-buildpackage -b -d -uc -us
cd ..
mv $PKG*.* $PKG
cd $PKG
dpkg -i *deb
rm -f *.tar.xz
make distclean
cd ..

# Build and install libxmlccwrap:
if [[ ! -d libdvbsi++ ]]; then
	set -e
	set -o pipefail
else
	PKG="libxmlccwrap"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                     *** Build and install $PKG ***"
	echo ""
	dpkg -s $PKG | grep -iw ok > /dev/null
	if [[ $? -eq 0 ]]; then
		dpkg -r $PKG $PKG-dev $PKG-dbgsym
	else
		echo "$PKG not installed"
	fi
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget https://www.i-have-a-dreambox.com/Sources/$PKG-0.0.12.tar.gz
	tar -xvf $PKG-0.0.12.tar.gz
	rm -f $PKG-0.0.12.tar.gz
	cd $PKG-0.0.12
	./configure --prefix=/usr
	checkinstall -D --install=yes --default --pkgname=$PKG --pkgversion=1.2.0 --maintainer=e2pc@gmail.com --pkggroup=video --gzman=yes
	make distclean
	cd ..
fi

# Build and install libtuxtxt:
if [[ ! -d libxmlccwrap-0.0.12 ]]; then
	set -e
	set -o pipefail
else
	SOURCE="tuxtxt-git"
	PKG="libtuxtxt"
	PKG_="tuxtxt"
	VER="1402795d660955757d87967b8ff1e3790625f9c1"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                       *** Build and install $PKG ***"
	echo ""
	dpkg -s $PKG | grep -iw ok > /dev/null
	if [[ $? -eq 0 ]]; then
		dpkg -r $PKG
	else
		echo "$PKG not installed"
	fi
	if [[ -d $SOURCE ]]; then
		dpkg -r $PKG $PKG_
		rm -rf $SOURCE
	fi

	wget --no-check-certificate https://github.com/OpenPLi/$PKG_/archive/$VER.zip
	unzip $VER.zip
	rm $VER.zip
	mv $PKG_-$VER $SOURCE
	cd ..
	cp -v patches/$PKG_.patch libs/$SOURCE
	cd libs/$SOURCE
	patch -p1 < $PKG_.patch
	echo ""
	echo "                       *** patches for $PKG applied ***"
	echo ""
	cd $PKG
#	autoupdate
	autoreconf -i
	./configure --prefix=/usr --with-boxtype=generic DVB_API_VERSION=5
	checkinstall -D --install=yes --default --pkgname=$PKG --pkgversion=1.0 --maintainer=e2pc@gmail.com --pkggroup=video --gzman=yes
	rm -f *.tgz
	make distclean
	cd ..
fi

# Build and install tuxtxt:
if [[ ! -d libtuxtxt ]]; then
	set -e
	set -o pipefail
else
	INSTALL_E2DIR="/usr/local/e2"
	PKG="tuxtxt"
	DIR="Tuxtxt"

	ln -sf $INSTALL_E2DIR/lib/enigma2 /usr/lib

	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                        *** Build and install $PKG ***"
	echo ""
	dpkg -s $PKG | grep -iw ok > /dev/null
	if [[ $? -eq 0 ]]; then
		echo "$PKG already installed"
	else
		mkdir -p $INSTALL_E2DIR/lib/enigma2/python/Plugins/Extensions/$DIR
		cd $PKG

		#autoupdate
		autoreconf -i
		./configure --prefix=/usr --with-boxtype=generic --with-configdir=/usr/etc --with-fbdev=/dev/fb0 --with-textlcd DVB_API_VERSION=5
		checkinstall -D --install=yes --default --pkgname=$PKG --pkgversion=1.0 --maintainer=e2pc@gmail.com --pkggroup=video --gzman=yes
		rm -f *.tgz
		make distclean
		cd ../..
	fi
fi

# Build and install aio-grab-git:
if [[ ! -d tuxtxt-git/tuxtxt ]]; then
	set -e
	set -o pipefail
else
	PKG="aio-grab"
	VER="cf62da47eedb6afe4c44949253ef0b876deb2105"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                       *** Build and install $PKG ***"
	echo ""
	dpkg -s $PKG | grep -iw ok > /dev/null
	if [[ $? -eq 0 ]]; then
		dpkg -r $PKG
	else
		echo "$PKG not installed"
	fi
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget --no-check-certificate https://github.com/OpenPLi/$PKG/archive/$VER.zip
	unzip $VER.zip
	rm $VER.zip
	mv $PKG-$VER $PKG
	cd $PKG
	autoreconf -i
	./configure --prefix=/usr
	checkinstall -D --install=yes --default --pkgname=$PKG --pkgversion=1.0 --maintainer=e2pc@gmail.com --pkggroup=video --gzman=yes
	rm -f *.tgz
	make distclean
	cd ..
fi

# Build and install gst-plugin-dvbmediasink-git:
if [[ ! -d aio-grab ]]; then
	set -e
	set -o pipefail
else
	LIB="libgstreamer-plugins-dvbmediasink"
	PKG="gst-plugin-dvbmediasink"
	VER="1d197313832d39fdaf430634f62ad95a33029db0"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                 *** Build and install $PKG ***"
	echo ""
	dpkg -s $LIB | grep -iw ok > /dev/null
	if [[ $? -eq 0 ]]; then
		dpkg -r $LIB
	else
		echo "$LIB not installed"
	fi
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget --no-check-certificate https://github.com/OpenPLi/$PKG/archive/$VER.zip
	unzip $VER.zip
	rm $VER.zip
	mv $PKG-$VER $PKG
	ln -s /usr/lib/x86_64-linux-gnu/gstreamer-1.0 /usr/lib
	cd $PKG
#	autoupdate
	autoreconf -i
	./configure --prefix=/usr --with-wma --with-wmv --with-pcm --with-dtsdownmix --with-eac3 --with-mpeg4 --with-mpeg4v2 --with-h263 --with-h264 --with-h265
	checkinstall -D --install=yes --default --pkgname=$LIB --pkgversion=1.0.0 --maintainer=e2pc@gmail.com --pkggroup=video --gzman=yes
	rm -f *.tgz
	make distclean
	cd ..
fi

# Build and install gst-plugin-subsink-git:
if [[ ! -d gst-plugin-dvbmediasink ]]; then
	set -e
	set -o pipefail
else
	LB="libgstreamer-plugins-subsink"
	PKG="gst-plugin-subsink"
	VER="2c4288bb29e0781f27aecc25c941b6e441630f8d"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                    *** Build and install $PKG ***"
	echo ""
	dpkg -s $LB | grep -iw ok > /dev/null
	if [[ $? -eq 0 ]]; then
		dpkg -r $LB
	else
		echo "$LB not installed"
	fi
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget --no-check-certificate https://github.com/OpenPLi/$PKG/archive/$VER.zip
	unzip $VER.zip
	rm $VER.zip
	mv $PKG-$VER $PKG
	cd ..
	cp -v patches/subsink_1.0.patch libs/$PKG
	cd libs/$PKG
	echo "AC_CONFIG_MACRO_DIR([m4])" >> configure.ac
	patch -p1 < subsink_1.0.patch
	echo ""
	echo "                  *** Patch for $PKG applied ***"
	echo ""
	#autoupdate
	autoreconf -i
	./configure --prefix=/usr
	checkinstall -D --install=yes --default --pkgname=$LB --pkgversion=1.0 --maintainer=e2pc@gmail.com --pkggroup=video --gzman=yes
	rm -f *.tgz
	make distclean
	cd ..
fi

# Build and install twistedsnmp-python3:
if [[ ! -d gst-plugin-subsink ]]; then
	set -e
	set -o pipefail
else
	PKG="twistedsnmp"
	VER="caab5fb520ee8f1535a1500324a0254df268d0ba"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                    *** Build and install $PKG ***"
	echo ""
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget --no-check-certificate https://github.com/mcfletch/twistedsnmp/archive/caab5fb520ee8f1535a1500324a0254df268d0ba.zip
	unzip $VER.zip
	rm $VER.zip
	mv $PKG-$VER $PKG
	cd ..
	cp -v patches/$PKG-python3.patch libs/$PKG
	cd libs/$PKG
	patch -p1 < $PKG-python3.patch
	echo ""
	echo "                  *** Patch for $PKG applied ***"
	echo ""
	/home/$(logname)/.venv/e2pc/bin/pip install $prefix2/$PKG
	ln -s -f $prefix3/$PKG $prefix1
	cd ..
fi

# Build and install python3-pythonwifi:
if [[ ! -d twistedsnmp ]]; then
	set -e
	set -o pipefail
else
	PKG="pythonwifi"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                    *** Build and install $PKG ***"
	echo ""
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget --no-check-certificate https://github.com/athoik/pythonwifi/archive/refs/heads/master.zip
	unzip master.zip
	rm -f master.zip
	mv $PKG-master $PKG
	cd $PKG
	/home/$(logname)/.venv/e2pc/bin/pip install $prefix2/$PKG
	ln -s -f $prefix3/$PKG $prefix1
	cd ..
fi

# Build and install python3-Js2Py:
if [[ ! -d pythonwifi ]]; then
	set -e
	set -o pipefail
else
	PKG="Js2Py"
	PKG1="js2py"
	VER="b16d7ce90ac9c03358010c1599c3e87698c9993f"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                    *** Build and install $PKG ***"
	echo ""
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget --no-check-certificate https://github.com/PiotrDabkowski/Js2Py/archive/$VER.zip
	unzip $VER.zip
	rm $VER.zip
	mv $PKG-$VER $PKG
	cd ..
	cp patches/$PKG.patch libs/$PKG
	cd libs/$PKG
	patch -p1 < $PKG.patch
	/home/$(logname)/.venv/e2pc/bin/pip install $prefix2/$PKG
	ln -s -f $prefix3/$PKG1 $prefix1
	cd ..
fi

# Build and install python3-ipaddress:
if [[ ! -d Js2Py ]]; then
	set -e
	set -o pipefail
else
	PKG="ipaddress"
	VER="d8aef06cc3ca8a6fd8570cda665b2bb879a29390"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                    *** Build and install $PKG ***"
	echo ""
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget --no-check-certificate https://github.com/phihag/ipaddress/archive/$VER.zip
	unzip $VER.zip
	rm $VER.zip
	mv $PKG-$VER $PKG
	cd ..
	cp patches/$PKG.patch libs/$PKG
	cd libs/$PKG
	patch -p1 < $PKG.patch
	/home/$(logname)/.venv/e2pc/bin/pip install $prefix2/$PKG
	ln -s -f $prefix3/$PKG.py $prefix1
	cd ..
fi

# Build and install python3-pyload:
if [[ ! -d ipaddress ]]; then
	set -e
	set -o pipefail
else
	PKG="pyload"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                    *** Build and install $PKG ***"
	echo ""
	if [[ -d $PKG ]]; then
		rm -rf $PKG
	fi
	wget --no-check-certificate https://github.com/$PKG/$PKG/archive/refs/heads/main.zip
	unzip main.zip
	rm main.zip
	mv $PKG-main $PKG
	cd ..
	cp patches/$PKG.patch libs/$PKG
	cd libs/$PKG
	patch -p1 < $PKG.patch
	/home/$(logname)/.venv/e2pc/bin/pip install $prefix2/$PKG
	ln -s -f $prefix3/$PKG $prefix1
	cd ..
fi

# Message if error at any point of script
if [[ ! -d pyload ]]; then
	set -e
	set -o pipefail
	echo ""
	echo "          *** Forced stop script execution. It maybe сompilation error, ***"
	echo "           *** lost Internet connection or the server not responding. ***"
	echo "                    *** Check the log for more information. ***"
	echo ""
else
	cd ..
	if [[ ! -f /usr/lib/python3/dist-packages/fix-writing-after-channel-is-closed.patch ]]; then
		cp patches/fix-writing-after-channel-is-closed.patch /usr/lib/python3/dist-packages
		cd /usr/lib/python3/dist-packages
		patch -p1 < fix-writing-after-channel-is-closed.patch
	else
		echo ""
		echo "************************ The file http.py already patched. *************************"
		echo ""
	fi
	cd ..
	python3 -m compileall -f $prefix1
	echo ""
	echo "************************************ DONE! *****************************************"
fi
