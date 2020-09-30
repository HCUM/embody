class ConnectionInfo:
    def __init__(self, udpIP, udpPort):

        self.udpIP = udpIP
        self.udpPort = udpPort
        self.estimatedSamplingRate = None
        self.numberOfChannels = None
        self.activeChannels = []

    def setEstimatedSamplingRate(self, estimatedSamplingRate):
        self.estimatedSamplingRate = estimatedSamplingRate

    def setNumberOfChannels(self, numberOfChannels):
        self.numberOfChannels = numberOfChannels