import json
import os
import sys

import xbmc
import xbmcgui

import svt
import helper

FILE_PATH = os.path.join(xbmc.translatePath("special://temp"),"svtplaylist.json")

class Playlist:
  """
  Holds a playlist representation
  """
  
  def __init__(self):
    self.contents = {"items": []}
    self.loaded = False

__playlist = Playlist()

def add(url, title, thumbnail):
  if not __playlist.loaded:
    __load_from_file()

  __playlist.contents["items"].append(
        {
          "url": url,
          "title": title,
          "thumbnail": thumbnail
        }
      )
  __save_to_file()

def remove(item_id):
  if item_id < 0 or item_id > len(__playlist.contents["items"]):
    print("Illegal item id "+str(item_id))
    return
  del(__playlist.contents["items"][item_id])
  __save_to_file()

def __load_from_file():
  """
  Loads a playlist from disk
  """
  if os.path.exists(FILE_PATH):
    file_handle = open(FILE_PATH, "r")
    __playlist.contents = json.load(file_handle)
    file_handle.close()
  __playlist.loaded = True

def __save_to_file():
  """
  Stores a playlist to disk
  """
  file_handle = open(FILE_PATH, "w")
  json.dump(__playlist.contents, file_handle)
  file_handle.close()

def save():
  """
  Save a playlist to file

  Public access
  """
  __save_to_file()

def clear():
  """
  Clears the playlist
  """
  __playlist.contents["items"] = []
  __save_to_file()

def getPlaylist():
  if not __playlist.loaded:
    __load_from_file()

  return __playlist.contents["items"]

def getPlaylistAsListItems():
  """
  Returns the playlist as a list of xbmc.ListItems
  """
  if not __playlist.loaded:
    __load_from_file()

  items = []
  for index, item in enumerate(__playlist.contents["items"]):
    list_item = xbmcgui.ListItem(
        label=item["title"],
        path=item["url"],
        thumbnailImage=item["thumbnail"])
    list_item.setProperty("id", str(index))
    items.append(list_item)
  
  return items

def play():
  """
  Starts playback of a playlist
  """
  if not __playlist.loaded:
    __load_from_file()

  playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
  # Clear the current playlist first
  playlist.clear()
  for item in __playlist.contents["items"]:
    list_item = xbmcgui.ListItem(item["title"])
    list_item.setThumbnailImage(item["thumbnail"])
    url = __getVideoUrl(item["url"])
    playlist.add(url, list_item)

  print("Play list size:"+str(playlist.size()))
  xbmc.Player().play(playlist)

def __getVideoUrl(url):
  url = svt.BASE_URL + url+ svt.JSON_SUFFIX
  json_obj = helper.getJsonObj(url)
  video_url = helper.getVideoUrl(json_obj)
  if not video_url:
    return ""
  return video_url

def dump():
  print json.dumps(__playlist.contents)


# To support XBMC.RunScript
if __name__ == "__main__":
  print("PLM called as script!")
  print(str(sys.argv))
  if len(sys.argv) < 2:
    print "No argument given!"
  else:
    if sys.argv[1] == "add" and len(sys.argv) > 4:
      add(sys.argv[2], sys.argv[3], sys.argv[4])
