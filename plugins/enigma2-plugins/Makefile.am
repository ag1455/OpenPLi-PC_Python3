ACLOCAL_AMFLAGS = -I m4

SUBDIRS = \
	antiscrollbar \
	automaticvolumeadjustment \
	bitrate \
	epgrefresh \
	epgsearch \
	filebrowser \
	ftpbrowser \
	mphelp \
	networkbrowser \
	permanentclock \
	pluginhider \
	recordinfobar \
	satipclient \
	servicemp3

metadir = $(datadir)/meta
meta_DATA = index-enigma2-plugins.xml
CLEANFILES = index-enigma2-plugins.xml

index-enigma2-plugins.xml: $(top_srcdir)/genmetaindex.py $(top_srcdir)/*/meta/plugin_*.xml
	$(AM_V_GEN)$(PYTHON) $^ > $@
