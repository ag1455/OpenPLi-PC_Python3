#!/bin/bash

# To build enigma2 on Ubuntu 24.04 with startup option "Ubuntu on Xorg".

dpkg --configure -a

echo ""
echo "                       *** INSTALL REQUIRED PACKAGES ***"
echo ""

release=$(lsb_release -a 2>/dev/null | grep -i release | awk ' { print $2 } ')

REQPKG_ALL="ant aptitude autoconf automake autopoint avahi-daemon bash build-essential checkinstall chrpath cmake coreutils cvs debhelper desktop-file-utils docbook-utils \
	diffstat dvb-apps dvdbackup ethtool fakeroot flex ffmpeg gawk gettext git help2man linux-headers-`uname -r` libdvdnav-dev libfreetype6-dev libfribidi-dev libsigc++-2.0-dev \
	libpcsclite-dev libjpeg8-dev libgif-dev libjpeg-turbo8-dev libgiftiio0 libaio-dev libxinerama-dev libxt-dev libasound2-dev libcaca-dev libpulse-dev libvorbis-dev \
	libgtk2.0-dev libtool libxml2-dev libxml2-utils libxslt1-dev libssl-dev libvdpau-dev libcdio-dev libcrypto++-dev libudf-dev libvcdinfo-dev libusb-1.0-0-dev \
	libavcodec-dev libavformat-dev libpostproc-dev libavutil-dev libnl-3-dev libbluray-dev libmpcdec-dev libvpx-dev libnl-genl-3-dev libavahi-client3 libavahi-client-dev \
	libflac-dev libogg-dev libxcb-xv0-dev libxcb-shape0-dev libxv-dev libxvmc-dev libaa1-dev libmodplug-dev libjack-jackd2-dev libdirectfb-dev libmagickwand-dev libdvbcsa-dev \
	libwavpack-dev libspeex-dev libmng-dev libmad0-dev librsvg2-bin libtheora-dev libsmbclient-dev liblircclient-dev librtmp1 libmng2 libx11-6 libxext6 libglib2.0-dev \
	libelf-dev libmysqlclient-dev libupnp-dev libgiftiio-dev libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev gstreamer1.0-libav mawk mercurial mingetty mjpegtools \
	net-tools openssh-sftp-server pmccabe patch pkg-config rpl rsyslog rtmpdump sdparm setserial smartmontools software-properties-common sphinx-common streamripper \
	subversion texi2html texinfo unclutter unzip uchardet w3m vsftpd xmlto xterm ubuntu-restricted-extras wavpack imagemagick \
	"

for p in $REQPKG_ALL; do
	echo -n ">>> Checking \"$p\" : "
	dpkg -s $p >/dev/null
	if [[ "$?" -eq "0" ]]; then
		echo "package is installed, skip it"
	else
		echo "package NOT present, installing it"
		apt-get -y install $p
	fi
done

