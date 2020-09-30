import wx
from gui.StreamEventListener import StreamEventListener
from gui.StreamEventListener import StreamEvent
from wx.lib.intctrl import IntCtrl

class SetupTap(StreamEventListener):
    def __init__(self, parent, streamHandler):
        StreamEventListener.__init__(self, parent, streamHandler)
        self.initUI()

    def initUI(self):
        #IP address, port and test button
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st_ip = wx.StaticText(self, label="UDP IP:")
        hbox1.Add(st_ip, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.tc_ip = wx.TextCtrl(self)
        hbox1.Add(self.tc_ip, proportion=1)
        st_port = wx.StaticText(self, label="UDP Port:")
        hbox1.Add(st_port, flag=wx.RIGHT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.tc_port = IntCtrl(self, value=3333, min=1024, max=49151)
        hbox1.Add(self.tc_port, proportion=.5)
        self.vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        self.vbox.Add((-1, 10))
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        btn_testConn = wx.Button(self, label="Test Connection", size=(100, 30))
        hbox2.Add(btn_testConn)
        self.vbox.Add(hbox2, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        #sizer for the connection info
        self.vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.vbox2)

        self.Bind(wx.EVT_BUTTON, self.onTestConnection, btn_testConn)
        self.SetSizer(self.vbox)


    def onTestConnection(self, e):
        if self.tc_port.IsInBounds():
            try:
                self.streamHandler.testConnection(self.tc_ip.GetValue(), int(self.tc_port.GetValue()))
            except TypeError:
                dial = wx.MessageDialog(None, 'Wrong UDP Format! Please provide a valid IP address.',
                                        'Error', wx.OK | wx.ICON_ERROR)
                dial.ShowModal()
            except ValueError:
                dial = wx.MessageDialog(None, 'Wrong UDP Format! Please provide a valid IP address.',
                                        'Error', wx.OK | wx.ICON_ERROR)
                dial.ShowModal()
        else:
            dial = wx.MessageDialog(None, 'Wrong UDP Format! Please provide a value between 1024 and 49151.',
                                    'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()


    def updateConnectionInfo(self):

        #always delete old info first
        while len(self.vbox2.GetChildren()) > 0:
            self.vbox2.Hide(len(self.vbox2.GetChildren()) - 1)
            self.vbox2.Remove(len(self.vbox2.GetChildren())-1)

        if self.streamHandler.connectionInfo is None:
            return

        #we have connection info -> display it
        sb_conn = wx.StaticBox(self, label="Connection Information")
        boxsizer = wx.StaticBoxSizer(sb_conn, wx.VERTICAL)
        boxsizer.Add(wx.StaticText(self, label="Estimated Sampling rate: " + "{:.1f}".format(self.streamHandler.getEstimatedSamplingRate()) + "Hz"), flag=wx.LEFT|wx.TOP, border=5)
        boxsizer.Add(wx.StaticText(self, label="Number of Channels found: " + str(self.streamHandler.getNumberOfChannels())), flag=wx.LEFT|wx.TOP, border=5)
        self.vbox2.Add(boxsizer, flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT , border=10)

        #add channel selection
        self.vbox2.Add((-1, 10))
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st_chSelect = wx.StaticText(self, label="Select Channels to use:")
        self.vbox2.Add(st_chSelect, flag=wx.EXPAND|wx.LEFT, border=5)
        self.selectedChannels = []
        for i in range(self.streamHandler.getNumberOfChannels()):
            cb = wx.CheckBox(self, label="CH" + str(i+1))
            hbox1.Add(cb, flag=wx.RIGHT|wx.TOP|wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
            self.selectedChannels.append(cb)
            self.Bind(wx.EVT_CHECKBOX, self.onUpdateActiveChannels, cb)
        self.vbox2.Add(hbox1, flag=wx.EXPAND|wx.LEFT, border=5)

        #button to go to calibration and liveview tab
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        btn_calibrate = wx.Button(self, label="Calibrate", size=(100, 30))
        hbox2.Add(btn_calibrate, flag=wx.EXPAND|wx.LEFT, border=5)
        btn_liveView = wx.Button(self, label="Live View", size=(100, 30))
        hbox2.Add(btn_liveView, flag=wx.EXPAND|wx.LEFT, border=5)
        self.vbox2.Add(hbox2, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        self.Bind(wx.EVT_BUTTON, self.onStartCalibrateView, btn_calibrate)
        self.Bind(wx.EVT_BUTTON, self.onStartLiveView, btn_liveView)
        self.Layout()

    def onUpdateActiveChannels(self, e):
        activeChannels = []
        for i in range(len(self.selectedChannels)):
            if self.selectedChannels[i].IsChecked():
                activeChannels.append(i)
        self.streamHandler.setActiveChannels(activeChannels)

    def onStartCalibrateView(self, e):
        if not self.streamHandler.getActiveChannels():
            wx.MessageDialog(None, 'Please select at least one active channel to record!', 'Select active channels', wx.OK | wx.ICON_ERROR).ShowModal()
            return
        else:
            if self.streamHandler.getEstimatedSamplingRate() > 103.0 and self.streamHandler.getEstimatedSamplingRate() < 200.0:
                dlg = wx.MessageDialog(None, 'Low Sampling rate detected. Ensure > 200 Hz for best results. Do you want to continue?', 'Low sampling rate', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
                if dlg.ShowModal() == wx.ID_OK:
                    self.GetParent().SetSelection(1)
            elif self.streamHandler.getEstimatedSamplingRate() < 103.0:
                wx.MessageDialog(None, 'Insufficient sampling rate detected. Ensure at least > 103 Hz.', 'Insufficient sampling rate', wx.OK | wx.ICON_ERROR).ShowModal()
            else:
                self.GetParent().SetSelection(1)

    def onStartLiveView(self, e):
        self.streamHandler.startLiveView()
        self.GetParent().SetSelection(2)


    def onStreamEvent(self, streamEvent):
        '''
        Handles StreamEvents for this class. Mainly testing connections.
        '''
        if streamEvent == StreamEvent.TEST_CONNECTION_INITIALIZING:
            self.dlg2 = TimeoutDialog('Establishing Connection...', 'Connecting')

        elif streamEvent == StreamEvent.TEST_CONNECTION_INIT_FAILED_SERVER_UNREACHABLE:
            self.dlg2.Destroy()
            wx.MessageDialog(None, 'Could not establish connection! Check UDP address!\nYou might already be connected to that address, blocking access!', 'Error', wx.OK | wx.ICON_ERROR).ShowModal()
            self.updateConnectionInfo()

        elif streamEvent == StreamEvent.TEST_CONNECTION_STARTED:
            self.dlg2.Destroy()
            self.dlg = TimeoutDialog('Testing connection parameters. Closing in 5s...', 'Connection Test')
            wx.CallLater(5000, self.streamHandler.onTestConnectionTimeout)

        elif streamEvent == StreamEvent.TEST_CONNECTION_COMPLETE:
            self.dlg.Destroy()
            self.updateConnectionInfo()

        elif streamEvent == StreamEvent.TEST_CONNECTION_FAILED_SERVER_UNRESPONSIVE:
            self.dlg.Destroy()
            wx.MessageDialog(None, 'Server is not responding!', 'Error', wx.OK | wx.ICON_ERROR).ShowModal()
            self.updateConnectionInfo()


class TimeoutDialog(wx.Dialog):
    '''
    Simple timeout dialog used during testConnection
    '''
    def __init__(self, message, title):
        wx.Dialog.__init__(self, None, title=title, style=wx.CAPTION)
        self.text = wx.StaticText(self, label=message)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.text, flag=wx.ALIGN_CENTER|wx.ALL, border=20)
        self.SetSizer(self.vbox)
        self.Layout()
        self.Fit()
        self.Show()
