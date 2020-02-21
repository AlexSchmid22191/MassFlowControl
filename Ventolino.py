from pubsub.pub import addTopicDefnProvider, TOPIC_TREE_FROM_CLASS
import wx
import topic_def
from engine import Ventolino
from Interface import VentolinoGUI

addTopicDefnProvider(topic_def, TOPIC_TREE_FROM_CLASS)


def main():
    ex = wx.App()
    eng = Ventolino()
    g = VentolinoGUI(parent=None, channels=4)
    ex.MainLoop()


if __name__ == '__main__':
    main()
