from functools import partial

import wx
from serial.tools.list_ports import comports

from Ventolino import Ventolino


class VentolinoGUI(wx.Frame):
    def __init__(self, channels, engine=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.engine = engine
        self.channels = channels

        self.timer = wx.Timer(self)

        self.menu_bar = Menubar(style=wx.BORDER_NONE)
        self.SetMenuBar(self.menu_bar)

        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_CLOSE)

        panel = wx.Panel(parent=self)
        if channels == 1:
            sizer = wx.GridSizer(rows=1, cols=1, vgap=10, hgap=20)
        elif channels == 2:
            sizer = wx.GridSizer(rows=1, cols=2, vgap=10, hgap=20)
        else:
            sizer = wx.GridSizer(rows=2, cols=2, vgap=10, hgap=20)

        self.MFC = []
        for channel in range(channels):
            self.MFC.append(MFCChannelPanel(parent=panel, channel=channel + 1))
            sizer.Add(self.MFC[channel])

        panel.SetSizerAndFit(sizer)

        self.Show(True)

    def bind_to_engine(self, engine):
        if not self.engine:
            self.engine = engine

        self.menu_bar.rod_com_menu.binding(self.engine, self.timer)

        self.Bind(wx.EVT_TIMER, self.update, self.timer)

        for panel in self.MFC:
            panel.binding(self.engine)

    def on_quit(self, *args):
        self.Close()

    def update(self, *args):
        for chan in range(self.channels):
            self.engine.read_is_flow(channel=chan+1)
            self.MFC[chan].is_label.SetLabel('Flow: {:3.1f}%'.format(self.engine.is_flows[chan]))
            self.MFC[chan].gauge.SetValue(int(self.engine.is_flows[chan]))

            self.engine.read_set_flow(channel=chan+1)
            self.MFC[chan].set_label.SetLabel('Set: {:3.1f}%'.format(self.engine.set_flows[chan]))

        self.timer.Start(300)


class MFCChannelPanel(wx.Panel):
    def __init__(self, channel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.channel = channel

        self.set_button = wx.Button(parent=self, label='Set Flow')

        self.flow_control = wx.SpinCtrlDouble(parent=self, value='0', min=0, max=100, inc=0.1, style=wx.SP_ARROW_KEYS,
                                              size=(70, 20))

        self.is_label = wx.StaticText(parent=self, label='Flow:      ')
        self.set_label = wx.StaticText(parent=self, label='Set:      ')

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

    def set_flow_handler(self, *args, engine):
        flow_value = self.flow_control.GetValue()
        engine.set_flow(channel=self.channel, flow=flow_value)

    def binding(self, engine):
        self.Bind(wx.EVT_BUTTON, partial(self.set_flow_handler, engine=engine), source=self.set_button)


class Menubar(wx.MenuBar):
    def __init__(self, _=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.port = None

        filemenu = wx.Menu()
        filemenu.Append(item='Quit', id=wx.ID_CLOSE)

        self.rod_com_menu = PortMenu()

        self.Append(filemenu, 'File')
        self.Append(self.rod_com_menu, 'Serial Connection')


class PortMenu(wx.Menu):
    def __init__(self):
        super().__init__()

        self.selected_port = None

        self.portdict = self.port_dict = {port[1]: port[0] for port in comports()}
        self.portItems = [wx.MenuItem(parentMenu=self, id=wx.ID_ANY, text=port, kind=wx.ITEM_RADIO)
                          for port in list(self.port_dict.keys())]

        for item in self.portItems:
            self.Append(item)

        self.AppendSeparator()

        self.connect = self.Append(id=wx.ID_ANY, item='Connect', kind=wx.ITEM_CHECK)

    def binding(self, engine, timer):
        self.Bind(event=wx.EVT_MENU, handler=partial(self.connect_handler, engine=engine, timer=timer), source=self.connect)

    def connect_handler(self, source, engine, timer):
        if source.IsChecked():
            for item in self.portItems:
                if item.IsChecked():
                    engine.connect(self.port_dict[item.GetText()])
                    timer.Start()

        else:
            timer.Stop()
            engine.disconnect()




def main():
    ex = wx.App()
    eng = Ventolino()
    g = VentolinoGUI(parent=None, channels=2)
    g.bind_to_engine(engine=eng)
    ex.MainLoop()


if __name__ == '__main__':
    main()
