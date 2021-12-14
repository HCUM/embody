import wx
import matplotlib.pyplot as plt

from gui.StreamEventListener import StreamEventListener, StreamEvent
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import matplotlib.animation as animation

#standard layout for liveview
nrow = 2
ncol = 3
view_modes = ["Raw Signal", "Filtered Signal", "RMS of Signal"]
view_mode_axis = [(0, 4096), (-2000, 2000), (0, 2000)]

class LiveViewTab(StreamEventListener):
    def __init__(self, parent, streamHandler):
        StreamEventListener.__init__(self, parent, streamHandler)
        self.animator = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.currentViewMode = 0
        self.updateView()

    def updateView(self):
        '''
        Updates liveview, based on available elements, e.g. whether liveview is active
        '''
        #always delete old first
        while len(self.sizer.GetChildren()) > 0:
            self.sizer.Hide(len(self.sizer.GetChildren()) - 1)
            self.sizer.Remove(len(self.sizer.GetChildren())-1)

        if self.streamHandler.isLiveViewActive or self.streamHandler.isStreamingClassification:

            hbox1 = wx.BoxSizer(wx.HORIZONTAL)
            self.lsl_rms_stream = wx.CheckBox(self, label="Stream RMS data to LSL")

            self.viewModeChoice = wx.Choice(self, -1, choices = view_modes)
            self.viewModeChoice.SetSelection(self.currentViewMode)
            self.Bind(wx.EVT_CHOICE, self.onViewModeChanged, self.viewModeChoice)
            hbox1.Add(self.viewModeChoice, flag=wx.TOP | wx.LEFT, border=5)
            hbox1.Add(self.lsl_rms_stream, flag=wx.TOP | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=5)
            self.lsl_rms_stream.SetValue(self.streamHandler.isStreamingRMS)
            self.lsl_rms_stream.Bind(wx.EVT_CHECKBOX, self.onRmsStreamToggled)

            self.sizer.Add(hbox1)

            self.figure = plt.Figure()
            self.createGridConfiguration()

            self.figure.subplots_adjust(wspace=0.5, hspace= 0.5)
            self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
            self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            #add live prediction label
            boxsizer = wx.BoxSizer(wx.HORIZONTAL)
            st_text = wx.StaticText(self, label="Current Prediction: ")
            st_text.SetFont(wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.BOLD))
            boxsizer.Add(st_text, flag=wx.LEFT | wx.TOP, border=5)
            self.st_prediction = wx.StaticText(self, label="")
            self.st_prediction.SetFont(wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.BOLD))
            boxsizer.Add(self.st_prediction, flag=wx.EXPAND | wx.TOP | wx.LEFT, border=5)
            self.sizer.Add(boxsizer, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            #assign an animation to update plots
            self.animator = animation.FuncAnimation(self.figure, self.updatePlot, interval=100)

        else:
            self.sizer.Add(wx.StaticText(self, -1, "No active connection", (20, 20)), flag=wx.TOP | wx.LEFT, border=20)

        self.Layout()

    def createGridConfiguration(self):
        self.axArray = self.figure.subplots(2, 3)
        displayData = []
        if self.currentViewMode == 1: #filtered signal view
            displayData = self.streamHandler.getCurrentBuffer(filtered=True)
        elif self.currentViewMode == 2: #RMS values view
            displayData = self.streamHandler.getCurrentBuffer(filtered=True, rms=True)
        else: #default to normal view
            displayData = self.streamHandler.getCurrentBuffer()

        lengthXAxis = len(displayData[0])
        self.rawData = []
        # create a grid of subplots to show channels
        for i in range(0, nrow):
            for j in range(0, ncol):
                self.axArray[i, j].set_title(label="CH_" + str(i * ncol + j + 1))
                if i * ncol + j not in self.streamHandler.getActiveChannels():
                    self.axArray[i, j].set_facecolor('.9')
            [axis.axis([0, lengthXAxis, view_mode_axis[self.currentViewMode][0], view_mode_axis[self.currentViewMode][1]]) for axis in self.axArray[i, :]]
            [axis.set_xticks([]) for axis in self.axArray[i, :]]
            [self.rawData.append(axis.plot([], [])) for axis in self.axArray[i, :]]

    def updatePlot(self, a):
        '''
        Animation function to update data for plots
        '''
        currentData = []
        if self.currentViewMode == 1: #filtered signal view
            currentData = self.streamHandler.getCurrentBuffer(filtered=True)
        elif self.currentViewMode == 2: #RMS values view
            currentData = self.streamHandler.getCurrentBuffer(filtered=True, rms=True)
        else: #default to normal view
            currentData = self.streamHandler.getCurrentBuffer()

        if currentData is not None:
            for i in range(0, 6):
                if i in self.streamHandler.getActiveChannels():
                    self.rawData[i][0].set_data(range(len(currentData[i]) - 1, -1, -1), currentData[i])

        # filteredData = self.streamHandler.getCurrentBuffer(filtered=True)
        # if filteredData is not None:
        #     for i in range(0, 6):
        #         if i in self.streamHandler.getActiveChannels():
        #             self.rawData[i][0].set_data(range(len(filteredData[i]) - 1, -1, -1), filteredData[i])

        #also update live prediction if required
        if self.st_prediction is not None:
            if self.streamHandler.isStreamingClassification:
                prediction = self.streamHandler.getCurrentPrediction()
                if prediction is None:
                    self.st_prediction.SetLabel("No live classification available.")
                else:
                    self.st_prediction.SetLabel(prediction)
            else:
                self.st_prediction.SetLabel("No live classification available.")

    def onViewModeChanged(self, e):
        self.currentViewMode = self.viewModeChoice.GetSelection()
        #restart view
        self.onStreamEvent(StreamEvent.LIVE_VIEW_STOPPED)
        self.onStreamEvent(StreamEvent.LIVE_VIEW_STARTED)

    def onStreamEvent(self, streamEvent):
        '''
        Listen for StreamEvent for this class. Only interested in start/stop of liveview or live classification and whether the active channels have changed.
        '''
        if streamEvent == StreamEvent.LIVE_VIEW_STARTED or streamEvent == StreamEvent.LIVE_CLASSIFICATION_STARTED:
            self.updateView()
        if streamEvent == StreamEvent.LIVE_VIEW_STOPPED or streamEvent == StreamEvent.LIVE_CLASSIFICATION_STOPPED:
            if self.animator is not None:
                self.animator.event_source.stop()
                del self.animator
            if self.st_prediction is not None:
                self.st_prediction.SetLabel("No live classification available.")
        if streamEvent == StreamEvent.ACTIVE_CHANNELS_CHANGED:
            self.updateView()


    '''
    Convience method to send out an RMS Stream for LSL -> sends the current buffer; does not check for new samples; sampling rate of approx. 60Hz
    '''
    def onRmsStreamToggled(self, e):
        self.streamHandler.stopStreamingRMS()
        if self.lsl_rms_stream.IsChecked():
            self.streamHandler.startStreamingRMS()




