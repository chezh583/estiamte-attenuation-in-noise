"""
Baseline ML model for buoy acceleration-spectrum noise-floor regression.

Data (this run only covers the "clean" case: noise != NaN and != 100,
already filtered by hand into noise.csv):
    wvsp.csv  : 85 x 4933, rows = frequency bins, cols = samples
    noise.csv : 4933 x 1,  manually-picked noise floor (energy units)
    buoy_groups.csv (optional, from match_buoys.py): col_idx -> buoy id,
        used for leakage-safe cross-validation.

Approach, per discussion:
  - Work in log10 space for both input spectrum and target: the data
    spans several decades and the meaningful notion of error is
    "within a factor of X", not absolute energy units.
  - Feature = log10(spectrum), i.e. the 85 log-energy values directly.
    This is the simple starting point; swap in engineered/length-invariant
    features later if you extend to other instruments with different
    frequency grids.
  - Model = HistGradientBoostingRegressor (sklearn): sample-efficient,
    handles the ~5k rows we have far better than a deep net would, and
    gives feature_importances-style diagnostics for free.
  - Evaluation = GroupKFold by buoy, NOT a random split. Noise floor is
    strongly autocorrelated within a buoy (lag-1 autocorr ~0.8 in raw
    column order), so a random split leaks near-duplicate spectra across
    train/test and overstates accuracy. Samples we couldn't match to a
    buoy (no buoy_groups.csv entry) get their own singleton group so
    they never leak either.
"""
import os
# Cap BLAS/OpenMP threads *before* importing sklearn: on a many-core shared
# node, HistGradientBoostingRegressor's default thread count (= all cores)
# causes massive oversubscription overhead on a dataset this small - a
# single fit went from ~1.5s to 7+ minutes without this.
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error

HERE = Path(__file__).parent
WVSP_CSV = HERE / "wvsp.csv"
NOISE_CSV = HERE / "noise.csv"
GROUPS_CSV = HERE / "buoy_groups.csv"  # optional; run match_buoys.py first
NC_FILE = HERE / "../OMB/2022_AWI_UTOKYO/v2021.nc"  # source of the freq grid
EPS = 1e-12
N_SPLITS = 5
RANDOM_STATE = 0


def load_freq_grid():
    """The 85 frequencies wvsp.csv's rows correspond to (AWI_UTOKYO grid).
    Saved alongside the model so new data - which may be on a different
    grid / a different length entirely - can be resampled onto it before
    prediction. See predict_noise_floor.py.
    """
    import netCDF4 as nc
    d = nc.Dataset(NC_FILE)
    return np.array(d.variables["frequencies_waves_imu"][:])


def load_data():
    w = pd.read_csv(WVSP_CSV, header=None).values.T  # (n_samples, n_freq)
    y = pd.read_csv(NOISE_CSV, header=None)[0].values

    x = np.log10(np.clip(w, EPS, None))
    # Impute the rare (515/4933) single missing bin per sample by linear
    # interpolation *in log space* along frequency (nearest neighbours in
    # the same row) - consistent with how predict_noise_floor.py resamples
    # new data. A handful of true zero-padding entries (raw energy = 0,
    # not NaN) are left as EPS -> "far below everything else": a harmless
    # sentinel if it's genuine padding; if you later track true per-sample
    # length, mask those out instead.
    x = pd.DataFrame(x).interpolate(axis=1, limit_direction="both").values

    logy = np.log10(np.clip(y, EPS, None))
    return x, logy, y


def load_groups(n_samples):
    if GROUPS_CSV.exists():
        g = pd.read_csv(GROUPS_CSV)
        groups = np.array([f"unmatched_{i}" for i in range(n_samples)], dtype=object)
        groups[g["col_idx"].values] = g["buoy"].values
        n_unmatched = (pd.Series(groups).str.startswith("unmatched_")).sum()
        print(f"groups: {n_samples - n_unmatched} matched to a buoy, "
              f"{n_unmatched} unmatched (each its own singleton group)")
        return groups
    print("buoy_groups.csv not found - run match_buoys.py first for a "
          "leakage-safe split; falling back to one group per sample "
          "(equivalent to a random split, will look overly optimistic).")
    return np.arange(n_samples)


def evaluate(x, logy, groups):
    gkf = GroupKFold(n_splits=N_SPLITS)
    fold_mae, fold_within2x = [], []
    for fold, (tr, te) in enumerate(gkf.split(x, logy, groups)):
        model = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
        model.fit(x[tr], logy[tr])
        pred = model.predict(x[te])
        mae = mean_absolute_error(logy[te], pred)
        within2x = (np.abs(pred - logy[te]) < np.log10(2)).mean()
        fold_mae.append(mae)
        fold_within2x.append(within2x)
        print(f"fold {fold}: n_test={len(te)}  "
              f"MAE(log10)={mae:.3f}  within-factor-2={within2x:.2%}")
    print(f"\nmean MAE(log10) = {np.mean(fold_mae):.3f} "
          f"(i.e. typical error is a factor of {10**np.mean(fold_mae):.2f}x)")
    print(f"mean within-factor-2 = {np.mean(fold_within2x):.2%}")


def fit_final_model(x, logy):
    model = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
    model.fit(x, logy)
    return model


def main():
    x, logy, y_raw = load_data()
    groups = load_groups(len(y_raw))
    freq_grid = load_freq_grid()
    print(f"loaded {x.shape[0]} samples, {x.shape[1]} freq bins, "
          f"{len(np.unique(groups))} groups\n")

    evaluate(x, logy, groups)

    model = fit_final_model(x, logy)
    import joblib
    bundle = {"model": model, "freq_grid": freq_grid, "eps": EPS}
    joblib.dump(bundle, HERE / "noise_floor_model.joblib")
    print(f"\nfinal model (trained on all {len(y_raw)} samples) saved to "
          f"noise_floor_model.joblib, bundled with its {len(freq_grid)}-bin "
          f"frequency grid for predict_noise_floor.py")


if __name__ == "__main__":
    main()
