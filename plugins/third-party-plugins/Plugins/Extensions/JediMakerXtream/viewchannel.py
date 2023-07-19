#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import downloads
from . import jedi_globals as glob

from .plugin import skin_path
from .jediStaticText import StaticText

from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Screens.Screen import Screen
import json


class JediMakerXtream_ViewChannels(Screen):

    def __init__(self, session, current):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, "channels.xml")

        with open(skin, "r") as f:
            self.skin = f.read()

        self.list = []
        self["viewlist"] = List(self.list)

        self.setup_title = _("Channel List")

        self.current = current

        self["actions"] = ActionMap(["JediMakerXtreamActions"], {
            "ok": self.quit,
            "cancel": self.quit,
            "red": self.quit,
        }, -2)

        self["key_red"] = StaticText(_("Close"))

        self.onFirstExecBegin.append(self.getchannels)
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def quit(self):
        self.close()

    def getchannels(self):
        self.list = []

        username = glob.current_playlist["playlist_info"]["username"]
        password = glob.current_playlist["playlist_info"]["password"]
        protocol = glob.current_playlist["playlist_info"]["protocol"]
        domain = glob.current_playlist["playlist_info"]["domain"]
        port = str(glob.current_playlist["playlist_info"]["port"])
        host = str(protocol) + str(domain) + ":" + str(port) + "/"
        player_api = str(host) + "player_api.php?username=" + str(username) + "&password=" + str(password)
        liveStreamsUrl = player_api + "&action=get_live_streams"
        vodStreamsUrl = player_api + "&action=get_vod_streams"
        seriesUrl = player_api + "&action=get_series"

        category = self.current[1]
        category_id = self.current[2]

        url = ""

        if category == "Live":
            url = liveStreamsUrl + "&category_id=" + str(category_id)

        elif category == "VOD":
            url = vodStreamsUrl + "&category_id=" + str(category_id)

        elif category == "Series":
            url = seriesUrl + "&category_id=" + str(category_id)

        response = downloads.checkGZIP(url)

        if response:
            try:
                streamlist = json.loads(response)
            except Exception as e:
                print(e)
            try:
                for stream in streamlist:
                    if "name" in stream:
                        name = str(stream["name"])
                        self.list.append((name, "test"))
            except Exception as e:
                print(e)

        self.list.sort()

        self["viewlist"].list = self.list
        self["viewlist"].setList(self.list)
