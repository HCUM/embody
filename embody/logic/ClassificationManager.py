from logic.helpers import *
import pandas as pd
from sklearn import svm, preprocessing
from scipy.stats import mode
from sklearn.model_selection import cross_validate

CLASS_LABEL = "class_label"
TIMESTAMP = "timestamp"
GROUP_INDEX = "group_index"

class ClassificationManager:
    def __init__(self, windowSize=20):
        self.calibrationData = pd.DataFrame()
        self.calibrationLabels = []
        self.mlData = None
        self.clf = None
        self.scaler = None
        self.clf_stats = None
        self.currentSamplingRate = None
        self.windowSize = windowSize
        self.currentPrediction = None


    def makePrediction(self, data):
        """
        Uses the internally trained model (cf. trainClassifierModel) to predict classes for the given data. Return 'None' is not classifier is present.
        Executes a prediction for each EMG data sample (i.e. each row in data) and returns both a list of predictions and a voted (mode-based) final prediction.

        Note that a prediction is only possible when the window (cf. windowsize) completely overlaps with the data. Hence, the number of predictions is len(data) - windowsize.
        Accordingly, the first prediction corresponds to the element data[:][windowsize/2].

        Parameters:
        data: 2D-array containing recorded EMG data samples (rows) per channel (columns).

        returns:
        currentPrediction: voted (mode-based) prediction for the given data
        prediction: list of predictions for valid window configurations; length = len(data) - windowsize
        """

        if self.clf is None:
            return 'None'

        df = pd.DataFrame(data)
        df = df.transpose()

        apply_bandpass_filter(df, 2.0, self.currentSamplingRate / 2.0 - 1.0, self.currentSamplingRate)
        apply_bandstop_filter(df, 49.0, 51.0, self.currentSamplingRate)

        X = pd.DataFrame()
        for column in df.columns:
            X['rms' + str(column)] = rms_convolution(df[column], self.windowSize)
        addPairwiseRatios(X)

        try:
            X = self.scaler.transform(X[X.columns])
            prediction = self.clf.predict(X)
            voted_prediction = mode(prediction)[0][0]
            self.currentPrediction = str(voted_prediction)
            return self.currentPrediction, prediction
        except ValueError:
            self.currentPrediction = None
            return None, []

    def saveCalibrationData(self, pathname):
        if self.calibrationData is None:
            self.calibrationData = pd.DataFrame()
        self.calibrationData.to_csv(pathname + ".csv", index=False, na_rep="None")

    def getCalibrationStatus(self, deleteCalibrationForUnusedLabels = True):
        calibrationStatus = {}
        for label in self.calibrationLabels:
            calibrationStatus[label] = None
        if not self.calibrationData.empty:
            toBeDeleted = []
            for name, group in self.calibrationData.groupby(CLASS_LABEL):
                if name in self.calibrationLabels:
                    calibrationStatus[name] = len(group.index)/self.currentSamplingRate
                else:
                    toBeDeleted.append(name)

            if deleteCalibrationForUnusedLabels:
                self.calibrationData = self.calibrationData[self.calibrationData[CLASS_LABEL].map(lambda x: x not in toBeDeleted)]

        return calibrationStatus


    def onCalibrationInitialized(self, calibrationLabels):
        self.calibrationLabels = calibrationLabels

    def onRawCalibrationDataAvailable(self, rawTimestamps, rawData, synchronizedLabels, totalCalibrationDuration):
        """
        Populates an internal data structure that can be used for training a classification model.

        Parameters:
        rawTimestamps: list of timestamps of the recorded EMG data (same length of column axis as rawData)
        rawData: 2D-array containing recorded EMG data samples (rows) per channel (columns).
        synchronizedLabels: list of calibration labels; each entry corresponds to the respective entry in rawData (same length of column axis as rawData)
        totalCalibrationDuration: time spent during calibration; used to check amount of sample recevied

        """
        if len(rawData[0]) == len(rawTimestamps) and len(rawTimestamps) == len(synchronizedLabels):
            samplingRate = getAvgSamplingRateFromTimestamps(rawTimestamps)
            self.currentSamplingRate = samplingRate
            expectedSamples = self.currentSamplingRate*totalCalibrationDuration
            if len(rawData[0]) >= 0.9*expectedSamples and len(rawData[0]) <= 1.1*expectedSamples:
                #expected samples is within 10% deviation; given samplingRate
                self.calibrationData = self.preprocessData(rawTimestamps, rawData, samplingRate, synchronizedLabels)
            else:
                raise InsufficientDataRecordedError()
        else:
            raise DataNotSynchronizedError()


    def trainClassifierModel(self):
        """
        Generates RMS (root mean square) features and their channel-wise pair-wise ratios and trains an SVM model.
        Note that onRawCalibrationDataAvailable populates the internal data structure used by this method.

        RMS features are calculated using a convolution approach and a window size specified by this class (defaults to 20).

        Implements a support vector classification using standard parameters from sklearn. Includes a standard scaler (unit variance, zero mean).
        Evaluates the trained model after training (10-fold CV).

        returns:
        clf_stats: python dict reporting on the trained model, including "accuracy", "classes" and "num_channels".
        Additionally provides sklearn prediction results, such as "test_score" per fold.

        """
        self.mlData = pd.DataFrame()
        grouped = self.calibrationData.groupby([CLASS_LABEL, GROUP_INDEX])
        for name, group in grouped:
            featuresForGroup = pd.DataFrame()
            numChannels = 0
            for column in list(group):
                if column.startswith("EMG"):
                    featuresForGroup['rms' + str(column)] = rms_convolution(group[column], self.windowSize)
                    numChannels+=1
            addPairwiseRatios(featuresForGroup)
            featuresForGroup[CLASS_LABEL] = name[0] #add class label
            self.mlData = self.mlData.append(featuresForGroup, ignore_index=True)

        self.clf = svm.SVC(gamma='scale')
        X = self.mlData.loc[:, self.mlData.columns != CLASS_LABEL]
        self.scaler = preprocessing.StandardScaler(copy=False)
        X = self.scaler.fit_transform(X)
        y = self.mlData[CLASS_LABEL]
        self.clf.fit(X,y)
        self.clf_stats = cross_validate(self.clf, X, y, cv=10, scoring=['accuracy', 'balanced_accuracy', 'f1_weighted', 'precision_weighted', 'recall_weighted'])
        self.clf_stats['accuracy'] = self.clf_stats['test_accuracy'].mean()*100.0
        self.clf_stats['balanced_accuracy'] = self.clf_stats['test_balanced_accuracy'].mean()*100.0
        self.clf_stats['f1_weighted'] = self.clf_stats['test_f1_weighted'].mean()*100.0
        self.clf_stats['precision_weighted'] = self.clf_stats['test_precision_weighted'].mean()*100.0
        self.clf_stats['recall_weighted'] = self.clf_stats['test_recall_weighted'].mean()*100.0

        self.clf_stats['classes'] = y.unique()
        self.clf_stats['num_channels'] = numChannels

        return self.clf_stats



    def preprocessData(self, rawTimestamps, rawData, samplingRate, synchronizedLabels):
        """
        Applies filter steps on raw collected EMG data samples, syncs class labels and groups.

        Parameters:
        rawTimestamps: list of timestamps of the recorded EMG data (same length of column axis as rawData); not used
        rawData: 2D-array containing recorded EMG data samples (rows) per channel (columns).
        samplingRate: estimated sampling rate based on rawTimestamps
        synchronizedLabels: list of calibration labels; each entry corresponds to the respective entry in rawData (same length of column axis as rawData)

        Returns:
        df: pandas DataFrame containing filterd data per channel (columns "EMG_X") and associated "class_label" and "group_index"

        """
        df = pd.DataFrame(rawData).transpose()
        df.columns = ['EMG_' + str(i) for i in range(len(df.columns))]

        if samplingRate >= 103.0:
            #normal filtering
            apply_bandpass_filter(df, 2.0, samplingRate/2.0-1.0, samplingRate)
            apply_bandstop_filter(df, 49.0, 51.0, samplingRate)
        else:
            raise SamplingRateTooLowError()

        df[CLASS_LABEL] = [x[0] for x in synchronizedLabels]
        df[GROUP_INDEX] = [x[1] for x in synchronizedLabels]


        #drop roughly the first two second to account for filter delays
        df.drop(df.index[list(range(0, int(2.0*samplingRate)))], inplace=True)
        df.drop(df.index[list(range(-int(2.0*samplingRate), 0))], inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df


class SamplingRateTooLowError(Exception):
    pass


class DataNotSynchronizedError(Exception):
    pass


class InsufficientDataRecordedError(Exception):
    pass
