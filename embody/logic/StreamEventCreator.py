
class StreamEventCreator:
    '''
    Super class for every module that creates noteworthy stream events.
    '''

    def __init__(self):
        self.streamEventListeners = []

    def fireStreamEvent(self, streamEvent):
        [listener.onStreamEvent(streamEvent) for listener in self.streamEventListeners]


    def addStreamEventListeners(self, streamEventListeners):
        [self.streamEventListeners.append(listener) for listener in streamEventListeners]