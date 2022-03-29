"""
Base module to measure eccentricity and mean anomaly for given waveform data.

Part of Defining eccentricity project
Md Arif Shaikh, Mar 29, 2022
"""

import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline


class eccDefinition:
    """Measure eccentricity from given waveform data dictionary."""

    def __init__(self, dataDict):
        """Init eccDefinition class.

        parameters:
        ----------
        dataDict: Dictionary conntaining time, modes, etc
        """
        self.dataDict = dataDict
        self.time = self.dataDict["t"]
        self.hlm = self.dataDict["hlm"]
        self.h22 = self.hlm[(2, 2)]
        self.amp22 = np.abs(self.h22)
        self.time = self.time - get_peak_via_quadratic_fit(
            self.time, self.amp22)
        self.phase22 = - np.unwrap(np.angle(self.h22))
        self.omega22 = np.gradient(self.phase22, self.time)

    def find_peaks(self, order=10):
        """Find the peaks in the data.

        parameters:
        -----------
        order: window/width of peaks
        """
        raise NotImplementedError("Please override me.")

    def find_troughs(self, order=10):
        """Find the troughs in the data.

        parameters:
        -----------
        order: window/width of troughs
        """
        raise NotImplementedError("Please override me.")

    def peaks_interp(self, order=10, **kwargs):
        """Interpolator through peaks."""
        peak_idx = self.find_peaks(order)
        if len(peak_idx) >= 2:
            return InterpolatedUnivariateSpline(self.time[peak_idx],
                                                self.omega22[peak_idx],
                                                **kwargs)
        else:
            print("...Number of peaks is less than 2. Not able"
                  " to create an interpolator.")
            return None

    def troughs_interp(self, order=10, **kwargs):
        """Interpolator through troughs."""
        trough_idx = self.find_troughs(order)
        if len(trough_idx) >= 2:
            return InterpolatedUnivariateSpline(self.time[trough_idx],
                                                self.omega22[trough_idx],
                                                **kwargs)
        else:
            print("...Number of troughs is less than 2. Not able"
                  " to create an interpolator.")
            return None

    def measure_ecc(self, t_ref, order=10, **kwargs):
        """Measure eccentricity and meann anomaly at reference time.

        parameters:
        ----------
        t_ref: reference time to measure eccentricity and mean anomaly.
        order: width of peaks/troughs
        kwargs: any extra kwargs to the peak/trough findining functions.

        returns:
        --------
        ecc_ref: measured eccentricity at t_ref
        mean_ano_ref: measured mean anomaly at t_ref
        """
        default_kwargs = {"w": None,
                          "bbox": [None, None],
                          "k": 3,
                          "ext": 0,
                          "check_finite": False}
        for kw in default_kwargs.keys():
            if kw in kwargs:
                default_kwargs[kw] = kwargs[kw]

        peaks_interpolator = self.peaks_interp(order, **default_kwargs)
        troughs_interpolator = self.troughs_interp(order, **default_kwargs)

        if peaks_interpolator is None or troughs_interpolator is None:
            print("...Sufficient number of peaks/troughs are not found."
                  " Can not create an interpolator. Most probably the "
                  "excentricity is too small. Returning eccentricity to be"
                  " zero")
            ecc_ref = 0
            mean_ano_ref = 0
        else:
            eccVals = ((np.sqrt(np.abs(peaks_interpolator(self.time)))
                        - np.sqrt(np.abs(troughs_interpolator(self.time))))
                       / (np.sqrt(np.abs(peaks_interpolator(self.time)))
                          + np.sqrt(np.abs(troughs_interpolator(self.time)))))
            ecc_interpolator = InterpolatedUnivariateSpline(self.time, eccVals,
                                                            **default_kwargs)
            ecc_ref = ecc_interpolator(t_ref)

            idx_peaks = self.find_peaks(order)
            meanperAnoVals = np.array([])
            timeVals = np.array([])

            idx = 0
            while idx < len(idx_peaks) - 1:
                orbital_period = (self.times[idx_peaks[idx + 1]]
                                  - self.times[idx_peaks[idx]])
                time_since_last_peak = (
                    self.times[idx_peaks[idx]: idx_peaks[idx + 1]]
                    - self.times[idx_peaks[idx]])
                meanperAno = 2 * np.pi * time_since_last_peak / orbital_period
                meanperAnoVals = np.append(meanperAnoVals, meanperAno)
                timeVals = np.append(
                    timeVals,
                    self.times[idx_peaks[idx]: idx_peaks[idx + 1]])
                idx += 1

            mean_ano_interpolator = InterpolatedUnivariateSpline(
                timeVals, meanperAnoVals, **kwargs)
            mean_ano_ref = mean_ano_interpolator(t_ref)

        return ecc_ref, mean_ano_ref


def get_peak_via_quadratic_fit(t, func):
    """
    Find the peak time of a function quadratically.

    Fits the function to a quadratic over the 5 points closest to the argmax
    func.
    t : an array of times
    func : array of function values
    Returns: tpeak, fpeak
    """
    # Find the time closest to the peak, making sure we have room on either
    # side
    index = np.argmax(func)
    index = max(2, min(len(t) - 3, index))

    # Do a quadratic fit to 5 points,
    # subtracting t[index] to make the matrix inversion nice
    testTimes = t[index-2:index+3] - t[index]
    testFuncs = func[index-2:index+3]
    xVecs = np.array([np.ones(5), testTimes, testTimes**2.])
    invMat = np.linalg.inv(np.array([[v1.dot(v2) for v1 in xVecs]
                                     for v2 in xVecs]))

    yVec = np.array([testFuncs.dot(v1) for v1 in xVecs])
    coefs = np.array([yVec.dot(v1) for v1 in invMat])
    return t[index] - coefs[1]/(2.*coefs[2]), (coefs[0]
                                               - coefs[1]**2./4/coefs[2])
