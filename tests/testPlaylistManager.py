import sys
# Manipulate path first
sys.path.append("../")
sys.path.append("./lib")

import resources.lib.PlaylistManager as PlaylistManager


def runTests():

  PlaylistManager.add(
      "/video/1897136/del-8-av-10",
      "Tjockare..",
      "http://www.svt.se/cachable_image/1389192612000/tjockare-an-vatten/article1717444.svt/ALTERNATES/medium/tjockare-an-vatten-logga-992.jpg")

  PlaylistManager.dump()

  PlaylistManager.play()

  PlaylistManager.clear()


if __name__ == "__main__":
  runTests()
