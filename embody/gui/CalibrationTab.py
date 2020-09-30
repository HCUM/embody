import wx
import wx.grid
from gui.StreamEventListener import StreamEventListener, StreamEvent
from wx.lib.intctrl import IntCtrl

headers = ["Label", "CALIB"]
NULL_CLASS_LABEL = "NULL_CLASS"

class CalibrationTab(StreamEventListener):
    def __init__(self, parent, streamHandler):
        StreamEventListener.__init__(self, parent, streamHandler)
        self.initUI()

    def initUI(self):
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)

        #calibration label panel
        self.vbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        markersText = wx.StaticText(self, wx.ID_ANY, "Calibration Labels")
        btn_loadCalibrationLabels = wx.BitmapButton(self, bitmap=wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, client=wx.ART_BUTTON))
        btn_loadCalibrationLabels.SetToolTip(wx.ToolTip("Load calibration labels from file"))
        btn_loadCalibrationLabels.Bind(wx.EVT_BUTTON, self.onLoadCalibrationLabels)
        btn_saveCalibrationLabels = wx.BitmapButton(self, bitmap=wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, client=wx.ART_BUTTON))
        btn_saveCalibrationLabels.SetToolTip(wx.ToolTip("Save calibration labels to file"))
        btn_saveCalibrationLabels.Bind(wx.EVT_BUTTON, self.onSaveCalibrationLabels)
        hbox2.Add(markersText, flag= wx.EXPAND | wx.ALL, border=5, proportion=1)
        hbox2.Add(btn_loadCalibrationLabels, flag=wx.LEFT, border=5)
        hbox2.Add(btn_saveCalibrationLabels, flag=wx.LEFT, border=5)
        self.vbox1.Add(hbox2)
        self.labelsInput = wx.TextCtrl(self, size=(200, 100), style=wx.TE_MULTILINE)
        self.vbox1.Add(self.labelsInput, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        btn_generateCalibrationLabels = wx.Button(self, label="Create Calibration")
        btn_generateCalibrationLabels.Bind(wx.EVT_BUTTON, self.onGenerateCalibrationLabels)


        # force horizontal layout and seperate from calibration data panel
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(btn_generateCalibrationLabels, border= 5)
        self.vbox1.Add(hbox1, flag=wx.ALIGN_LEFT | wx.LEFT, border=5)
        self.hbox.Add(self.vbox1, flag= wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, border=5, proportion=1)
        self.hbox.Add(20, -1)
        self.hbox.Add(wx.StaticLine(self, -1, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        self.hbox.Add(20, -1)


        #calibration data panel (initial state)
        self.vbox2 = wx.BoxSizer(wx.VERTICAL)
        st = wx.StaticText(self, -1, "No active calibration", (20,20))
        self.vbox2.Add(st)
        self.hbox.Add(self.vbox2, flag= wx.LEFT| wx.TOP | wx.EXPAND, border=5, proportion=1)
        self.SetSizer(self.hbox)
        self.Layout()

    def onGenerateCalibrationLabels(self, e):
        '''
        Called everytime the calibration labels change or new calibration data is available. Updates the right-hand side panel of calibration accordingly.
        '''
        #check whether we have labels
        hasTextInput = 0
        for i in range(0, self.labelsInput.GetNumberOfLines()):
            hasTextInput += len(self.labelsInput.GetLineText(i).strip())
        if hasTextInput == 0:
            wx.MessageDialog(None, 'You need to provide at least one calibration label!', 'Calibration impossible',
                             wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()
            return

        #remove all previous buttons or other elements
        while len(self.vbox2.GetChildren()) > 0:
            self.vbox2.Hide(len(self.vbox2.GetChildren()) - 1)
            self.vbox2.Remove(len(self.vbox2.GetChildren())-1)

        #create a new grid for calibration data
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0,len(headers))
        self.grid.SetColSize(0, 200)
        self.grid.HideRowLabels()
        self.grid.EnableEditing(False)
        for i in range(0, len(headers)):
            self.grid.SetColLabelValue(i, headers[i])

        #setup button and classifier info
        btn_exportCalibration = wx.BitmapButton(self, bitmap=wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, client=wx.ART_BUTTON))
        btn_exportCalibration.SetToolTip(wx.ToolTip("Export calibration data as csv"))
        btn_exportCalibration.Bind(wx.EVT_BUTTON, self.onExportCalibrationData)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.grid, flag=wx.EXPAND|wx.ALL, border=5, proportion=1)
        hbox1.Add(btn_exportCalibration, flag=wx.LEFT, border=5)
        self.vbox2.Add(hbox1, flag=wx.EXPAND|wx.ALL, border=5, proportion=1)
        sb_conn = wx.StaticBox(self, label="Current Prediction Model")
        boxsizer = wx.StaticBoxSizer(sb_conn, wx.VERTICAL)
        self.st_classifierInfo = wx.StaticText(self, label="No Model trained.")
        boxsizer.Add(self.st_classifierInfo, flag=wx.ALL|wx.EXPAND, border=10)
        self.vbox2.Add(boxsizer, flag= wx.LEFT | wx.BOTTOM, border=5)

        #live classification
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_toggleLiveClassification = wx.Button(self, label="Start Live Classification")
        self.btn_toggleLiveClassification.Bind(wx.EVT_BUTTON, self.onLiveClassificationToggled)
        hbox1.Add(self.btn_toggleLiveClassification, flag= wx.LEFT | wx.BOTTOM, border=5)
        self.st_port = wx.StaticText(self, label="UDP Port:")
        hbox1.Add(self.st_port, flag= wx.LEFT | wx.RIGHT| wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, border=5)
        self.tc_port = IntCtrl(self, value=3334, min=1024, max=49151)
        hbox1.Add(self.tc_port, proportion=.2)
        self.lsl_checkmark = wx.CheckBox(self, label="Use PyLSL")
        hbox1.Add(self.lsl_checkmark, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.vbox2.Add(hbox1, flag= wx.LEFT | wx.BOTTOM, border=5)
        self.vbox2.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        self.vbox2.Add((-1, 10))

        #train classifier, start calibration buttons
        self.btn_trainClassifier = wx.Button(self, label="Train Classifier")
        self.btn_trainClassifier.Bind(wx.EVT_BUTTON, self.onTrainClassifier)
        self.btn_trainClassifier.Disable()
        btn_startCalibration = wx.Button(self, label="Start Complete Calibration")
        btn_startCalibration.Bind(wx.EVT_BUTTON, self.onStartCalibration)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(btn_startCalibration, border= 5)
        hbox1.Add(self.btn_trainClassifier, border= 5)
        self.vbox2.Add(hbox1, flag= wx.LEFT | wx.BOTTOM, border=5)

        #update the grid with actual calibration data values; also updates button states
        self.updateGridLabels()

        self.Layout()


    def updateGridLabels(self):
        labels = [NULL_CLASS_LABEL]
        for i in range(0, self.labelsInput.GetNumberOfLines()):
            if self.labelsInput.GetLineText(i).strip():
                labels.append(self.labelsInput.GetLineText(i).strip())
        self.streamHandler.updateCalibrationLabel(labels)
        self.updateCalibrationGrid()


    def updateCalibrationGrid(self):
        self.grid.ClearGrid()
        while self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows()

        activateTrainClassifierButton = True

        for label, data in self.streamHandler.getCalibrationStatus().items():
            self.grid.InsertRows()
            self.grid.SetCellValue(0, 0, label)
            if data is None:
                self.grid.SetCellValue(0, 1, "X")
                activateTrainClassifierButton = False
            else:
                self.grid.SetCellValue(0, 1, "{:.1f}".format(data))

        self.btn_trainClassifier.Enable(activateTrainClassifierButton)
        self.updateClassifierInfo()


    def updateClassifierInfo(self):
        if self.streamHandler.getClassifierInfo() is not None:
            self.st_classifierInfo.SetLabel("Classes: " + ", ".join(self.streamHandler.getClassifierInfo()['classes']) + "\n"
                                            + "Accuracy (10-fold CV): " + "{:.1f}".format(self.streamHandler.getClassifierInfo()['accuracy']) + " %" + "\n"
                                            + "# of Channels: " + str(self.streamHandler.getClassifierInfo()['num_channels']))
            self.toggleLiveClassificationState(True)
        else:
            self.st_classifierInfo.SetLabel("No Model trained.")
            self.toggleLiveClassificationState(False)
        self.Layout()

    def toggleLiveClassificationState(self, state):
        self.btn_toggleLiveClassification.Enable(state)
        self.st_port.Enable(state)
        self.tc_port.Enable(state)
        self.lsl_checkmark.Enable(state)


    def onExportCalibrationData(self, e):
        with wx.FileDialog(self, "Export calibration data",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                self.streamHandler.saveCalibrationData(pathname)
            except IOError:
                wx.MessageDialog(None, "Cannot save file '%s'." % pathname,
                                 'Cannot save file', wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()
        wx.MessageDialog(None, 'Calibration data successfully exported.', 'Export complete',
                         wx.ICON_INFORMATION | wx.OK | wx.CENTRE).ShowModal()

    def onLoadCalibrationLabels(self, e):
        with wx.FileDialog(self, "Load calibration labels",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                self.labelsInput.LoadFile(pathname)
            except IOError:
                wx.MessageDialog(None, "Cannot open file '%s'." % pathname,
                                 'Cannot open file', wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

    def onSaveCalibrationLabels(self, e):
        with wx.FileDialog(self, "Save calibration labels",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                self.labelsInput.SaveFile(pathname)
            except IOError:
                wx.MessageDialog(None, "Cannot save file '%s'." % pathname,
                                 'Cannot save file', wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()
        wx.MessageDialog(None, 'Calibration labels successfully saved.', 'Save complete',
                         wx.ICON_INFORMATION | wx.OK | wx.CENTRE).ShowModal()


    def onLiveClassificationToggled(self, e):
        if not self.streamHandler.isStreamingClassification:
            if self.lsl_checkmark.IsChecked():
                #use pylsl to stream
                self.streamHandler.startLiveClassification(3334, usePyLSL=True)
            elif self.tc_port.IsInBounds():
                try:
                    udp_port = int(self.tc_port.GetValue())
                    if udp_port == self.streamHandler.connectionInfo.udpPort:
                        dial = wx.MessageDialog(None,
                                                'You cannot specify the same UDP port that EMBody uses to listen for EMG signals.',
                                                'Error', wx.OK | wx.ICON_ERROR)
                        dial.ShowModal()
                    else:
                        self.streamHandler.startLiveClassification(udp_port)
                except TypeError:
                    dial = wx.MessageDialog(None, 'Wrong UDP Format! Please provide a value between 1024 and 49151.', 'Error', wx.OK | wx.ICON_ERROR)
                    dial.ShowModal()
                except ValueError:
                    dial = wx.MessageDialog(None, 'Wrong UDP Format! Please provide a value between 1024 and 49151.', 'Error', wx.OK | wx.ICON_ERROR)
                    dial.ShowModal()
            else:
                dial = wx.MessageDialog(None, 'Wrong UDP Format! Please provide a value between 1024 and 49151.',
                                        'Error', wx.OK | wx.ICON_ERROR)
                dial.ShowModal()
        else:
            self.streamHandler.stopLiveClassification()


    def onTrainClassifier(self, e):
        if len(self.streamHandler.getCalibrationStatus().keys()) < 2:
            wx.MessageDialog(None, 'You need to provide at least two calibrated classes!', 'Not enough classes', wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()
            return

        self.trainClassifierDialog = wx.MessageDialog(None, 'Train classification model in background? This might take a while.', 'Build model?', wx.OK | wx.ICON_INFORMATION | wx.CANCEL | wx.CENTRE)
        if self.trainClassifierDialog.ShowModal() == wx.ID_CANCEL:
            return
        else:
            self.streamHandler.startTrainingClassifier()
            self.GetTopLevelParent().statusbar.SetStatusText("Training classifier model...")


    def onStartCalibration(self, e):
        dlg = wx.MessageDialog(None, 'During the calibration process you will be asked to perform '
                                     'gesture/motion input corresponding to the labels specified by you.\n\n'
                                     'Each label will be recorded for 5 seconds following a 3 second period for preparation. '
                                     'Note that the "NULL_CLASS" will be recorded additionally after each label, following the same process.\n\n'
                                     'The labels specified are:\n' + str(list(self.streamHandler.getCalibrationStatus())), 'Calibration explanation', wx.OK | wx.ICON_INFORMATION | wx.CANCEL | wx.CENTRE)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        self.streamHandler.startCalibration()


    def onCompleteCalibration(self):
        wx.MessageDialog(None, 'Calibration successful', 'Calibration', wx.OK | wx.ICON_INFORMATION | wx.CENTRE).Show()
        self.updateCalibrationGrid()


    def onStreamEvent(self, streamEvent):
        '''
        Handles StreamEvents for this class. Listens for calibration and classification related messages.
        '''
        if streamEvent == StreamEvent.CALIBRATION_FAILED_NO_CONNECTION:
            wx.MessageDialog(None, 'Please specify connection info before calibration.', 'No connection',
                             wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

        if streamEvent == StreamEvent.CALIBRATION_FAILED_NO_ACTIVE_CHANNELS:
            wx.MessageDialog(None, 'Please specify active channels you want to calibrate for in Setup.', 'No active channels',
                             wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

        if streamEvent == StreamEvent.CALIBRATION_FAILED_DATA_NOT_IN_SYNC:
            if self.calibrationDialog is not None:
                self.calibrationDialog.Destroy()
            wx.MessageDialog(None, 'Recorded data does not match synchronized labels. Most likely cause of this is an unstable connection.', 'Calibration failed',
                             wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

        if streamEvent == StreamEvent.CALIBRATION_FAILED_SAMPLING_RATE_TOO_LOW:
            if self.calibrationDialog is not None:
                self.calibrationDialog.Destroy()
            wx.MessageDialog(None, 'Average sampling rate during the recording was too low (less than 103 Hz). Most likely cause of this is an unstable connection.', 'Calibration failed',
                             wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

        if streamEvent == StreamEvent.CALIBRATION_FAILED_INSUFFICIENT_DATA:
            if self.calibrationDialog is not None:
                self.calibrationDialog.Destroy()
            wx.MessageDialog(None, 'Data samples recorded do not match the calculated sampling rate. Most likely cause of this is an unstable connection, dropping packages.', 'Calibration failed',
                             wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

        if streamEvent == streamEvent.CALIBRATION_STARTED:
            self.calibrationDialog = CompleteCalibrationDialog(self.streamHandler, list(self.streamHandler.getCalibrationStatus()), 3, 5)

        if streamEvent == StreamEvent.CALIBRATION_COMPLETED:
            self.calibrationDialog.Destroy()
            wx.MessageDialog(None, 'Calibration successful.', 'Calibration', wx.OK | wx.ICON_INFORMATION | wx.CENTRE).Show()
            self.updateCalibrationGrid()

        if streamEvent == StreamEvent.CALIBRATION_FAILED_ABORT:
            self.calibrationDialog.Destroy()

        if streamEvent == StreamEvent.TRAIN_CLASSIFIER_CANCELLED:
            if self.trainClassifierDialog is not None:
                self.trainClassifierDialog.Destroy()
            self.GetTopLevelParent().statusbar.SetStatusText("")

        if streamEvent == StreamEvent.TRAIN_CLASSIFIER_COMPLETED:
            if self.trainClassifierDialog is not None:
                self.trainClassifierDialog.Destroy()
            self.GetTopLevelParent().statusbar.SetStatusText("")
            tmp = self.streamHandler.getClassifierInfo
            wx.MessageDialog(None, 'Training classification model completed. Showing averaged metrics for 10-fold CV:\n'
                                   'Accuracy: ' + "{:.1f}".format(self.streamHandler.getClassifierAccuracy()) + "%\n"
                                    "Balanced Acc.: " + "{:.1f}".format(self.streamHandler.getClassifierInfo()['balanced_accuracy']) + "%\n"
                                    "F1 weighted: " + "{:.1f}".format(self.streamHandler.getClassifierInfo()['f1_weighted']) + "%\n"
                                    "Precision weighted: " + "{:.1f}".format(self.streamHandler.getClassifierInfo()['precision_weighted']) + "%\n"
                                    "Recall weighted: " + "{:.1f}".format(self.streamHandler.getClassifierInfo()['recall_weighted']) + "%", 'Building model completed',
                             wx.ICON_INFORMATION | wx.OK | wx.CENTRE).ShowModal()
            self.updateClassifierInfo()

        if streamEvent == StreamEvent.LIVE_CLASSIFICATION_NO_CLF:
            wx.MessageDialog(None, 'No Classifier available for prediction. Try re-calibrating and re-learning.', 'No Model available', wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

        if streamEvent == StreamEvent.LIVE_CLASSIFICATION_NO_CONNECTION:
            wx.MessageDialog(None, 'No Connection available. Check Setup tab.', 'No Connection', wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

        if streamEvent == StreamEvent.LIVE_CLASSIFICATION_NUM_CHANNEL_MISMATCH:
            wx.MessageDialog(None, 'Number of input channels does not match learned classifier. Most likely channel count was altered after training the classifier. Try re-calibrating and re-learning.', 'Input channel mismatch', wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

        if streamEvent == StreamEvent.LIVE_CLASSIFICATION_STARTED:
            self.GetTopLevelParent().statusbar.SetStatusText("Streaming live classification...")
            self.btn_toggleLiveClassification.SetLabel("Stop live classification")
            self.st_port.Enable(False)
            self.tc_port.Enable(False)
            self.lsl_checkmark.Enable(False)
            self.GetParent().SetSelection(2)

        if streamEvent == StreamEvent.LIVE_CLASSIFICATION_STOPPED:
            self.GetTopLevelParent().statusbar.SetStatusText("")
            self.btn_toggleLiveClassification.SetLabel("Start live classification")
            self.st_port.Enable(True)
            self.tc_port.Enable(True)
            self.lsl_checkmark.Enable(True)


class CompleteCalibrationDialog(wx.Dialog):
    '''
    Wizard that guides the user through the calibration. Displays windows for calibration labels in turns and informs the StreamHandler about changes. Note that the StreamHandler takes care of data synchronization (set/getCurrentCalibrationLabel())
    '''
    def __init__(self, streamHandler, gestureLabels, preparationTime, recordingTime):
        wx.Dialog.__init__(self, None, style=wx.CAPTION)
        self.streamHandler = streamHandler
        self.gestureLabels = []
        nullClassGroupIndex = 0
        for label in gestureLabels:
            # add a NONE class in between every other label
            if label is not NULL_CLASS_LABEL:
                self.gestureLabels.append((label, str(0)))
                self.gestureLabels.append((NULL_CLASS_LABEL, str(nullClassGroupIndex)))
                nullClassGroupIndex+=1
        self.labelIndex = 0
        self.preparationTime = preparationTime
        self.recordingTime = recordingTime
        self.finishTimer = 3
        self.SetTitle("Calibrating...")
        self.text = wx.StaticText(self)
        font = wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.text.SetFont(font)
        self.countdown = wx.StaticText(self)
        font = wx.Font(40, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.countdown.SetFont(font)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.text, flag=wx.ALIGN_CENTER | wx.ALL, border=20)
        self.vbox.Add(self.countdown, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=20)
        self.SetSizer(self.vbox)
        self.SetMinSize(wx.Size(700, 300))
        self.Layout()
        self.Fit()
        self.Centre()
        self.Show()

        self.streamHandler.setCurrentCalibrationLabel((None, None))
        self.startCalibrationRun()

    def startCalibrationRun(self):
        self.preparationTimeCounter = self.preparationTime
        self.recordingTimeCounter = self.recordingTime
        self.updateCountdown()


    def onCalibrationRunReturn(self):
        if self.labelIndex < len(self.gestureLabels)-1:
            self.labelIndex+=1
            self.startCalibrationRun()
        else:
            #all labels considered -> return
            self.finishCalibration()


    def finishCalibration(self):

        if self.finishTimer > 0:
            self.text.SetLabel("Finishing up calibration...")
            self.text.SetForegroundColour((0,0,0))
            self.countdown.SetLabel(str(self.finishTimer))
            self.countdown.SetForegroundColour((0, 0, 0))
            self.finishTimer -= 1
            self.Layout()
            self.Fit()
            wx.CallLater(1000, self.finishCalibration)
            return
        self.streamHandler.onCalibrationComplete()

    def updateCountdown(self):

        if self.preparationTimeCounter > 0:
            self.text.SetLabel("Prepare for " + str(self.gestureLabels[self.labelIndex][0]) + " in ...")
            self.text.SetForegroundColour((0,0,0))
            self.countdown.SetLabel(str(self.preparationTimeCounter))
            self.countdown.SetForegroundColour((0, 0, 0))
            self.preparationTimeCounter -= 1
            self.Layout()
            self.Fit()
            wx.CallLater(1000, self.updateCountdown)
            return

        if self.recordingTimeCounter > 0:
            self.streamHandler.setCurrentCalibrationLabel(self.gestureLabels[self.labelIndex])
            self.text.SetLabel("Calibrating for " + str(self.gestureLabels[self.labelIndex][0]))
            self.text.SetForegroundColour((255,0,0))
            self.countdown.SetLabel(str(self.recordingTimeCounter))
            self.countdown.SetForegroundColour((255, 0, 0))
            self.recordingTimeCounter -= 1
            self.Layout()
            self.Fit()
            wx.CallLater(1000, self.updateCountdown)
            return
        self.streamHandler.setCurrentCalibrationLabel((None, None))
        self.onCalibrationRunReturn()
