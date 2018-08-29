import wx
from pubsub.pub import sendMessage, subscribe


class Minimalapp(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetTitle('Test GUI')

        self.label = wx.StaticText(parent=self, label='Still empty')

        self.btn1 = wx.Button(parent=self, label='Start')

        sizer = wx.BoxSizer(orient=wx.VERTICAL)

        sizer.Add(self.btn1, flag=wx.EXPAND, proportion=1)
        sizer.Add(self.label, flag=wx.EXPAND, proportion=1)

        self.btn1.Bind(wx.EVT_BUTTON, self.start_worker)

        self.SetSizer(sizer)

        subscribe(self.log_post, 'topic-test_wtg')

        sizer.Fit(self)

        self.Show()

    def log_post(self, msg):
        msg = str(msg)

        self.label.SetLabel(msg)
        print(msg)

    def start_worker(self, *args):
        sendMessage(topicName='topic-test_gtw', inp=20)


class SlowWorker:
    def __init__(self):
        subscribe(self.doubler, 'topic-test_gtw')

    def doubler(self, inp):
        print(vars())
        result = 2 * inp
        sendMessage(topicName='topic-test_wtg', msg=result)


def main():
    ex = wx.App()
    gui = Minimalapp(parent=None)
    worker = SlowWorker()
    ex.MainLoop()


if __name__ == '__main__':
    main()
