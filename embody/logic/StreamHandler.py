from logic.ConnectionInfo import ConnectionInfo
import socket
import time
from threading import Thread
from gui.StreamEventListener import StreamEvent
from collections import deque
from logic.ClassificationManager import DataNotSynchronizedError, SamplingRateTooLowError, InsufficientDataRecordedError
from logic.StreamEventCreator import StreamEventCreator
import itertools
from logic.helpers import filterRingBuffer
from pylsl import StreamInfo, StreamOutlet
from random import randint
import numpy as np
import math


class StreamHandler(StreamEventCreator):
    '''
    Handles stream connections for EMBody. Most of the work is outsourced to custom Threads.
    '''
    def __init__(self, classificationManager):
        StreamEventCreator.__init__(self)
        self.connectionInfo = None
        self.connectionTestThread = None
        self.liveViewThread = None
        self.isStreamingClassification = False
        self.isStreamingRMS = False
        self.liveClassificationThread = None
        self.calibrationThread = None
        self.trainClassifierThread = None
        self.rmsStreamingThread = None
        self.isLiveViewActive = False
        self.classificationManager = classificationManager
        self.currentCalibrationLabel = (None, None)
        self.currentPrediction = None
        self.lsl_rand_int = str(randint(0,1000))

    def initializeStream(self, udpIP, udpPort):
        self.connectionInfo = ConnectionInfo(udpIP, udpPort)

    def updateConnectionInfo(self, connectionInfo):
        self.connectionInfo = connectionInfo

    def setActiveChannels(self, activeChannels):
        self.connectionInfo.activeChannels = activeChannels
        self.fireStreamEvent(StreamEvent.ACTIVE_CHANNELS_CHANGED)

    def getEstimatedSamplingRate(self):
        return self.connectionInfo.estimatedSamplingRate

    def getNumberOfChannels(self):
        return self.connectionInfo.numberOfChannels

    def getActiveChannels(self):
        return self.connectionInfo.activeChannels

    def getCurrentCalibrationLabel(self):
        if self.calibrationThread:
            return self.currentCalibrationLabel
        else:
            return None

    def getClassifierAccuracy(self):
        if self.classificationManager.clf_stats is not None:
            return self.classificationManager.clf_stats['accuracy']
        else:
            return None

    def getClassifierInfo(self):
        return self.classificationManager.clf_stats

    def getCurrentPrediction(self):
        return self.classificationManager.currentPrediction

    def setCurrentCalibrationLabel(self, calibrationLabel):
        self.currentCalibrationLabel = calibrationLabel

    def saveCalibrationData(self, pathname):
        self.classificationManager.saveCalibrationData(pathname)

    def startLiveClassificationThread(self, udp_port, usePyLSL):
        self.stopAllLiveViewConnections()
        self.isStreamingClassification = True
        self.liveClassificationThread = LiveClassificationThread(self.connectionInfo, self.classificationManager, udp_port, usePyLSL, self.lsl_rand_int)
        self.liveClassificationThread.start()
        self.fireStreamEvent(StreamEvent.LIVE_CLASSIFICATION_STARTED)

    def startLiveView(self):
        self.stopAllLiveViewConnections()
        self.isLiveViewActive = True
        self.liveViewThread = LiveViewThread(self.connectionInfo)
        self.liveViewThread.start()
        self.fireStreamEvent(StreamEvent.LIVE_VIEW_STARTED)


    def stopAllLiveViewConnections(self):
        self.stopLiveView()
        self.stopLiveClassification()

    def stopLiveClassification(self):
        if self.liveClassificationThread is not None:
            self.liveClassificationThread.running = False
            self.liveClassificationThread.join()
            self.isStreamingClassification = False
            self.liveClassificationThread = None
            self.fireStreamEvent(StreamEvent.LIVE_CLASSIFICATION_STOPPED)

    def stopLiveView(self):
        if self.liveViewThread is not None:
            self.liveViewThread.running = False
            self.liveViewThread.join()
            self.isLiveViewActive = False
            self.liveViewThread = None
            self.fireStreamEvent(StreamEvent.LIVE_VIEW_STOPPED)

    def testConnection(self, udpIP, udpPort):

        self.stopAllLiveViewConnections()
        self.fireStreamEvent(StreamEvent.TEST_CONNECTION_INITIALIZING)

        try:
            self.initializeStream(udpIP, udpPort)
            self.connectionTestThread = TestConnectionThread(self.connectionInfo)
        except OSError:
            self.connectionTestThread = None
            self.connectionInfo = None
            self.fireStreamEvent(StreamEvent.TEST_CONNECTION_INIT_FAILED_SERVER_UNREACHABLE)
            return

        self.connectionTestThread.start()
        self.fireStreamEvent(StreamEvent.TEST_CONNECTION_STARTED)

    def onTestConnectionTimeout(self):
        self.connectionTestThread.running = False
        self.connectionTestThread.join()
        self.updateConnectionInfo(self.connectionTestThread.connectionInfo)
        self.connectionTestThread = None
        if self.connectionInfo == None:
            self.fireStreamEvent(StreamEvent.TEST_CONNECTION_FAILED_SERVER_UNRESPONSIVE)
        else:
            self.fireStreamEvent(StreamEvent.TEST_CONNECTION_COMPLETE)

    def getCurrentBuffer(self, filtered=False, rms=False):
        if self.liveViewThread is not None:
            return filterRingBuffer(self.liveViewThread.ringBuffer, self.getActiveChannels(), self.connectionInfo.estimatedSamplingRate, filtered, rms)
        if self.liveClassificationThread is not None:
            return filterRingBuffer(self.liveClassificationThread.ringBuffer, self.getActiveChannels(), self.connectionInfo.estimatedSamplingRate, filtered, rms)
        else:
            return None

    def closeAll(self):
        if self.connectionTestThread is not None:
            self.connectionTestThread.running = False
            self.connectionTestThread.join()
            self.connectionTestThread = None
            self.fireStreamEvent(StreamEvent.TEST_CONNECTION_FAILED_ABORT)

        self.stopAllLiveViewConnections()

        if self.calibrationThread is not None:
            self.calibrationThread.running = False
            self.calibrationThread.join()
            self.calibrationThread = None
            self.fireStreamEvent(StreamEvent.CALIBRATION_FAILED_ABORT)

    def updateCalibrationLabel(self, labels):
        self.classificationManager.onCalibrationInitialized(labels)

    def getCalibrationStatus(self):
        return self.classificationManager.getCalibrationStatus()


    def onCalibrationComplete(self):
        self.calibrationThread.running = False
        self.calibrationThread.join()
        try:
            self.classificationManager.onRawCalibrationDataAvailable(self.calibrationThread.rawTimestamps, self.calibrationThread.rawData, self.calibrationThread.rawLabelData, self.calibrationThread.totalCalibrationDuration)
            self.fireStreamEvent(StreamEvent.CALIBRATION_COMPLETED)
        except DataNotSynchronizedError:
            self.fireStreamEvent(StreamEvent.CALIBRATION_FAILED_DATA_NOT_IN_SYNC)
            return
        except SamplingRateTooLowError:
            self.fireStreamEvent(StreamEvent.CALIBRATION_FAILED_SAMPLING_RATE_TOO_LOW)
            return
        except InsufficientDataRecordedError:
            self.fireStreamEvent(StreamEvent.CALIBRATION_FAILED_INSUFFICIENT_DATA)
            return
        finally:
            self.calibrationThread = None

    def startCalibration(self):
        self.stopAllLiveViewConnections()

        if self.connectionInfo is not None:
            if self.connectionInfo.activeChannels:
                self.calibrationThread = CalibrationThread(self.connectionInfo, self)
                self.calibrationThread.start()
                self.fireStreamEvent(StreamEvent.CALIBRATION_STARTED)
            else:
                self.fireStreamEvent(StreamEvent.CALIBRATION_FAILED_NO_ACTIVE_CHANNELS)
        else:
            self.fireStreamEvent(StreamEvent.CALIBRATION_FAILED_NO_CONNECTION)

    def startTrainingClassifier(self):
        self.trainClassifierThread = TrainClassifierThread(self)
        self.trainClassifierThread.start()
        self.fireStreamEvent(StreamEvent.TRAIN_CLASSIFIER_STARTED)

    def startLiveClassification(self, udp_port, usePyLSL = False):

        if self.classificationManager.clf is None:
            self.fireStreamEvent(StreamEvent.LIVE_CLASSIFICATION_NO_CLF)
            return
        if self.connectionInfo is None:
            self.fireStreamEvent(StreamEvent.LIVE_CLASSIFICATION_NO_CONNECTION)
            return
        if len(self.connectionInfo.activeChannels) != self.classificationManager.clf_stats['num_channels']:
            #this is just a sanity check -> actual id of channels is not checked!
            self.fireStreamEvent(StreamEvent.LIVE_CLASSIFICATION_NUM_CHANNEL_MISMATCH)
            return

        self.stopAllLiveViewConnections()
        self.startLiveClassificationThread(udp_port, usePyLSL)

    def startStreamingRMS(self):
        self.rmsStreamingThread = RMSStreamingThread(self, self.connectionInfo, self.lsl_rand_int)
        self.rmsStreamingThread.start()
        self.isStreamingRMS = True
        self.fireStreamEvent(StreamEvent.RMS_STREAM_STARTED)

    def stopStreamingRMS(self):
        if self.rmsStreamingThread is not None:
            self.rmsStreamingThread.running = False
            self.rmsStreamingThread.join()
            self.isStreamingRMS = False
            self.rmsStreamingThread = None
            self.fireStreamEvent(StreamEvent.RMS_STREAM_STOPPED)


