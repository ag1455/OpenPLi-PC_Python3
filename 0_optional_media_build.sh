#!/bin/bash

git clone https://github.com/tbsdtv/media_build.git
cd media_build
./build
make install
cd ../../..

cd /lib/firmware
#zstd -f *.fw
rm -f *.fw

cd go7007
#zstd -f *.fw
rm -f *.fw

if [ -d dvb-firmware ]; then
	rm -rf dvb-firmware
fi

# If need more firmare
git clone https://github.com/OpenELEC/dvb-firmware.git
cd dvb-firmware/firmware
#zstd -f *.fw
#cp -f *.zst /lib/firmware
cp -f *.fw /lib/firmware

depmod -a
