## About it

For each spectrum, frequency bins dominated by instrumental noise need to be filtered out before estimating the attenuation
coefficient. To determine the noise floor, we convert elevation spectra back to acceleration spectra and train a machine-
learning regression model on 4933 spectra from previous study for which the noise floor had already been identified manually. 
We use a histogram-based gradient boosting regressor, which performs well on datasets of this size, and the trained model can 
be applied to spectra with different frequency-bin settings than those used in training. The model was validated on spectra 
held out from training, reproducing the manually identified noise floor to within a factor of two in about 97% of cases. 
The training code and trained model perform well on our new datasets.

## How to use the pre-trained model to detect instrumental noise from acceleration spectrum:



