import numpy as np
import scipy.signal as signal

def rms_convolution(a, window_size):
    '''
    calculates rms on an array using convolution
    adapted from https://stackoverflow.com/a/8260297
    :param a: array-like
    :param window_size: size of rms window
    :return: array-like of rms values (only valid -> len(a) - window_size))
    '''
    a2 = np.power(a, 2)
    window = np.ones(window_size)/float(window_size)
    temp = np.sqrt(np.convolve(a2, window, 'valid'))
    return temp

def addPairwiseRatios(df):
    '''
    calculate inplace pairwise ratios for each column in the given dataframe. Adds them to the passed dataframe.
    :param df: pandas dataframe, each column corresponds to one signal channel
    '''
    numberOfChannels = df.shape[1]
    for i in range(numberOfChannels):
        for j in range(i, numberOfChannels):
            if i != j:
                df['ratio_rms' + str(i) + '_' + str(j)] = df.iloc[:,i] / df.iloc[:,j]


def getAvgSamplingRateFromTimestamps(timestamps):
    '''
    estimates average sampling rate from timestamps
    :param timestamps: array-like of timestamps
    :return: average sampling rate
    '''
    return 1e3 / np.mean(np.diff(timestamps))


def butter_bandstop_filter(data, cutoff_low, cutoff_high, nyq_freq, order=3):
    sos = signal.butter(order, [cutoff_low / nyq_freq, cutoff_high / nyq_freq], btype='bandstop', output='sos')
    y = signal.sosfiltfilt(sos, data)
    return y

def butter_bandpass_filter(data, cutoff_low, cutoff_high, nyq_freq, order=3):
    sos = signal.butter(order, [cutoff_low / nyq_freq, cutoff_high / nyq_freq], btype='bandpass', output='sos')
    y = signal.sosfiltfilt(sos, data)
    return y

def apply_bandpass_filter(df, cutoff_low, cutoff_high, samplingRate):
    '''
    applies a bandpass filter (butterworth forward-backward digital filter using cascaded second-order sections, 3rd order). Works inplace.
    :param df: the pandas dataframe to filter (each column is considered a channel)
    :param cutoff_low: low cut-off frequency
    :param cutoff_high: high cut-off frequency
    :param samplingRate: sampling rate for the given signal
    '''
    numberOfChannels = df.shape[1]
    for channel in range(numberOfChannels):
        df.iloc[:, channel] = butter_bandpass_filter(df.iloc[:,channel], cutoff_low, cutoff_high, samplingRate * 0.5)

def apply_bandstop_filter(df, cutoff_low, cutoff_high, samplingRate):
    '''
    applies a bandstop filter (butterworth forward-backward digital filter using cascaded second-order sections, 3rd order). Works inplace.
    :param df: the pandas dataframe to filter (each column is considered a channel)
    :param cutoff_low: low cut-off frequency
    :param cutoff_high: high cut-off frequency
    :param samplingRate: sampling rate for the given signal
    '''
    numberOfChannels = df.shape[1]
    for channel in range(numberOfChannels):
        df.iloc[:, channel] = butter_bandstop_filter(df.iloc[:,channel], cutoff_low, cutoff_high, samplingRate * 0.5)

def filterRingBuffer(ringBuffer, activeChannels, samplingRate, filtered, rms):
    '''
    filters the current ringBuffer (cf. LiewView and LiveViewClassification)
    :param ringBuffer: current EMG data for display in LiveView; first dimension corresponds to channels
    :param activeChannels: the currently active channels; only those get filtered
    :param samplingRate: the estimated sampling rate
    :param filtered: whether to apply a filter
    :param rms: whether to apply RMS calculation (not used if filtered is not TRUE)
    :return: a copy of the given ringBuffer object, where every active channel has been filtered and/or rms calculated
    '''

    filteredRingBuffer = []
    for i in range(0, len(ringBuffer)):
        if i in activeChannels:
            if filtered:
                if rms:
                    filteredRingBuffer.append(rms_convolution(butter_bandstop_filter(
                        butter_bandpass_filter(ringBuffer[i], 2.0, min(100.0, samplingRate * 0.5 - 1.0),
                                               samplingRate * 0.5), 49.0, 51.0, samplingRate * 0.5), 20))
                else:
                    filteredRingBuffer.append(butter_bandstop_filter(
                        butter_bandpass_filter(ringBuffer[i], 2.0, min(100.0, samplingRate * 0.5 - 1.0),
                                               samplingRate * 0.5), 49.0, 51.0, samplingRate * 0.5))
            else:
                filteredRingBuffer.append(ringBuffer[i])
        else:
            filteredRingBuffer.append(ringBuffer[i])
    return filteredRingBuffer