if [[ "$release" = "24.04" ]]; then
	dpkg-reconfigure python3
	echo ""
	echo "************************************************************************************"
	echo "                             *** release 24.04 ***"
	echo "************************************************************************************"
	echo ""
	REQPKG1="ant aptitude autoconf automake autopoint avahi-daemon bash build-essential checkinstall chrpath cmake coreutils cvs debhelper desktop-file-utils docbook-utils \
	diffstat dvb-apps dvdbackup ethtool fakeroot flex ffmpeg gawk gettext git help2man linux-headers-`uname -r` libdvdnav-dev libfreetype-dev libfribidi-dev libsigc++-2.0-dev \
	libpcsclite-dev libjpeg8-dev libgif-dev libjpeg-turbo8-dev libgiftiio0 libaio-dev libxinerama-dev libxt-dev libasound2-dev libcaca-dev libpulse-dev libvorbis-dev \
	libgtk2.0-dev libtool libxml2-dev libxml2-utils libxslt1-dev libssl-dev libvdpau-dev libcdio-dev libcrypto++-dev libudf-dev libvcdinfo-dev libusb-1.0-0-dev libavdevice-dev \
	libavcodec-dev libavformat-dev libpostproc-dev libavutil-dev libnl-3-dev libbluray-dev libmpcdec-dev libvpx-dev libnl-genl-3-dev libavahi-client3 libavahi-client-dev \
	libflac-dev libogg-dev libxcb-xv0-dev libxcb-shape0-dev libxv-dev libxvmc-dev libaa1-dev libmodplug-dev libjack-jackd2-dev libdirectfb-dev libmagickwand-dev \
	libwavpack-dev libspeex-dev libmng-dev libmad0-dev librsvg2-bin libtheora-dev libsmbclient-dev liblircclient-dev librtmp1 libmng2 libx11-6 libxext6 libglib2.0-dev \
	libelf-dev libmysqlclient-dev libupnp-dev libgiftiio-dev libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev gstreamer1.0-libav mawk mercurial mingetty mjpegtools \
	net-tools openssh-sftp-server pmccabe patch pkg-config rpl rsyslog rtmpdump sdparm setserial smartmontools software-properties-common sphinx-common streamripper \
	subversion texi2html texinfo unclutter unzip uchardet yt-dlp w3m vsftpd xmlto xterm ubuntu-restricted-extras wavpack libset-scalar-perl libpython3.12-dev libdvbcsa-dev \
	flake8 gcc-13 g++-13 libdav1d-dev libssl3t64 libdca-dev libsdl2-dev libtool-bin libpng-dev libqt5gstreamer-dev libva-glx2 libva-dev liba52-0.7.4-dev libffi8 libfuture-perl \
	ntpsec pycodestyle sqlite3 sphinx-rtd-theme-common libupnp-dev libvdpau1 libvdpau-va-gl1 libv4l-dev dh-exec libgnutls28-dev libaom-dev libsdl1.2-dev swig libsigc++-3.0-dev \
	streamlink yamllint ntpsec-ntpdate pkg-kde-tools neurodebian-popularity-contest popularity-contest pylint python3-full python3-transmissionrpc python3-flickrapi \
	python3-demjson python3-mechanize python3-sendfile python3-blessings python3-httpretty python3-mutagen python3-urllib3 python3-pymysql python3-sphinxcontrib.websupport \
	python3-sphinxcontrib.httpdomain python3-langdetect python3-restructuredtext-lint python3-ntplib python3-ntp python3-pysnmp4 python3-asn1crypto python3-attr python3-autobahn \
	python3-biplist python3-cheroot python3-cheetah python3-cherrypy3 python3-circuits python3-cssselect python3-dnspython python3-feedparser python3-fuzzywuzzy python3-guessit \
	python3-icalendar python3-isodate python3-ndg-httpsclient python3-notify2 python3-pbkdf2 python3-puremagic python3-pycountry python3-pytest python3-singledispatch \
	python3-sphinx-rtd-theme python3-streamlink python3-levenshtein python3-sgmllib3k python3-ujson python3-willow python3-num2words 7zip 7zip-rar unar dbus-x11 gtkhash \
	"

	for p in $REQPKG1; do
		echo -n ">>> Checking \"$p\" : "
		dpkg -s $p >/dev/null
		if [[ "$?" -eq "0" ]]; then
			echo "package is installed, skip it"
		else
			echo "package NOT present, installing it"
			apt-get -y install $p
		fi
	done

	apt install -y python3-venv
	python3 -m venv /home/$(logname)/.venv/e2pc
	/home/$(logname)/.venv/e2pc/bin/pip install pysmb zope.interface pycryptodomex pysocks rbtranslations soco tenjin tcpbridge pyserial PyHamcrest pyexecjs py3amf pillow gdata-python3 \
	futures3 cfscrape bluetool pyopenssl pyusb websockets PyCryptodome

	if [[ -d driver ]]; then
		rm -fr driver
	fi
	mkdir driver
	cd driver
	wget http://archive.ubuntu.com/ubuntu/pool/universe/i/intel-vaapi-driver/i965-va-driver_2.4.1+dfsg1-1_amd64.deb
	wget http://archive.ubuntu.com/ubuntu/pool/universe/i/intel-media-driver/intel-media-va-driver_22.3.1+dfsg1-1ubuntu2_amd64.deb
	wget http://archive.ubuntu.com/ubuntu/pool/universe/libv/libva/va-driver-all_2.14.0-1_amd64.deb
	dpkg -i *deb
	cd ..

	if [[ -d libva ]]; then
	rm -fr libva
	fi
	mkdir libva
	cd libva
	wget http://archive.ubuntu.com/ubuntu/pool/universe/libv/libva/libva2_2.14.0-1_amd64.deb
	wget http://archive.ubuntu.com/ubuntu/pool/universe/libv/libva/libva-dev_2.14.0-1_amd64.deb
	wget http://archive.ubuntu.com/ubuntu/pool/universe/libv/libva/libva-drm2_2.14.0-1_amd64.deb
	wget http://archive.ubuntu.com/ubuntu/pool/universe/libv/libva/libva-glx2_2.14.0-1_amd64.deb
	wget http://archive.ubuntu.com/ubuntu/pool/universe/libv/libva/libva-wayland2_2.14.0-1_amd64.deb
	wget http://archive.ubuntu.com/ubuntu/pool/universe/libv/libva/libva-x11-2_2.14.0-1_amd64.deb
	dpkg -i *deb
	cd ..
	apt clean

	echo ""
	echo "NOW THE SYSTEM WILL BE RESTARTED!"
	echo ""
	sleep 2
	reboot  # Need to restart system!
fi