class TrainClassifierThread(Thread):
    '''
    Background thread that performs calculations to train a classifier model. Fires TRAIN_CLASSIFIER_COMPLETED after completion.
    '''
    def __init__(self, streamHandler):
        Thread.__init__(self)
        self.streamHandler = streamHandler

    def run(self):
        self.streamHandler.classificationManager.trainClassifierModel()
        self.onTrainClassifierCompleted()

    def onTrainClassifierCompleted(self):
        self.streamHandler.fireStreamEvent(StreamEvent.TRAIN_CLASSIFIER_COMPLETED)


class CalibrationThread(Thread):
    '''
    Background thread that is active during calibration. Synchronized provided labels from CalibrationTab with received data. Is stopped via onCalibrationCompleted(), which is called from CalibrationTab, after it iterated through all calibration labels.
    '''
    def __init__(self, connectionInfo, streamHandler):
        Thread.__init__(self)
        self.streamHandler = streamHandler
        self.running = False
        self.totalCalibrationDuration = 0.0
        self.connectionInfo = connectionInfo
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.sock.settimeout(5)
        self.sock.bind((self.connectionInfo.udpIP, self.connectionInfo.udpPort))
        self.rawData = []
        [self.rawData.append([]) for channel in self.connectionInfo.activeChannels]
        self.rawTimestamps = []
        self.rawLabelData = []
        self.errorCodes = []

    def run(self):
        self.running = True
        startTime = time.time()
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                data = str(data.decode('utf-8')).split(';')
                self.rawTimestamps.append(int(data[0])) #assuming one timestamp channel
                #collect only data for active channels
                for i in range(0, len(self.connectionInfo.activeChannels)):
                    self.rawData[i].append(int(data[self.connectionInfo.activeChannels[i]+1]))
                #synchronized with current calibration label
                self.rawLabelData.append(self.streamHandler.getCurrentCalibrationLabel())
            except ValueError:
                self.errorCodes.append("Transmission Error")
            except socket.timeout:
                self.running = False
                self.errorCodes.append("Server Timeout")
        self.totalCalibrationDuration = time.time() - startTime
        self.sock.close()


