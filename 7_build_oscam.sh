#!/bin/bash

SOURCE="oscam-trunk"
EMU="oscam-emu"
CONF="/etc/vdr/oscam"
BIN="/usr/local/bin"

echo "-------------------------------------------"
echo "          *** INSTALL OSCAM ***"
echo "-------------------------------------------"

cd oscam

if [ -d $SOURCE ]; then
	rm -fr $SOURCE
fi

git clone https://git.streamboard.tv/common/oscam.git $SOURCE

cd $SOURCE
wget https://sat-forum.net/download/file.php?id=24261
mv file.php?id=24261 $EMU.patch.rar
unrar x $EMU.patch.rar
rm -f $EMU.patch.rar
mv $EMU.patch.txt $EMU.patch

patch -p1 < $EMU.patch
./config.sh -E WITH_SSL MODULE_CONSTCW
make

mv -v Distribution/*.debug Distribution/oscam.debug
cp -fv Distribution/oscam-* $BIN/oscam
cd ..

echo "-------------------------------------------"
echo "*** COPY CONFIG FILES in /etc/vdr/oscam ***"
echo "       *** EDIT DATA FOR YOU ***"
echo "-------------------------------------------"

if [ ! -d $CONF ]; then
	mkdir -p $CONF
fi

if [ ! -d /var/log/oscam ]; then
	mkdir -p /var/log/oscam
fi

cp -rfv conf/* $CONF
cp -fv softcam.oscam $BIN
cp -fv oscamchk $BIN
cp -fv root /var/spool/cron/crontabs

if [ ! -f $BIN/softcam ]; then
	ln -s $BIN/softcam.oscam $BIN/softcam
fi

if [ ! -f $CONF/SoftCam.Key ]; then
	ln -s /var/keys/SoftCam.Key $CONF
	ln -s /var/keys/AutoRoll.Key $CONF
	ln -s /var/keys/Autoupdate.Key $CONF
fi

softcam restart
