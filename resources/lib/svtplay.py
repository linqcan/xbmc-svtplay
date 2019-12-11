from __future__ import absolute_import,unicode_literals
import os
import re
import sys
import xbmc # pylint: disable=import-error
import xbmcaddon # pylint: disable=import-error
import xbmcgui # pylint: disable=import-error
import xbmcplugin # pylint: disable=import-error

from resources.lib.api import svt
from resources.lib.api.graphql import GraphQL
from resources.lib.settings import Settings
from resources.lib.listing.common import Common
from resources.lib import logging
from resources.lib import helper

try:
  # Python 2
  from urllib import quote
except ImportError:
  # Python 3
  from urllib.parse import quote

class BlockedForChildrenException(BaseException): #pylint: disable=function-redefined
    def __init__(self):
        pass

class SvtPlay:
    # List modes
    MODE_LIVE_PROGRAMS = "live"
    MODE_LATEST = "latest"
    MODE_LATEST_NEWS = 'news'
    MODE_POPULAR = "popular"
    MODE_LAST_CHANCE = "last_chance"
    MODE_CHANNELS = "kanaler"
    MODE_A_TO_O = "a-o"
    MODE_SEARCH = "search"
    MODE_CATEGORIES = "categories"
    MODE_LETTER = "letter"
    MODE_CATEGORY = "category"

    def __init__(self, plugin_handle, plugin_url, plugin_params):
        self.addon = xbmcaddon.Addon()
        self.localize = self.addon.getLocalizedString
        self.settings = Settings(self.addon)
        self.plugin_url = plugin_url
        self.plugin_handle = plugin_handle
        self.graphql = GraphQL()
        xbmcplugin.setContent(plugin_handle, "tvshows")
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_DATEADDED)
        self.default_fanart = os.path.join(
            xbmc.translatePath(self.addon.getAddonInfo("path") + "/resources/images/"),
            "background.png")
        self.common = Common(self.addon, plugin_url, plugin_handle, 
            self.default_fanart, self.settings)
        self.arg_params = helper.get_url_parameters(plugin_params)
        logging.log("Addon params: {}".format(self.arg_params))
        self.arg_mode = self.arg_params.get("mode")
        self.arg_url = self.arg_params.get("url", "")
    
    def run(self):
        if self.settings.kids_mode and not self.arg_params:
            logging.log("Kids mode, redirecting to genre Barn")
            self.arg_mode = self.MODE_CATEGORY
            self.arg_url = "barn"

        try:
            self.navigate(self.arg_mode, self.arg_url, self.arg_params)
        except BlockedForChildrenException:
            dialog = xbmcgui.Dialog()
            dialog.ok("SVT Play", self.addon.getLocalizedString(30504))
            return

        cacheToDisc = True
        if not self.arg_params:
            # No params means top-level menu.
            # The top-level menu should not be cached as it will prevent
            # Kids mode to take effect when toggled on.
            cacheToDisc = False
        xbmcplugin.endOfDirectory(self.plugin_handle, cacheToDisc=cacheToDisc)

    def navigate(self, mode, url, params):
        if not mode:
            self.view_start()
        elif mode == self.MODE_A_TO_O:
            if self.settings.alpha_program_listing:
                self.view_alpha_directories()
            else:
                self.view_a_to_z()
        elif mode == self.MODE_CATEGORIES:
            self.view_categories()
        elif mode == self.MODE_CATEGORY:
            self.view_category(url)
        elif mode == self.common.MODE_PROGRAM:
            self.view_video_content(url)
        elif mode == self.common.MODE_VIDEO:
            self.start_video(url)
        elif mode == self.MODE_POPULAR or \
            mode == self.MODE_LATEST or \
            mode == self.MODE_LAST_CHANCE or \
            mode == self.MODE_LIVE_PROGRAMS:
            self.view_start_section(mode)
        elif mode == self.MODE_LATEST_NEWS:
            self.view_latest_news()
        elif mode == self.MODE_CHANNELS:
            self.view_channels()
        elif mode == self.MODE_LETTER:
            self.view_programs_by_letter(params.get("letter"))
        elif mode == self.MODE_SEARCH:
            self.view_search()

    def view_start(self):
        self.common.add_directory_item(self.localize(30009), {"mode": self.MODE_POPULAR})
        self.common.add_directory_item(self.localize(30003), {"mode": self.MODE_LATEST})
        self.common.add_directory_item(self.localize(30004), {"mode": self.MODE_LATEST_NEWS})
        self.common.add_directory_item(self.localize(30010), {"mode": self.MODE_LAST_CHANCE})
        self.common.add_directory_item(self.localize(30002), {"mode": self.MODE_LIVE_PROGRAMS})
        self.common.add_directory_item(self.localize(30008), {"mode": self.MODE_CHANNELS})
        self.common.add_directory_item(self.localize(30000), {"mode": self.MODE_A_TO_O})
        self.common.add_directory_item(self.localize(30001), {"mode": self.MODE_CATEGORIES})
        self.common.add_directory_item(self.localize(30006), {"mode": self.MODE_SEARCH})


    def view_alpha_directories(self):
        letters = svt.getAlphas()
        if not letters:
            return
        for letter in letters:
            self.common.add_directory_item(
                letter, 
                {
                    "mode": self.MODE_LETTER,
                    "letter": letter.encode("utf-8")
                }
            )

    def view_a_to_z(self):
        programs = self.graphql.getAtoO()
        self.common.create_dir_items(programs)

    def view_programs_by_letter(self, letter):
        programs = self.graphql.getProgramsByLetter(letter)
        self.common.create_dir_items(programs)

    def view_categories(self):
        categories = self.graphql.getGenres()
        for category in categories:
            self.common.add_directory_item(
                category["title"],
                {
                    "mode": self.MODE_CATEGORY, 
                    "url": category["genre"]
                }
            )

    def view_start_section(self, section):
        items = []
        if section == self.MODE_POPULAR:
            items = self.graphql.getPopular()
        elif section == self.MODE_LATEST:
            items = self.graphql.getLatest()
        elif section == self.MODE_LAST_CHANCE:
            items = self.graphql.getLastChance()
        elif section == self.MODE_LIVE_PROGRAMS:
            items = self.graphql.getLive()
        else:
            raise ValueError("Section {} is not supported!".format(section))
        if not items:
            return
        self.common.create_dir_items(items)

    def view_channels(self):
        channels = svt.getChannels()
        if not channels:
            return
        self.common.create_dir_items(channels)

    def view_latest_news(self ):
        items = self.graphql.getLatestNews()
        if not items:
            return
        self.common.create_dir_items(items)

    def view_category(self, genre):
        play_items = self.graphql.getProgramsForGenre(genre)
        if not play_items:
            return
        self.common.create_dir_items(play_items)

    def view_video_content(self, url):
        slug = url.split("/")[-1]
        logging.log("View episodes for {}".format(slug))
        episodes = self.graphql.getVideoContent(slug)
        self.common.create_dir_items(episodes)

    def view_search(self):
        keyword = helper.getInputFromKeyboard(self.localize(30102))
        if keyword == "" or not keyword:
            self.view_start()
            return
        keyword = quote(keyword)
        logging.log("Search string: " + keyword)
        keyword = re.sub(r" ", "+", keyword)
        keyword = keyword.strip()
        play_items = self.graphql.getSearchResults(keyword)
        self.common.create_dir_items(play_items)

    def start_video(self, video_url):
        channel_pattern = re.compile(r'^ch\-')
        logging.log("Start video for {}".format(video_url))
        if channel_pattern.search(video_url):
            video_json = svt.getVideoJSON(video_url)
        else:
            legacy_id = video_url.split("/")[2]
            video_data = self.graphql.getVideoDataForLegacyId(legacy_id)
            if self.settings.inappropriate_for_children and video_data["blockedForChildren"]:
                raise BlockedForChildrenException()
            video_json = svt.getSvtVideoJson(video_data["svtId"])
        self.common.start_video(video_json)