class LiveViewThread(Thread):
    '''
    Background thread that is active during liveview. Receives data from the hardware prototype and populates a ringbuffer. LiveviewTab reads this buffer when active.
    '''
    def __init__(self, connectionInfo):
        Thread.__init__(self)
        self.running=False
        self.connectionInfo = connectionInfo
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.sock.settimeout(5)
        self.sock.bind((self.connectionInfo.udpIP, self.connectionInfo.udpPort))
        self.ringBuffer = [deque(int(self.connectionInfo.estimatedSamplingRate*10) * [0]) for i in range(0, self.connectionInfo.numberOfChannels)]

    def run(self):
        self.running = True
        while self.running:
            try:
                self.receiveData()
            except ValueError:
                print("TransmissionError")
            except socket.timeout:
                self.running = False
        self.sock.close()

    def receiveData(self):
        data, addr = self.sock.recvfrom(1024)
        data = str(data.decode('utf-8')).split(';')
        # assuming one timestamp channel
        [self.addSample(int(data[i + 1]), self.ringBuffer[i]) for i in range(0, self.connectionInfo.numberOfChannels)]

    def addSample(self, sample, data):
        data.pop()
        data.appendleft(sample)


class LiveClassificationThread(LiveViewThread):
    '''
    Background thread that is active during live classification. Extends LiveViewThread making used of its ringBuffer and receivce methods. Additionally implements live classification via ClassificationManager and sends out prediction via UDP.
    '''
    def __init__(self, connectionInfo, classificationManager, udp_port, usePyLSL, lsl_rand_int):
        LiveViewThread.__init__(self, connectionInfo)
        self.classificationManager = classificationManager
        self.usePyLSL = usePyLSL
        if not self.usePyLSL:
            self.udp_port = udp_port
            self.sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sendSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sendSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        else:
            info = StreamInfo('EMBody', 'Markers', 1, 0, 'string', 'EMBody-' + lsl_rand_int)
            self.outlet = StreamOutlet(info)


    def run(self):
        self.running = True
        classificationTimer = 0
        initializationTimer = self.classificationManager.windowSize*3
        while self.running:
            try:
                self.receiveData()
                if initializationTimer > 0:
                    #wait for buffer to fill
                    initializationTimer -= 1
                    continue

                classificationTimer += 1
                #predict every windowsSize samples
                if classificationTimer >= self.classificationManager.windowSize:
                    data = [list(itertools.islice(self.ringBuffer[i], 0, self.classificationManager.windowSize*3)) for i in self.connectionInfo.activeChannels]
                    prediction, _ = self.classificationManager.makePrediction(data)
                    classificationTimer = 0

                    if not self.usePyLSL:
                        self.sendSocket.sendto(bytes(str(prediction), "utf-8"), ("<broadcast>", self.udp_port))
                    else:
                        self.outlet.push_sample([str(prediction)])
            except socket.timeout:
                self.running = False

        if not self.usePyLSL:
            self.sendSocket.close()
        self.classificationManager.currentPrediction = None


