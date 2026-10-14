#!/bin/bash

# Unfortunately e2pc doesn't work with wayland
#cp -fv /etc/gdm3/custom.conf /etc/gdm3/custom.conf~
#rpl '#WaylandEnable=false' 'WaylandEnable=false' /etc/gdm3/custom.conf

prefix1="/usr/src/OpenPLi-PC_Python3/libs"

#cd ../../..
#/root/./venv.sh
#cd /usr/src/OpenPLi-PC_Python3

if [ -d libs ]; then
	rm -rf libs
	mkdir libs
	cd libs
fi

# 1. Your source flags for the compiler
export PYTHON_CPPFLAGS=-I/usr/local/include/python3.9
export PYTHON_LDFLAGS="-L/usr/local/lib -lpython3.9"
# 2. Redefining default variables for ./configure and make or /usr/bin/python3.9, check where 3.9.25 is located
export PYTHON=/usr/local/bin/python3.9
export PYTHON3=/usr/local/bin/python3.9
export PYTHON_CONFIG=/usr/local/bin/python3.9-config
# 3. We replace the python/python3 command on the fly for all child make scripts
mkdir -p /tmp/python39-bin
ln -sf $(which python3.9) /tmp/python39-bin/python
ln -sf $(which python3.9) /tmp/python39-bin/python3
ln -sf $(which python3.9-config) /tmp/python39-bin/python3-config
export PATH=/tmp/python39-bin:$PATH

# Build and install python3-pythonwifi
PKG1="pythonwifi"
echo ""
echo "**************************** OK. Go to the next step. ******************************"
echo ""
echo "                    *** Build and install $PKG1 ***"
echo ""
wget https://github.com/OpenPLi/$PKG1/archive/refs/heads/master.zip
unzip master.zip
rm -f master.zip
mv $PKG1-master $PKG1
cd $PKG1
pip3.9 --disable-pip-version-check install $prefix1/$PKG1
cd ..

if [ ! -d pythonwifi ]; then
	set -e
	set -o pipefail
else
	PKG2="pyload"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                    *** Build and install $PKG2 ***"
	echo ""
	wget --no-check-certificate https://github.com/$PKG2/$PKG2/archive/refs/heads/main.zip
	unzip main.zip
	rm main.zip
	mv $PKG2-main $PKG2
	cd ..
	cp patches/$PKG2.patch libs/$PKG2
	cd libs/$PKG2
	patch -p1 < $PKG2.patch
	pip3.9 --disable-pip-version-check install $prefix1/$PKG2
	cd ..
fi

# Build and install Cheetah3
if [ ! -d pyload ]; then
	set -e
	set -o pipefail
else
	PKG3="cheetah3"
	echo ""
	echo "**************************** OK. Go to the next step. ******************************"
	echo ""
	echo "                    *** Build and install $PKG3 ***"
	echo ""
	wget https://github.com/CheetahTemplate3/$PKG3/archive/refs/heads/master.zip
	unzip master.zip
	rm master.zip
	mv -f $PKG3-master $PKG3
	pip3.9 --disable-pip-version-check install $prefix1/$PKG3
fi

# Message if error at any point of script
if [ ! -d cheetah3 ]; then
	set -e
	set -o pipefail
	echo ""
	echo "          *** Forced stop script execution. It maybe сompilation error, ***"
	echo "           *** lost Internet connection or the server not responding. ***"
	echo "                    *** Check the log for more information. ***"
	echo ""
fi
echo ""
echo "************************************ DONE! *****************************************"
echo ""
cd ..