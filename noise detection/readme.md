## About it

For each spectrum, frequency bins dominated by instrumental noise need to be filtered out before estimating the attenuation
coefficient. To determine the noise floor, we convert elevation spectra back to acceleration spectra and train a machine-
learning regression model on 4933 spectra from previous study for which the noise floor had already been identified manually. 
We use a histogram-based gradient boosting regressor, which performs well on datasets of this size, and the trained model can 
be applied to spectra with different frequency-bin settings than those used in training. The model was validated on spectra 
held out from training, reproducing the manually identified noise floor to within a factor of two in about 97% of cases. 
The training code and trained model perform well on our new datasets.

## How to use it:
import numpy as np
from predict_noise_floor import NoiseFloorModel
acc_noise_floor = np.zeros((len(ind_pair),2))
acc0 = wvsp[ind_pair, 0, :] * (2*np.pi*frq)**4
acc1 = wvsp[ind_pair, 1, :] * (2*np.pi*frq)**4
acc_all = np.vstack([acc0, acc1])            # (2*len(ind_pair), n_freq)
if frq.shape == m.freq_grid.shape and np.allclose(frq, m.freq_grid):
    x = np.log10(np.clip(acc_all, m.eps, None))
else:
    x = np.vstack([m._resample(frq, row)[0] for row in acc_all])
log_pred = m.model.predict(x)                 # ONE call for all 17000 rows
pred = 10 ** log_pred
n = len(ind_pair)
acc_noise_floor[ind_pair, 0] = pred[:n]
acc_noise_floor[ind_pair, 1] = pred[n:]


