## 1. Introduction

The attenuation coefficient is defined as:

$$\alpha = \dots \tag{1}$$

OMBs use an accelerometer to measure vertical acceleration. Instrumental noise is
noticeable at frequencies where wave energy is minimal. The recorded acceleration
spectrum is:

$$\alpha(f) = \frac{1}{\Delta x} \ln \frac{S_\mathrm{up}(f)}{S_\mathrm{dn}(f)}$$

## 2. Key idea

At each (pair, frequency) bin, each of the two buoys is either detected or not.
That gives four combinations, and three of them carry information.

![Figure 1](figures/regimes.png)

*Figure 1: The four regimes at one frequency (grey dashed vertical line). Solid lines
are what the buoy records, faint dashed lines the true spectrum, dotted horizontal
lines each buoy's own noise floor. Note that the two buoys have different floors —
that is why the third case, in which the upstream buoy is the blind one, occurs at all.*

1. **Both detected.** Both spectra are trustworthy, so Eq. (1) gives $\alpha$
   exactly. Call this an *exact* observation.
2. **Downstream not detected, upstream detected.** The recorded $S_\mathrm{dn}$ is
   too large (Eq. 2), so the computed $\alpha$ is too small — but by how much we do
   not know. What we do know is that the true $\alpha$ is at least the computed
   value: $\alpha_\mathrm{true} \geq \hat{\alpha}$ (a *lower bound*).
3. **Upstream not detected, downstream detected.** Now the recorded
   $S_\mathrm{up}$ is too large, so the computed $\alpha$ is too large:
   $\alpha_\mathrm{true} \leq \hat{\alpha}$ (an *upper bound*).
4. **Neither detected.** Both spectra are overstated by unknown amounts, and the
   errors work in opposite directions on the ratio, so little can be said. These
   bins are discarded.
