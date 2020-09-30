import wx
from gui.SetupTap import SetupTap
from gui.CalibrationTab import CalibrationTab
from gui.LiveViewTab import LiveViewTab
from gui.AboutTab import AboutTab
from logic.StreamHandler import StreamHandler
from logic.ClassificationManager import ClassificationManager
from logic.ConsoleStreamEventListener import ConsoleStreamEventListener


class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MainFrame, self).__init__(*args, **kw)
        self.panel = wx.Panel(self)
        self.notebook = wx.Notebook(self.panel)
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

        #initialize the streamhandler with a standard ClassificationManager
        self.streamHandler = StreamHandler(ClassificationManager())

        #tabs
        self.setupTab = SetupTap(self.notebook, self.streamHandler)
        self.calibrationTab = CalibrationTab(self.notebook, self.streamHandler)
        self.liveViewTab = LiveViewTab(self.notebook, self.streamHandler)
        self.aboutTab = AboutTab(self.notebook)

        self.notebook.AddPage(self.setupTab, "Setup")
        self.notebook.AddPage(self.calibrationTab, "Calibration")
        self.notebook.AddPage(self.liveViewTab, "Liveview")
        self.notebook.AddPage(self.aboutTab, "About")

        self.streamHandler.addStreamEventListeners([self.setupTab, self.calibrationTab, self.liveViewTab, ConsoleStreamEventListener()])

        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.notebook, 1, wx.EXPAND)
        self.panel.SetSizer(self.sizer)

        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('')

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        #save all data and stop all streams
        self.streamHandler.closeAll()
        #stop all views with running threads
        self.Destroy()


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame(None, title="EMBody Toolkit", size=(1000, 600))
    frame.Show()
    frame.Centre()
    app.MainLoop()


