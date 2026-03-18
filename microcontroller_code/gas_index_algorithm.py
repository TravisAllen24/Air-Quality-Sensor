# ---------------------------------------------------------------------------
# Sensirion Gas Index Algorithm (VOC Index & NOx Index)
# Ported from Sensirion gas-index-algorithm v3.2.0 (C floating-point reference)
# https://github.com/Sensirion/gas-index-algorithm
#
# Copyright (c) 2022, Sensirion AG – BSD-3-Clause license
# ---------------------------------------------------------------------------

import math


class GasIndexAlgorithm:
    """
    Sensirion Gas Index Algorithm for SGP4x sensors.
    Calculates VOC Index or NOx Index (1-500) from raw sensor ticks.

    Usage::

        voc_algo = GasIndexAlgorithm(GasIndexAlgorithm.ALGORITHM_TYPE_VOC)
        nox_algo = GasIndexAlgorithm(GasIndexAlgorithm.ALGORITHM_TYPE_NOX)
        ...
        voc_index = voc_algo.process(sraw_voc)
        nox_index = nox_algo.process(sraw_nox)
    """

    ALGORITHM_TYPE_VOC = 0
    ALGORITHM_TYPE_NOX = 1

    def __init__(self, algorithm_type=0, sampling_interval=1.0):
        self._type = algorithm_type
        self._sampling_interval = sampling_interval

        # Type-specific parameters
        if algorithm_type == self.ALGORITHM_TYPE_NOX:
            self._index_offset = 1.0
            self._sraw_minimum = 10000
            self._gating_max_duration_min = 720.0
            self._init_duration_mean = 17100.0
            self._init_duration_variance = 20520.0
            self._gating_threshold = 30.0
            self._sigmoid_k = -0.0101
            self._sigmoid_x0 = 614.0
            self._tau_initial_mean = 1200.0
        else:
            self._index_offset = 100.0
            self._sraw_minimum = 20000
            self._gating_max_duration_min = 180.0
            self._init_duration_mean = 2700.0
            self._init_duration_variance = 5220.0
            self._gating_threshold = 340.0
            self._sigmoid_k = -0.0065
            self._sigmoid_x0 = 213.0
            self._tau_initial_mean = 20.0

        self._index_gain = 230.0
        self._tau_mean_hours = 12.0
        self._tau_variance_hours = 12.0
        self._sraw_std_initial = 50.0

        self.reset()

    def reset(self):
        """Reset internal algorithm states."""
        self._uptime = 0.0
        self._sraw = 0.0
        self._gas_index = 0.0
        self._init_instances()

    @staticmethod
    def _sigmoid(k, x0, sample):
        x = k * (sample - x0)
        if x < -50.0:
            return 1.0
        if x > 50.0:
            return 0.0
        return 1.0 / (1.0 + math.exp(x))

    def _init_instances(self):
        si = self._sampling_interval
        gs = 64.0   # GAMMA_SCALING
        ags = 8.0   # ADDITIONAL_GAMMA_MEAN_SCALING

        # Mean-variance estimator state
        self._mve_initialized = False
        self._mve_mean = 0.0
        self._mve_sraw_offset = 0.0
        self._mve_std = self._sraw_std_initial
        self._mve_gamma_mean = (ags * gs * (si / 3600.0)) / (self._tau_mean_hours + (si / 3600.0))
        self._mve_gamma_variance = (gs * (si / 3600.0)) / (self._tau_variance_hours + (si / 3600.0))
        self._mve_gamma_initial_mean = (ags * gs * si) / (self._tau_initial_mean + si)
        self._mve_gamma_initial_variance = (gs * si) / (2500.0 + si)
        self._mve_gamma_mean_active = 0.0
        self._mve_gamma_variance_active = 0.0
        self._mve_uptime_gamma = 0.0
        self._mve_uptime_gating = 0.0
        self._mve_gating_duration_min = 0.0

        # Mox model state
        self._mox_sraw_std = self._mve_std
        self._mox_sraw_mean = self._mve_mean + self._mve_sraw_offset

        # Sigmoid-scaled state
        self._ss_k = self._sigmoid_k
        self._ss_x0 = self._sigmoid_x0
        self._ss_offset_default = self._index_offset

        # Adaptive lowpass state
        self._lp_a1 = si / (20.0 + si)
        self._lp_a2 = si / (500.0 + si)
        self._lp_initialized = False
        self._lp_x1 = 0.0
        self._lp_x2 = 0.0
        self._lp_x3 = 0.0

    # --- Mox model ---
    def _mox_process(self, sraw):
        if self._type == self.ALGORITHM_TYPE_NOX:
            return ((sraw - self._mox_sraw_mean) / 2000.0) * self._index_gain
        return ((sraw - self._mox_sraw_mean) / (-(self._mox_sraw_std + 220.0))) * self._index_gain

    # --- Sigmoid-scaled ---
    def _sigmoid_scaled_process(self, sample):
        x = self._ss_k * (sample - self._ss_x0)
        if x < -50.0:
            return 500.0
        if x > 50.0:
            return 0.0
        if sample >= 0.0:
            if self._ss_offset_default == 1.0:
                shift = (500.0 / 499.0) * (1.0 - self._index_offset)
            else:
                shift = (500.0 - 5.0 * self._index_offset) / 4.0
            return ((500.0 + shift) / (1.0 + math.exp(x))) - shift
        return (self._index_offset / self._ss_offset_default) * (500.0 / (1.0 + math.exp(x)))

    # --- Adaptive lowpass ---
    def _adaptive_lowpass_process(self, sample):
        if not self._lp_initialized:
            self._lp_x1 = sample
            self._lp_x2 = sample
            self._lp_x3 = sample
            self._lp_initialized = True
        self._lp_x1 = (1.0 - self._lp_a1) * self._lp_x1 + self._lp_a1 * sample
        self._lp_x2 = (1.0 - self._lp_a2) * self._lp_x2 + self._lp_a2 * sample
        abs_delta = abs(self._lp_x1 - self._lp_x2)
        f1 = math.exp(-0.2 * abs_delta)
        tau_a = 480.0 * f1 + 20.0
        a3 = self._sampling_interval / (self._sampling_interval + tau_a)
        self._lp_x3 = (1.0 - a3) * self._lp_x3 + a3 * sample
        return self._lp_x3

    # --- Mean-variance estimator ---
    def _mve_calculate_gamma(self):
        si = self._sampling_interval
        uptime_limit = 32767.0 - si
        if self._mve_uptime_gamma < uptime_limit:
            self._mve_uptime_gamma += si
        if self._mve_uptime_gating < uptime_limit:
            self._mve_uptime_gating += si

        sig = self._sigmoid

        sigmoid_gamma_mean = sig(0.01, self._init_duration_mean, self._mve_uptime_gamma)
        gamma_mean = self._mve_gamma_mean + (
            (self._mve_gamma_initial_mean - self._mve_gamma_mean) * sigmoid_gamma_mean)

        gating_threshold_mean = self._gating_threshold + (
            (510.0 - self._gating_threshold) * sig(0.01, self._init_duration_mean, self._mve_uptime_gating))

        sigmoid_gating_mean = sig(0.09, gating_threshold_mean, self._gas_index)
        self._mve_gamma_mean_active = sigmoid_gating_mean * gamma_mean

        sigmoid_gamma_variance = sig(0.01, self._init_duration_variance, self._mve_uptime_gamma)
        gamma_variance = self._mve_gamma_variance + (
            (self._mve_gamma_initial_variance - self._mve_gamma_variance)
            * (sigmoid_gamma_variance - sigmoid_gamma_mean))

        gating_threshold_variance = self._gating_threshold + (
            (510.0 - self._gating_threshold) * sig(0.01, self._init_duration_variance, self._mve_uptime_gating))

        sigmoid_gating_variance = sig(0.09, gating_threshold_variance, self._gas_index)
        self._mve_gamma_variance_active = sigmoid_gating_variance * gamma_variance

        self._mve_gating_duration_min += (
            (si / 60.0) * (((1.0 - sigmoid_gating_mean) * 1.3) - 0.3))

        if self._mve_gating_duration_min < 0.0:
            self._mve_gating_duration_min = 0.0
        if self._mve_gating_duration_min > self._gating_max_duration_min:
            self._mve_uptime_gating = 0.0

    def _mve_process(self, sraw):
        gs = 64.0
        ags = 8.0
        if not self._mve_initialized:
            self._mve_initialized = True
            self._mve_sraw_offset = sraw
            self._mve_mean = 0.0
        else:
            if self._mve_mean >= 100.0 or self._mve_mean <= -100.0:
                self._mve_sraw_offset += self._mve_mean
                self._mve_mean = 0.0
            sraw = sraw - self._mve_sraw_offset
            self._mve_calculate_gamma()
            delta_sgp = (sraw - self._mve_mean) / gs

            if delta_sgp < 0.0:
                c = self._mve_std - delta_sgp
            else:
                c = self._mve_std + delta_sgp

            additional_scaling = 1.0
            if c > 1440.0:
                additional_scaling = (c / 1440.0) ** 2

            self._mve_std = (
                math.sqrt(additional_scaling * (gs - self._mve_gamma_variance_active))
                * math.sqrt(
                    self._mve_std * (self._mve_std / (gs * additional_scaling))
                    + (self._mve_gamma_variance_active * delta_sgp / additional_scaling) * delta_sgp
                )
            )
            self._mve_mean += (self._mve_gamma_mean_active * delta_sgp) / ags

    # --- Public API ---
    def process(self, sraw):
        """
        Calculate the gas index value from a raw SGP4x sensor tick.

        :param sraw: Raw signal tick (SRAW_VOC or SRAW_NOX) from SGP4x sensor.
        :returns: Gas index value (int). 0 during initial blackout, 1-500 afterwards.
        """
        if self._uptime <= 45.0:
            self._uptime += self._sampling_interval
        else:
            if 0 < sraw < 65000:
                if sraw < self._sraw_minimum + 1:
                    sraw = self._sraw_minimum + 1
                elif sraw > self._sraw_minimum + 32767:
                    sraw = self._sraw_minimum + 32767
                self._sraw = float(sraw - self._sraw_minimum)

            if self._type == self.ALGORITHM_TYPE_VOC or self._mve_initialized:
                self._gas_index = self._mox_process(self._sraw)
                self._gas_index = self._sigmoid_scaled_process(self._gas_index)
            else:
                self._gas_index = self._index_offset

            self._gas_index = self._adaptive_lowpass_process(self._gas_index)

            if self._gas_index < 0.5:
                self._gas_index = 0.5

            if self._sraw > 0.0:
                self._mve_process(self._sraw)
                self._mox_sraw_std = self._mve_std
                self._mox_sraw_mean = self._mve_mean + self._mve_sraw_offset

        return int(self._gas_index + 0.5)
