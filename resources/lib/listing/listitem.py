# -*- coding: utf-8 -*-
from __future__ import absolute_import,unicode_literals
from dateutil.parser import parse


class PlayItem(object):
    """
    A generic SVT Play list item
    """
    VIDEO_ITEM = "video"
    SHOW_ITEM = "show"

    def __init__(self, title, id, item_type, thumbnail="", geo_restricted=False, info={}, fanart=""):
        if not title:
            raise ValueError("Title is missing!")
        if not id:
            raise ValueError("ID is missing!")
        if not item_type:
            raise ValueError("Item type missing!")
        self.title = title
        self.id = id
        self.thumbnail = thumbnail
        self.geo_restricted = geo_restricted
        self.item_type = item_type
        self.info = info
        self.fanart = fanart

class VideoItem(PlayItem):
    """
    A video list item.
    """
    def __init__(self, title, video_id, thumbnail, geo_restricted, info={}, fanart=""):
        super(VideoItem, self).__init__(title, video_id, PlayItem.VIDEO_ITEM, thumbnail, geo_restricted, info, fanart)
        self.valid_from = None
    
    def setValidFrom(self, date_str):
        try:
            self.valid_from = parse(date_str)
        except:
            raise ValueError("{} is not a supported date string. Expected the following format \"2019-11-02T02:00:00+01:00\"".format(date_str))


    

class ShowItem(PlayItem):
    """
    A show list item, which means a folder containing VideoItems
    """
    def __init__(self, title, show_id, thumbnail, geo_restricted, info={}, fanart=""):
        super(ShowItem, self).__init__(title, show_id, PlayItem.SHOW_ITEM, thumbnail, geo_restricted, info, fanart)