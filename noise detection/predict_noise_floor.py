"""
Apply the trained noise-floor model to new spectra.

New data is NOT assumed to share the training frequency grid: it may have
a different length, different frequency spacing, different min/max
frequency (different buoy/instrument). Each new spectrum is resampled
(log-energy vs. frequency, linear interpolation) onto the exact 85-point
grid the model was trained on before prediction. Frequencies outside the
new spectrum's own coverage can't be interpolated - they're filled by
edge-extension (same convention used for the rare missing bin at training
time), and `coverage` tells you how much of that filling happened, so you
can judge whether to trust a given prediction.

Usage:
    from predict_noise_floor import NoiseFloorModel
    m = NoiseFloorModel()                      # loads noise_floor_model.joblib
    result = m.predict(freq_hz, spectrum)       # single spectrum, any length
    results = m.predict_batch([(f1, s1), (f2, s2), ...])
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")

from pathlib import Path
from dataclasses import dataclass

import numpy as np
import joblib

HERE = Path(__file__).parent
MODEL_PATH = HERE / "noise_floor_model.joblib"


@dataclass
class Prediction:
    noise_floor: float       # predicted noise floor, original energy units
    log10_noise_floor: float
    coverage: float          # fraction of the model's freq grid actually
                              # covered by the input spectrum's own range,
                              # 1.0 = fully covered, no extrapolation


class NoiseFloorModel:
    def __init__(self, model_path=MODEL_PATH):
        bundle = joblib.load(model_path)
        self.model = bundle["model"]
        self.freq_grid = np.asarray(bundle["freq_grid"])
        self.eps = bundle["eps"]

    def _resample(self, freq_hz, spectrum):
        freq_hz = np.asarray(freq_hz, dtype=float)
        spectrum = np.asarray(spectrum, dtype=float)
        if freq_hz.shape != spectrum.shape:
            raise ValueError("freq_hz and spectrum must be the same length")
        order = np.argsort(freq_hz)
        freq_hz, spectrum = freq_hz[order], spectrum[order]

        log_e = np.log10(np.clip(spectrum, self.eps, None))
        in_range = (self.freq_grid >= freq_hz.min()) & (self.freq_grid <= freq_hz.max())
        # np.interp already edge-extends for points outside the input's
        # range (returns the boundary value), matching the training-time
        # fill convention.
        x = np.interp(self.freq_grid, freq_hz, log_e)
        coverage = in_range.mean()
        return x, coverage

    def predict(self, freq_hz, spectrum) -> Prediction:
        x, coverage = self._resample(freq_hz, spectrum)
        log_pred = float(self.model.predict(x[None, :])[0])
        return Prediction(
            noise_floor=10 ** log_pred,
            log10_noise_floor=log_pred,
            coverage=coverage,
        )

    def predict_batch(self, spectra):
        """spectra: iterable of (freq_hz, spectrum) pairs, any lengths."""
        return [self.predict(f, s) for f, s in spectra]


if __name__ == "__main__":
    # Sanity check: pull a few real training spectra, subsample them to a
    # DIFFERENT, ragged length/frequency grid (simulating "new data with a
    # different length of spectrum"), run them through the resample +
    # predict pipeline, and compare against their true labels.
    import pandas as pd

    w = pd.read_csv(HERE / "wvsp.csv", header=None).values.T  # (n, 85)
    y = pd.read_csv(HERE / "noise.csv", header=None)[0].values
    m = NoiseFloorModel()

    rng = np.random.default_rng(0)
    print(f"{'true':>12}  {'pred':>12}  {'ratio':>7}  {'coverage':>8}  n_input_pts")
    for i in rng.choice(len(y), size=8, replace=False):
        full_freq = m.freq_grid
        n_keep = rng.integers(15, 60)  # different length each time
        keep = np.sort(rng.choice(len(full_freq), size=n_keep, replace=False))
        result = m.predict(full_freq[keep], w[i, keep])
        ratio = result.noise_floor / y[i]
        print(f"{y[i]:12.3e}  {result.noise_floor:12.3e}  {ratio:7.2f}  "
              f"{result.coverage:8.0%}  {n_keep}")
