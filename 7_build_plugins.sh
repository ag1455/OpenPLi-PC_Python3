#!/bin/bash

# Build and install plugins for enigma2pc

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

export PYTHON_EXTRA_LIBS="-lpthread -ldl -lutil -lm"
export PYTHON_EXTRA_LDFLAGS="-Xlinker -export-dynamic -Wl,-O1 -Wl,-Bsymbolic-functions"

INSTALL_E2DIR="/usr/local/e2"
prefix1="/usr/local/e2/lib/enigma2/python/Plugins"
prefix2="/usr/src/OpenPLi-PC_Python3/plugins/e2openplugins"
prefix3="/usr/local/lib/python3.9/site-packages"
MAKE_J="8"

DSP=`xdpyinfo -display :0.0 2>/dev/null | grep dimensions | egrep -o "[0-9]+x[0-9]+ pixels" | egrep -o "[0-9]+x[0-9]+"`

if [ -d plugins ]; then # This is the lock from the unpredictable script actions in the root directory in the absence of the plugins folder.
	# Removing old compiled pyc files
	find $INSTALL_E2DIR/lib/enigma2/python/ -name "*.py[c]" -exec rm {} \;
	if [ ! -f plugins/third-party-plugins/Plugins/Extensions/navibar/navibar.patch ]; then
		cp patches/navibar.patch plugins/third-party-plugins/Plugins/Extensions/navibar
		cd plugins/third-party-plugins/Plugins/Extensions/navibar
		patch -p1 < navibar.patch
		cd ../../../../..
	fi
	cp -fv pre/include/rpc/* /usr/include/rpc
	cd plugins/enigma2-plugins

	# Build enigma2-plugins
	echo ""
	echo "************************** OK. Let's build the plugins. ****************************"
	echo ""
	PKG="servicemp3"
	VER="bdb5a908276b69a913ca50cb8c274d1b5977ad82"
	if [ -d $PKG ]; then
		rm -rf $PKG
	fi
	# Case of download error or process interruption
	if [ -f $PKG ]; then
		rm -rf $PKG
	fi
	if [ -d $PKG-$VER ]; then
		rm -rf $PKG-$VER
	fi
	wget https://github.com/OpenPLi/$PKG/archive/$VER.zip
	unzip $VER.zip
	rm $VER.zip
	mv $PKG-$VER $PKG
	cd ../..
	cp -fv patches/$PKG.patch plugins/enigma2-plugins/$PKG
	cd plugins/enigma2-plugins/$PKG
	patch -p1 < $PKG.patch
	cd ..
	#autoupdate
	autoreconf -i
	./configure --prefix=$INSTALL_E2DIR PKG_CONFIG_PATH=$INSTALL_E2DIR/lib/pkgconfig
	make -j"$MAKE_J"
	make install
	cd ..

	if [ -d e2openplugins ]; then
		rm -rf e2openplugins
		mkdir e2openplugins
	fi

	# Build enigma2-plugin-extensions-infobarweather
	if [ ! -d enigma2-plugins/servicemp3 ]; then
		set -e
		set -o pipefail
	else
		cd e2openplugins
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="enigma2-plugin-extensions-infobarweather"
		PKG_="InfoBarWeather"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/OpenPLi/$PKG/archive/refs/heads/main.zip
		unzip main.zip
		rm -f main.zip
		mv $PKG-main $PKG
		cd $PKG
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build enigma2-plugin-extensions-ts-sateditor:
	if [ ! -d enigma2-plugin-extensions-infobarweather ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="enigma2-plugin-extensions-ts-sateditor"
		PKG_="TSsatEditor"
		VER="d4a10ebbc7ef8e8349b218f48dbeab43f5685180"
		if [ -d $prefix3/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/Dima73/$PKG/archive/$VER.zip
		unzip $VER.zip
		rm $VER.zip
		mv $PKG-$VER $PKG
		cd ../..
		cp patches/tssateditor.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < tssateditor.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build e2openplugin-StreamInterface:
	if [ ! -d enigma2-plugin-extensions-ts-sateditor ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2openplugin-StreamInterface"
		PKG_="StreamInterface"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/E2OpenPlugins/$PKG/archive/refs/heads/python3.zip
		unzip python3.zip
		rm python3.zip
		mv $PKG-python3 $PKG
		cd ../..
		cp patches/$PKG_.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG_.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build e2openplugin-SystemTools
	if [ ! -d e2openplugin-StreamInterface ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2openplugin-SystemTools"
		PKG_="SystemTools"
		VER="88dbcac49202a4d850221841b8f16891f684a375"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/E2OpenPlugins/$PKG/archive/$VER.zip
		unzip $VER.zip
		rm $VER.zip
		mv $PKG-$VER $PKG
		cd ../..
		cp -fv patches/$PKG_.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG_.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build e2openplugin-AddStreamUrl
	if [ ! -d e2openplugin-SystemTools ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2openplugin-AddStreamUrl"
		PKG_="AddStreamUrl"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/E2OpenPlugins/$PKG/archive/refs/heads/python3.zip
		unzip python3.zip
		rm python3.zip
		mv $PKG-python3 $PKG
		cd ../..
		cp -fv patches/$PKG_.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG_.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build e2openplugin-e2openplugin-OpenWebif
	if [ ! -d e2openplugin-AddStreamUrl ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2openplugin-OpenWebif"
		PKG_="OpenWebif"
		VER="750db9715515c0fadb5f0c64e39dac21a1695bba"
		wget https://github.com/E2OpenPlugins/$PKG/archive/$VER.zip
		unzip $VER.zip
		rm $VER.zip
		mv $PKG-$VER $PKG
		cd ../..
		cp -fv patches/$PKG_.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG_.patch
		mv CI/create_ipk.sh create_ipk.sh
		./create_ipk.sh
		ar -x *.ipk
		tar -xvf data.tar.gz
		mv -f usr/lib/enigma2/python/Plugins/Extensions/$PKG_ $INSTALL_E2DIR/lib/enigma2/python/Plugins/Extensions # It's right
		rm -rf debian-binary usr *.gz *.ipk
		cd ..
	fi

	# Build e2openplugin-SetPicon
	if [ ! -d e2openplugin-OpenWebif ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2openplugin-SetPicon"
		PKG_="SetPicon"
		VER="6b777ed10fba7a825ba99ca8a27f6c381dee6d16"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/E2OpenPlugins/$PKG/archive/$VER.zip
		unzip $VER.zip
		rm $VER.zip
		mv $PKG-$VER $PKG
		cd ../..
		cp -fv patches/$PKG_.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG_.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build e2openplugin-SimpleUmount
	if [ ! -d e2openplugin-SetPicon ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2openplugin-SimpleUmount"
		PKG_="SimpleUmount"
		VER="c8517274748ebe7789b03cfcb4ff142332e7ea02"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/E2OpenPlugins/$PKG/archive/$VER.zip
		unzip $VER.zip
		rm $VER.zip
		mv $PKG-$VER $PKG
		cd ../..
		cp -fv patches/$PKG_.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG_.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build e2openplugin-Foreca
	if [ ! -d e2openplugin-SimpleUmount ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2openplugin-Foreca"
		PKG_="Foreca"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/E2OpenPlugins/$PKG/archive/refs/heads/python3.zip
		unzip python3.zip
		rm python3.zip
		mv $PKG-python3 $PKG
		cd ../..
		cp patches/$PKG_.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG_.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build enigma2-plugin-youtube
	if [ ! -d e2openplugin-Foreca ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="enigma2-plugin-youtube"
		PKG_="YouTube"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/Taapat/$PKG/archive/refs/heads/master.zip
		unzip master.zip
		rm master.zip
		mv $PKG-master $PKG
		cd $PKG
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build e2openplugin-OscamStatus
	if [ ! -d enigma2-plugin-youtube ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2openplugin-OscamStatus"
		PKG_="OscamStatus"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/E2OpenPlugins/$PKG/archive/refs/heads/master.zip
		unzip master.zip
		rm master.zip
		mv $PKG-master $PKG
		cd ../..
		cp -fv patches/$PKG_.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG_.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build enigma2-plugin-extensions-epgimport
	if [ ! -d e2openplugin-OscamStatus ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="enigma2-plugin-extensions-epgimport"
		PKG_="EPGImport"
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/OpenPLi/$PKG/archive/refs/heads/master.zip
		unzip -x master.zip
		rm master.zip
		mv $PKG-master $PKG
		cd ../..
		cp -fv patches/epgimport.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < epgimport.patch
		pip3.9 --disable-pip-version-check install $prefix2/$PKG/src
		cd ..
	fi

	# Build enigma2-plugin-mountmanager
	if [ ! -d enigma2-plugin-extensions-epgimport ]; then
		set -e
		set -o pipefail
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="enigma2-plugin-mountmanager"
		PKG_="MountManager"
		VER="342ac9a126533a8582f5f45ed2e0c8ac9c322fa0"
		if [ -d $prefix3/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://github.com/Dima73/$PKG/archive/$VER.zip
		unzip $VER.zip
		rm $VER.zip
		mv $PKG-$VER $PKG
		cd $PKG
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cd ..
	fi

	# Build e2iplayer
	if [ ! -d enigma2-plugin-mountmanager ]; then
		set -e
		set -o pipefail
		# Message if error at any point of script
		echo ""
		echo "************ Forced stop script execution. It maybe сompilation error, *************"
		echo "************** lost Internet connection or the server not responding. **************"
		echo "*********************** Check the log for more information. ************************"
		echo ""
	else
		echo ""
		echo "**************************** OK. Go to the next step. ******************************"
		echo ""
		PKG="e2iplayer"
		PKG_="IPTVPlayer"
		PKG__="E2IPlayer"
		VER="8f8f7a85a2d22c0c1af0d6d08e8e79ca53a517d9"
#		rm -f /usr/lib/librtmp.so.1
		if [ -d $prefix1/$PKG_ ]; then
			rm -rf $PKG_
		fi
		wget https://gitlab.com/zadmario/e2iplayer/-/archive/$VER/e2iplayer-$VER.zip
		unzip $PKG-$VER.zip
		rm $PKG-$VER.zip
		mv $PKG-$VER $PKG
		cd ../..
		cp -rv pre/icons plugins/e2openplugins/$PKG/$PKG_
		cp -fv patches/$PKG__.patch plugins/e2openplugins/$PKG
		cp -fv patches/E2IPlayer_4k_dimension.patch plugins/e2openplugins/$PKG
		cd plugins/e2openplugins/$PKG
		patch -p1 < $PKG__.patch
		# Patch and resize if you have 4K display.
		#DSP=`xdpyinfo -display :0.0 2>/dev/null | grep dimensions | egrep -o "[0-9]+x[0-9]+ pixels" | egrep -o "[0-9]+x[0-9]+"`
		if [ "$DSP" = "3840x2160" ]; then
			echo ""
			echo "*********************************** 4K display *************************************"
			echo ""
			if [ -f resize.sh ]; then
				rm -f resize.sh
			fi
			patch -p1 < E2IPlayer_4k_dimension.patch
			chmod 755 resize.sh
			./resize.sh
		else
			echo ""
			echo "*********************************** HD display *************************************"
			echo ""
		fi
		rm -f IPTVPlayer/locale/ru/LC_MESSAGES/.gitkeep
		pip3.9 --disable-pip-version-check install $prefix2/$PKG
		cp -rfv IPTVPlayer/locale $INSTALL_E2DIR/lib/enigma2/python/Plugins/Extensions/$PKG_
		if grep "config.plugins.iptvplayer.wgetpath=/usr/bin/wget" $INSTALL_E2DIR/etc/enigma2/settings; then
			echo ""
			echo ""
			echo "*************************** Detected $PKG_ settings.***************************"
		else
			echo ""
			echo "******************* There are no iptvplayer settings. Adding...*********************"
			echo "config.plugins.iptvplayer.autoCheckForUpdate=false" >> $INSTALL_E2DIR/etc/enigma2/settings
			echo "config.plugins.iptvplayer.deleteIcons=0" >> $INSTALL_E2DIR/etc/enigma2/settings
			echo "config.plugins.iptvplayer.downgradePossible=true" >> $INSTALL_E2DIR/etc/enigma2/settings
			echo "config.plugins.iptvplayer.dukpath=$INSTALL_E2DIR/lib/enigma2/python/Plugins/Extensions/$PKG_/bin/duk" >> $INSTALL_E2DIR/etc/enigma2/settings
			echo "config.plugins.iptvplayer.possibleUpdateType=sourcecode" >> $INSTALL_E2DIR/etc/enigma2/settings
			echo "config.plugins.iptvplayer.showinMainMenu=true" >> $INSTALL_E2DIR/etc/enigma2/settings
			echo "config.plugins.iptvplayer.uchardetpath=/usr/bin/uchardet" >> $INSTALL_E2DIR/etc/enigma2/settings
			echo "config.plugins.iptvplayer.wgetpath=/usr/bin/wget" >> $INSTALL_E2DIR/etc/enigma2/settings
		fi
	fi

	cd ../../..

	rsync -a --remove-source-files $prefix3/Extensions/ $prefix1/Extensions/
	rsync -a --remove-source-files $prefix3/SystemPlugins/ $prefix1/SystemPlugins/

	rm -rf $prefix3/Extensions
	rm -rf $prefix3/SystemPlugins

	# Copy files to $INSTALL_E2DIR
	echo ""
	echo "******************************** Copy  plugins E2PC ********************************"
	cp -rf plugins/third-party-plugins/* $INSTALL_E2DIR/lib/enigma2/python
	cp -rf pre/epgimport $INSTALL_E2DIR/etc
	cp -rf pre/xmltvimport $INSTALL_E2DIR/etc
	cp -rf skins/* $INSTALL_E2DIR

	if [ "$DSP" = "3840x2160" ]; then
		rpl '1080' '2160' $INSTALL_E2DIR/lib/enigma2/python/Plugins/Extensions/SatellitesGen/plugin.py
	fi

	if [ ! -f /usr/local/bin/bitrate ]; then
		ln -sf $INSTALL_E2DIR/bin/bitrate /usr/local/bin
	fi

	# Create folder for softam keys and symlink for plugin 'navibar'
	if [ ! -d /var/keys ]; then
		mkdir -p /var/keys
	fi

	if [ ! -d /home/hdd/icons ]; then
		ln -s $INSTALL_E2DIR/lib/enigma2/python/Plugins/Extensions/navibar/icons /media/hdd
	fi

	cd ../../..$prefix1/Extensions
	rm -rf DVDBurn

	# For use *.m3u8 in the /tmp folder
	#chown $(who | gawk '{print $1}') /tmp

	echo ""
	echo "************* Plugins, skins, E2PC python files installed successfully.*************"
else
	echo ""
	echo "************ Plugins folder is missing! Please run scripts step by step! ************"
	echo ""
fi # End lock