class TestConnectionThread(Thread):
    '''
    Background thread that is active when testing a connection. Tries to connect to the given address for five seconds. Reports connection information if successful.
    '''
    def __init__(self, connectionInfo):
        Thread.__init__(self)
        self.running=False
        self.connectionInfo = connectionInfo
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.sock.settimeout(5)
        self.sock.bind((self.connectionInfo.udpIP, self.connectionInfo.udpPort))

    def run(self):
        self.running=True
        packetCounter=0
        startTime = time.time()
        numberOfChannels = -1
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                packetCounter +=1
                if numberOfChannels == -1:
                    numberOfChannels = len(str(data.decode('utf-8')).split(';'))-1 #assuming one timestamp channel
            except socket.timeout:
                self.running = False
                self.connectionInfo = None
        if self.connectionInfo is not None:
            self.connectionInfo.setEstimatedSamplingRate(packetCounter / (time.time()-startTime))
            self.connectionInfo.setNumberOfChannels(numberOfChannels)
        self.sock.close()


class RMSStreamingThread(Thread):
    '''
    Background thread that is active during if RMS streaming is toggled in live view;
    '''
    def __init__(self, streamHandler, connectionInfo, lsl_rand_int):
        Thread.__init__(self)
        self.rmsSamplingRate = 60.0
        self.slowRmsSamplingRate = 4.0
        #TODO: change to real buffer length and sampling rate
        info = StreamInfo('EMBody RMS zero latency', 'EMG RMS', 6, 60, 'double64', 'EMBody-rms-' + lsl_rand_int)
        info2 = StreamInfo('EMBody RMS aggegrated (250ms)', 'EMG RMS', 6, 60, 'double64', 'EMBody-rms-' + lsl_rand_int)
        self.outlet = StreamOutlet(info)
        self.outlet2 = StreamOutlet(info2)
        self.streamHandler = streamHandler
        self.freshSamples = math.floor(connectionInfo.estimatedSamplingRate / 60.0)
        self.aggregatedSamples = math.floor(connectionInfo.estimatedSamplingRate / 4.0)



    def run(self):
        self.running = True
        while self.running:
            if self.freshSamples >= 1:
                rmsBuffer = self.streamHandler.getCurrentBuffer(filtered=True, rms=True)
                #calculate "new" sample based on samplingRate and projected 60Hz streaming rate

                rmsSample = []
                rmsSample2 = []
                for channel in rmsBuffer:
                    avg_rms = np.mean(list(itertools.islice(channel, 0, self.freshSamples)))
                    avg_rms2 = np.mean(list(itertools.islice(channel, 0, self.aggregatedSamples)))
                    rmsSample.append(avg_rms)
                    rmsSample2.append(avg_rms2)
                self.outlet.push_sample(rmsSample)
                self.outlet2.push_sample(rmsSample2)
                time.sleep(0.0167)