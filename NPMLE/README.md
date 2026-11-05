npmle.py estimates the **median** when some values are known exactly and others are only
known to be above or below a bound.

---

## 1. Mechanism

### Step 1: each observation becomes an interval

| Input    | Meaning            | Interval        |
|----------|--------------------|-----------------|
| `exact`  | value = x          | [x, x]          |
| `lower`  | value > L          | [L, ∞)          |
| `upper`  | value < U          | [low_end, U]    |

### Step 2: build the boxes

The script sorts all the interval endpoints. Wherever a left end is directly
followed by a right end, the two form a **box**. Every exact value gets its own
point box. The probability mass can go only into these boxes.

### Step 3: share out the mass (EM)

1. Start with equal mass in every box.
2. Each exact value puts 1 into its own box.
3. Each bounded value splits 1 across the boxes inside its interval, in proportion
   to the current mass.
4. Divide by n to get the new mass `w`.
5. Repeat until `w` stops changing.

### Step 4: read the median

Add up `w` from the left. The median is where the running total reaches 0.5:
- If that happens inside a point x.
- If it happens inside a finite box [a, b], or exactly between two boxes, the
  median is the midpoint.
- If that box reaches −∞ or +∞, the median is NaN (the data can't bound it).

---

## 2. How to use

### Basic call

```python
from npmle import npmle_fit, npmle_median

p, q, w = npmle_fit(exact=[1, 2, 4, 5], lower=[3, 3], upper=[])
med = npmle_median(p, q, w)
```

- `npmle_fit` returns the boxes `[p, q]` and their mass `w`.
- `npmle_median` returns the meda can't bound it.

### Arguments of `npmle_fit`

| Argument  | What to pass                          |
|-----------|-----------------------------------------------------------------|
| `exact`   | values known exact                    |
| `lower`   | lower bounds (value is above them)                              |
| `upper`   | upper bounds (valu                    |
| `low_end` | lowest possible value: `-np.inf` (default), or `0.0` if the value is always positive |

NaN and inf are dropped automatis are fine.


