import wx
from pubsub.pub import subscribe, sendMessage
from serial.tools.list_ports import comports
from ThreadDecorators import in_main_thread
from engine import Ventolino


class VentolinoGUI(wx.Frame):
    def __init__(self, channels, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.channels = channels

        self.timer = wx.Timer(self)
        self.Bind(event=wx.EVT_TIMER, source=self.timer, handler=self.update)

        self.SetBackgroundColour('white')

        self.menu_bar = Menubar(style=wx.BORDER_NONE, timer=self.timer)
        self.SetMenuBar(self.menu_bar)
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.on_connect, source=self.menu_bar.rod_com_menu.connect)

        self.status_bar = wx.StatusBar(parent=self)
        self.SetStatusBar(self.status_bar)
        subscribe(listener=self.set_status, topicName='ETG_status')

        self.MFC = []
        if channels == 1:
            sizer = wx.GridSizer(rows=1, cols=1, vgap=0, hgap=0)
        elif channels == 2:
            sizer = wx.GridSizer(rows=1, cols=2, vgap=0, hgap=0)
        else:
            sizer = wx.GridSizer(rows=2, cols=2, vgap=0, hgap=0)

        for channel in range(channels):
            self.MFC.append(MFCChannelPanel(parent=self, channel=channel + 1))
            sizer.Add(self.MFC[channel], border=5, flag=wx.ALL)

        sizer.Fit(self)
        self.SetSizer(sizer)
        self.SetMinSize(self.GetSize())
        self.Show(True)

    def on_quit(self, *args):
        self.Close()

    @in_main_thread
    def set_status(self, text=''):
        """Display text in status bar, clear status bar after 4 seconds. Can be called from external Thread"""
        self.status_bar.SetStatusText(text)
        wx.CallLater(millis=4000, callableObj=self.status_bar.SetStatusText, text='')

    def update(self, *args):
        """Request data from the engine"""
        for chan in range(self.channels):
            sendMessage(topicName='GTE_read_is_flow', channel=chan+1)
            sendMessage(topicName='GTE_read_set_flow', channel=chan+1)

        self.timer.Start(1000)

    def on_connect(self, *args):
        """Start timer for GUI update on serial conection"""
        self.timer.Start(2000)


class MFCChannelPanel(wx.Panel):
    def __init__(self, channel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.channel = channel

        subscribe(topicName='ETG_read_is_flow', listener=self.update_flow_is_data)
        subscribe(topicName='ETG_read_set_flow', listener=self.update_flow_set_data)

        self.set_button = wx.Button(parent=self, label='Set Flow')
        self.set_button.Bind(wx.EVT_BUTTON, self.set_flow)

        self.flow_control = wx.SpinCtrlDouble(parent=self, value='0', min=0, max=100, inc=0.1, style=wx.SP_ARROW_KEYS,
                                              size=(70, 20))

        self.is_label = wx.StaticText(parent=self, label='Flow: {: >4.1f}'.format(0))
        self.set_label = wx.StaticText(parent=self, label='Set: {: >4.1f}'. format(0))

        gridsizer = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=20)
        gridsizer.Add(self.is_label, proportion=1, flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gridsizer.Add(self.flow_control, proportion=1, flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gridsizer.Add(self.set_label, proportion=1, flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gridsizer.Add(self.set_button, proportion=1, flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        self.gauge = wx.Gauge(parent=self, range=100, style=wx.GA_SMOOTH)

        box = wx.StaticBox(parent=self, label='MFC Channel {:1d}'.format(channel))
        boxsizer = wx.StaticBoxSizer(box, orient=wx.VERTICAL)
        boxsizer.Add(gridsizer)
        boxsizer.Add(self.gauge)

        self.SetSizerAndFit(boxsizer)

    def set_flow(self, *args):
        flow_value = self.flow_control.GetValue()
        assert 0.0 <= flow_value <= 100.0, 'Invalid flow percentage'
        sendMessage(topicName='GTE_set_flow', channel=self.channel, flow=flow_value)

    @in_main_thread
    def update_flow_is_data(self, channel, flow):
        if channel == self.channel:
            self.is_label.SetLabel('Flow: {:3.1f}%'.format(flow))
            self.gauge.SetValue(int(flow))

    @in_main_thread
    def update_flow_set_data(self, channel, flow):
        if channel == self.channel:
            self.set_label.SetLabel('Set: {:3.1f}%'.format(flow))


class Menubar(wx.MenuBar):
    def __init__(self, timer, _=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.port = None
        self.timer = timer

        filemenu = wx.Menu()
        filemenu.Append(item='Quit', id=wx.ID_CLOSE)

        self.rod_com_menu = PortMenu(timer=self.timer)

        self.Append(filemenu, 'File')
        self.Append(self.rod_com_menu, 'Serial Connection')


class PortMenu(wx.Menu):
    def __init__(self, timer):
        super().__init__()

        self.timer = timer

        self.portdict = {}
        self.portItems = []

        self.make_port_list()

        self.refresh = self.Append(id=wx.ID_ANY, item='Refresh')
        self.connect = self.Append(id=wx.ID_ANY, item='Connect', kind=wx.ITEM_CHECK)
        self.Bind(event=wx.EVT_MENU, handler=self.on_connect, source=self.connect)
        self.Bind(event=wx.EVT_MENU, handler=self.refresh_ports, source=self.refresh)

    def on_connect(self, source):
        if source.IsChecked():
            for item in self.portItems:
                if item.IsChecked():
                    sendMessage(topicName='GTE_connect', port=self.portdict[item.GetItemLabelText()])
                    source.Skip()

        else:
            self.timer.Stop()
            sendMessage(topicName='GTE_disconnect')

    def refresh_ports(self, *args):
        for item in self.GetMenuItems():
            if item in self.portItems:
                self.DestroyItem(item)

        self.make_port_list()

    def make_port_list(self):
        self.portdict = {port[1]: port[0] for port in comports()}
        self.portItems = [wx.MenuItem(parentMenu=self, id=wx.ID_ANY, text=port, kind=wx.ITEM_RADIO)
                          for port in list(self.portdict.keys())]

        for item in reversed(self.portItems):
            self.Insert(0, item)

