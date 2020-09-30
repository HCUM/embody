from gui.StreamEventListener import StreamEventListener
import time


class ConsoleStreamEventListener(StreamEventListener):
    '''
    Logger for StreamEvents via Console.
    '''

    def __init__(self):
        pass

    def onStreamEvent(self, streamEvent):
        print(str(time.ctime(time.time())) + "\t" + str(streamEvent))
