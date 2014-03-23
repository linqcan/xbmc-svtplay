import sys

import xbmc
import xbmcgui

import svt
import helper

__playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

def add(url, title, thumbnail):
  list_item = __create_list_item(url, title, thumbnail)
  __playlist.add(list_item.getProperty("url"), list_item)

def remove(list_item):
  print list_item.getfilename()
  __playlist.remove(list_item.getfilename())

def clear():
  """
  Clears the playlist
  """
  __playlist.clear()

def getPlaylistAsListItems():
  """
  Returns the playlist as a list of xbmc.ListItems
  """
  size =  __playlist.size()
  i = 0
  items = []
  while i < size:
    list_item = __playlist.__getitem__(i)
    list_item.setProperty("id", str(i))
    print list_item.getLabel()
    items.append(list_item)
    i = i + 1
  
  return items

def play():
  """
  Starts playback of a playlist
  """
  xbmc.Player().play(__playlist)

def __create_list_item(url, title, thumbnail, urlResolved=False):
    list_item = xbmcgui.ListItem(
        label = title, 
        thumbnailImage = thumbnail
        )
    video_url = url
    if not urlResolved:
      # If URL has not been resolved already
      video_url = __get_video_url(url)
    list_item.setProperty("url", video_url)
    return list_item


def __get_video_url(url):
  url = svt.BASE_URL + url+ svt.JSON_SUFFIX
  json_obj = helper.getJsonObj(url)
  video_url = helper.getVideoUrl(json_obj)
  if not video_url:
    return ""
  return video_url

# To support XBMC.RunScript
if __name__ == "__main__":
  print("PLM called as script!")
  print(str(sys.argv))
  if len(sys.argv) < 2:
    print "No argument given!"
  else:
    if sys.argv[1] == "add" and len(sys.argv) > 4:
      add(sys.argv[2], sys.argv[3], sys.argv[4])
