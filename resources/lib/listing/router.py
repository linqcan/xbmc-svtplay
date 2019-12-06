from __future__ import absolute_import,unicode_literals
import re
from resources.lib.listing.common import Common
from resources.lib.listing.listitem import PlayItem
from resources.lib.api import svt
from resources.lib.api.graphql import GraphQL
from resources.lib import logging
from resources.lib import helper

try:
  # Python 2
  from urllib import quote
except ImportError:
  # Python 3
  from urllib.parse import quote

class BlockedForChildrenException(BaseException):
    def __init__(self):
        pass

class Router:
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
    MODE_CATEGORY = "ti"

    def __init__(self, addon, plugin_url, plugin_handle, default_fanart, settings):
        logging.log("Starting normal listing mode")
        self.graphql = GraphQL()
        self.common = Common(addon, plugin_url, plugin_handle, default_fanart, settings)
        self.localize = addon.getLocalizedString
        self.settings = settings

    def route(self, mode, url, params):
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
            self.view_episodes(url)
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

    def view_a_to_z(self):
        programs = self.graphql.getAtoO()
        self.__program_listing(programs)

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

    def view_programs_by_letter(self, letter):
        programs = self.graphql.getProgramsByLetter(letter)
        self.__program_listing(programs)

    def __program_listing(self, play_items):
        for play_item in play_items:
            logging.log(play_item.id)
            if self.common.is_geo_restricted(play_item):
                logging.log("Not showing {} as it is restricted to Sweden and geo setting is on".format(play_item.title))
                continue
            folder = True
            mode = self.common.MODE_PROGRAM
            info = {}
            if play_item.item_type == PlayItem.VIDEO_ITEM:
                mode = self.common.MODE_VIDEO
                folder = False
                info["title"] = play_item.title # Needed for now to trigger xbmcgui.ListItem::setInfo which makes the video playable
            self.common.add_directory_item(
                play_item.title,
                {
                    "mode": mode,
                    "url": play_item.id
                },
                thumbnail=play_item.thumbnail,
                folder=folder,
                info=info
            )

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
        else:
            raise AttributeError("Section {} is not supported!".format(section))
        if not items:
            return
        for item in items:
            mode = self.common.MODE_VIDEO
            if item.item_type == PlayItem.SHOW_ITEM:
                mode = self.common.MODE_PROGRAM
            self.common.create_dir_item(item, mode)

    def view_channels(self):
        channels = svt.getChannels()
        if not channels:
            return
        for channel in channels:
            self.common.create_dir_item(channel, self.common.MODE_VIDEO)

    def view_latest_news(self ):
        items = self.graphql.getLatestNews()
        if not items:
            return
        self.common.create_dir_items(items, self.common.MODE_VIDEO)

    def view_category(self, genre):
        play_items = self.graphql.getProgramsForGenre(genre)
        if not play_items:
            return
        for play_item in play_items:
            mode = self.common.MODE_PROGRAM
            if play_item.item_type == PlayItem.VIDEO_ITEM:
                mode = self.common.MODE_VIDEO
            self.common.create_dir_item(play_item, mode)

    def view_episodes(self, url):
        slug = url.split("/")[-1]
        logging.log("View episodes for {}".format(slug))
        episodes = self.graphql.getVideoContent(slug)
        self.common.view_episodes(episodes)

    def view_search(self):
        keyword = helper.getInputFromKeyboard(self.localize(30102))
        if keyword == "" or not keyword:
            self.view_start()
            return
        keyword = quote(keyword)
        logging.log("Search string: " + keyword)
        keyword = re.sub(r" ", "+", keyword)
        keyword = keyword.strip()
        results = self.graphql.getSearchResults(keyword)
        for result in results:
            mode = self.common.MODE_VIDEO
            if result.item_type == PlayItem.SHOW_ITEM:
                mode = self.common.MODE_PROGRAM
            self.common.create_dir_item(result, mode)

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
        