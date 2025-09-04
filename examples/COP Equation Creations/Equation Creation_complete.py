
# 2 Variable equation creation in the following format:
# A·Te_in + F·Ts_out + G
import numpy as np
import matplotlib.pyplot as plt

# ── 1) Reference datasets, Data30 is the data for 30-35 secondary temperatures
data_30 = [
    (-20, -15, 30, 35, 1.60),
    (-15, -10, 30, 35, 2.10),
    (-10,  -5, 30, 35, 2.50),
    ( -5,   0, 30, 35, 2.90),
    (  0,   5, 30, 35, 3.45),
    (  5,  10, 30, 35, 3.75),
    (  6,  11, 30, 35, 3.90),
    (  7,  12, 30, 35, 4.10),
    (  8,  13, 30, 35, 4.20),
    (  9,  14, 30, 35, 4.40),
    ( 10,  15, 30, 35, 4.50),
    ( 11,  16, 30, 35, 4.70),
    ( 12,  17, 30, 35, 4.80),
    ( 13,  18, 30, 35, 5.00),
    ( 15,  20, 30, 35, 5.10),
    ( 20,  25, 30, 35, 5.40),
    ( 25,  30, 30, 35, 5.90),
    ( 30,  35, 30, 35, 6.40),
    ( 35,  40, 30, 35, 6.70),
]
data_50 = [
    (-7,  -12, 50, 55, 1.80),
    (-6,  -11, 50, 55, 1.90),
    (-5,  -10, 50, 55, 2.00),
    (-4,   -9, 50, 55, 2.10),
    (-3,   -8, 50, 55, 2.15),
    (-2,   -7, 50, 55, 2.20),
    (-1,   -6, 50, 55, 2.25),
    ( 0,   -5, 50, 55, 2.30),
    ( 1,   -4, 50, 55, 2.35),
    ( 2,   -3, 50, 55, 2.45),
    ( 3,   -2, 50, 55, 2.50),
    ( 4,   -1, 50, 55, 2.55),
    ( 5,    0, 50, 55, 2.60),
    ( 6,    1, 50, 55, 2.70),
    ( 7,    2, 50, 55, 2.90),
    ( 8,    3, 50, 55, 2.95),
    ( 9,    4, 50, 55, 3.00),
    (10,    5, 50, 55, 3.20),
    (15,   10, 50, 55, 3.45),
    (20,   15, 50, 55, 3.75),
    (25,   20, 50, 55, 4.00),
    (30,   35, 50, 55, 4.50),
    (35,   40, 50, 55, 4.57),
]

# ── 2) Fit segments for three Te_in ranges and two Ts_out values ──────────────
def fit_segments_with_ts_out(data):
    Te = np.array([d[0] for d in data])
    Ts_out = np.array([d[3] for d in data])
    COP = np.array([d[4] for d in data])
    
    masks = {
        'lt6': Te < 6,
        '6_10': (Te >= 6) & (Te <= 10),
        'gt10': Te > 10
    }
    
    fits = {}
    for key, mask in masks.items():
        X = np.vstack([Te[mask], Ts_out[mask], np.ones_like(Te[mask])]).T
        coeffs, *_ = np.linalg.lstsq(X, COP[mask], rcond=None)
        fits[key] = coeffs  # a, f, g
    return fits

# Fit both datasets
fits30 = fit_segments_with_ts_out(data_30)
fits50 = fit_segments_with_ts_out(data_50)

# ── 3) Plot data and fits ─────────────────────────────────────────────────────
Te30 = np.array([d[0] for d in data_30])
COP30 = np.array([d[4] for d in data_30])
Te50 = np.array([d[0] for d in data_50])
COP50 = np.array([d[4] for d in data_50])

Te_range = np.linspace(min(Te30.min(), Te50.min()), max(Te30.max(), Te50.max()), 500)

plt.figure(figsize=(10, 6))
plt.scatter(Te30, COP30, color='C0', label='Data (Ts_out=35°C)', marker='o')
plt.scatter(Te50, COP50, color='C1', label='Data (Ts_out=55°C)', marker='s')

for key in ['lt6', '6_10', 'gt10']:
    if key == 'lt6':
        x_vals = Te_range[Te_range < 6]
    elif key == '6_10':
        x_vals = Te_range[(Te_range >= 6) & (Te_range <= 10)]
    else:
        x_vals = Te_range[Te_range > 10]

    a30, f30, g30 = fits30[key]
    y30 = a30 * x_vals + f30 * 35 + g30
    plt.plot(x_vals, y30, color='C0', linestyle='-', label=f'Fit 30°C ({key})')

    a50, f50, g50 = fits50[key]
    y50 = a50 * x_vals + f50 * 55 + g50
    plt.plot(x_vals, y50, color='C1', linestyle='--', label=f'Fit 50°C ({key})')

plt.title("2 VAR EQ -  COP vs Te_in — Fitted Segments with Ts_out = 35°C / 55°C")
plt.xlabel("Te_in (°C)")
plt.ylabel("COP")
plt.grid(True, linestyle="--", alpha=0.4)
plt.legend(ncol=2, fontsize=8)
plt.tight_layout()
plt.show()

# ── Print Equations ─────────────────────────────────────────────
def print_equations(fits, Ts_out_label):
    print(f"\n--- 2 VAR EQ COP equations for Ts_out = {Ts_out_label}°C ---")
    for region, (a, f, g) in fits.items():
        print(f"{region}: COP = {a:.4f}·Te_in + {f:.4f}·Ts_out + {g:.4f}")

print_equations(fits30, 35)
print_equations(fits50, 55)
#
#
#
#
#
#
#
#
#
#
#
#

#4 variable equation in the format:
#COP = A·Te_in + D·Te_out + E·Ts_in + F·Ts_out + G


def fit_segments_4var(data):
    Te_in  = np.array([d[0] for d in data])
    Te_out = np.array([d[1] for d in data])
    Ts_in  = np.array([d[2] for d in data])
    Ts_out = np.array([d[3] for d in data])
    COP    = np.array([d[4] for d in data])
    masks = {
        'lt6':   Te_in < 6,
        '6_10': (Te_in >= 6) & (Te_in <= 10),
        'gt10':  Te_in > 10
    }
    fits = {}
    for region, mask in masks.items():
        X = np.vstack([Te_in[mask], Te_out[mask], Ts_in[mask], Ts_out[mask], np.ones_like(Te_in[mask])]).T
        coeffs, *_ = np.linalg.lstsq(X, COP[mask], rcond=None)
        fits[region] = coeffs  # a, d, e, f, g
    return fits

fits30 = fit_segments_4var(data_30)
fits50 = fit_segments_4var(data_50)

def cop_fit(te_in, te_out, ts_in, ts_out, coeffs):
    a, d, e, f, g = coeffs
    return a*te_in + d*te_out + e*ts_in + f*ts_out + g

# Make plots
fig, ax = plt.subplots(figsize=(10, 6))
regions = ['lt6', '6_10', 'gt10']
colors = ['C0', 'C1', 'C2']
labels = ['< 6°C', '6–10°C', '> 10°C']

for i, region in enumerate(regions):
    x30 = np.linspace(-20, 35, 300)
    x30_region = x30[(x30 < 6) if region == 'lt6' else (x30 > 10) if region == 'gt10' else (x30 >= 6) & (x30 <= 10)]
    y30 = cop_fit(x30_region, x30_region + 5, np.full_like(x30_region, 30), np.full_like(x30_region, 35), fits30[region])
    y50 = cop_fit(x30_region, x30_region + 5, np.full_like(x30_region, 50), np.full_like(x30_region, 55), fits50[region])

    ax.plot(x30_region, y30, color=colors[i], label=f"35°C {labels[i]}", linestyle='-')
    ax.plot(x30_region, y50, color=colors[i], label=f"55°C {labels[i]}", linestyle='--')

ax.set_title("4 VAR EQ COP vs Te_in with Full 4-Temperature Fit")
ax.set_xlabel("Te_in (°C)")
ax.set_ylabel("COP")
ax.grid(True, linestyle="--", alpha=0.4)
ax.legend(fontsize=8, ncol=2)
plt.tight_layout()
plt.show()

# Print equations
def print_equations(fits, Ts_out):
    print(f"\n--- 4 VAR EQ COP equations for Ts_out = {Ts_out}°C ---")
    for r, (a, d, e, f, g) in fits.items():
        print(f"{r}: COP = {a:.4f}·Te_in + {d:.4f}·Te_out + {e:.4f}·Ts_in + {f:.4f}·Ts_out + {g:.4f}")

print_equations(fits30, 35)
print_equations(fits50, 55)

#
#
#
#
#
#
#
#
#
#

#3 Variable equation for COP in the format of:
#COP = A·Te_in + E·Ts_in + F·Ts_out + G

import numpy as np
import matplotlib.pyplot as plt

def fit_segments_3temps(data):
    Te_in = np.array([d[0] for d in data])
    Ts_in = np.array([d[2] for d in data])
    Ts_out = np.array([d[3] for d in data])
    COP = np.array([d[4] for d in data])

    masks = {
        'lt6': Te_in < 6,
        '6_10': (Te_in >= 6) & (Te_in <= 10),
        'gt10': Te_in > 10
    }

    fits = {}
    for key, mask in masks.items():
        X = np.vstack([Te_in[mask], Ts_in[mask], Ts_out[mask], np.ones_like(Te_in[mask])]).T
        coeffs, *_ = np.linalg.lstsq(X, COP[mask], rcond=None)
        fits[key] = coeffs  # a, e, f, g
    return fits

# Fit models
fits30 = fit_segments_3temps(data_30)
fits50 = fit_segments_3temps(data_50)

# Print equations
def print_eqs_3temp(fits, label):
    print(f"\n--- 3 VAR EQ COP equations for {label} ---")
    for region, (a, e, f, g) in fits.items():
        print(f"{region}: COP = {a:.4f}·Te_in + {e:.4f}·Ts_in + {f:.4f}·Ts_out + {g:.4f}")

print_eqs_3temp(fits30, "Ts_out = 35°C")
print_eqs_3temp(fits50, "Ts_out = 55°C")

# Plot
Te30 = np.array([d[0] for d in data_30])
COP30 = np.array([d[4] for d in data_30])
Te50 = np.array([d[0] for d in data_50])
COP50 = np.array([d[4] for d in data_50])
Te_range = np.linspace(min(Te30.min(), Te50.min()), max(Te30.max(), Te50.max()), 500)

plt.figure(figsize=(10, 6))
plt.scatter(Te30, COP30, color='C0', label='Data (Ts_out=35°C)', marker='o')
plt.scatter(Te50, COP50, color='C1', label='Data (Ts_out=55°C)', marker='s')

for region in ['lt6', '6_10', 'gt10']:
    # Te range
    if region == 'lt6':
        x_vals = Te_range[Te_range < 6]
    elif region == '6_10':
        x_vals = Te_range[(Te_range >= 6) & (Te_range <= 10)]
    else:
        x_vals = Te_range[Te_range > 10]

    a30, e30, f30, g30 = fits30[region]
    y30 = a30 * x_vals + e30 * 30 + f30 * 35 + g30
    plt.plot(x_vals, y30, '-', color='C0', label=f'Fit 30°C ({region})')

    a50, e50, f50, g50 = fits50[region]
    y50 = a50 * x_vals + e50 * 50 + f50 * 55 + g50
    plt.plot(x_vals, y50, '--', color='C1', label=f'Fit 50°C ({region})')

plt.title("3 VAR EQ COP vs Te_in — Fitted Segments (Te_in, Ts_in, Ts_out)")
plt.xlabel("Te_in (°C)")
plt.ylabel("COP")
plt.grid(True, linestyle="--", alpha=0.4)
plt.legend(ncol=2, fontsize=8)
plt.tight_layout()
plt.show()











# Precise multiple equations between each point of the COP 


# The resulting CSV ("piecewise_cop_equations.csv") has columns:
# Ts_in, Te_start, Te_end, a (coeff Te_in), d (coeff Te_out),
# e (coeff Ts_in), f (coeff Ts_out), g (intercept).
# This covers:
#  - Ts_in=30: Te_in from −20 to +35
#  - Ts_in=50: Te_in from  −7 to +35
#  - Ts_in=35,40,45: Te_in from −7 to +35 (blended intervals)
#COP = a*Te_in + d*Te_out + e*Ts_in + f*Ts_out + g
import numpy as np
import pandas as pd

# ── 2) Build piecewise‐linear segments for Ts_in = 30 → Ts_out = 35
segments_30 = []
for i in range(len(data_30) - 1):
    Te0, _, Ts0, Tso0, COP0 = data_30[i]
    Te1, _, Ts1, Tso1, COP1 = data_30[i + 1]
    m30 = (COP1 - COP0) / (Te1 - Te0)
    b30 = COP0 - m30 * Te0
    segments_30.append({
        "Ts_in":    30,
        "Te_start": Te0,
        "Te_end":   Te1,
        "a":        m30,  # coefficient of Te_in
        "d":        0.0,  # coefficient of Te_out
        "e":        0.0,  # coefficient of Ts_in
        "f":        0.0,  # coefficient of Ts_out
        "g":        b30   # constant term
    })

# ── 3) Build piecewise‐linear segments for Ts_in = 50 → Ts_out = 55
segments_50 = []
for i in range(len(data_50) - 1):
    Te0, _, Ts0, Tso0, COP0 = data_50[i]
    Te1, _, Ts1, Tso1, COP1 = data_50[i + 1]
    m50 = (COP1 - COP0) / (Te1 - Te0)
    b50 = COP0 - m50 * Te0
    segments_50.append({
        "Ts_in":    50,
        "Te_start": Te0,
        "Te_end":   Te1,
        "a":        m50,
        "d":        0.0,
        "e":        0.0,
        "f":        0.0,
        "g":        b50
    })

# ── 4) Collect all unique Te_in breakpoints
breakpoints = sorted(
    set([seg["Te_start"] for seg in segments_30] + [seg["Te_end"] for seg in segments_30] +
        [seg["Te_start"] for seg in segments_50] + [seg["Te_end"] for seg in segments_50])
)

# ── 5) Helper to find slope/intercept at a given Te_mid
def find_params(Te_mid, segments):
    for seg in segments:
        if seg["Te_start"] <= Te_mid <= seg["Te_end"]:
            return seg["a"], seg["g"]
    return None, None

# ── 6) Build piecewise equations for Ts_in = 30, 35, 40, 45, 50
Ts_list = [30, 35, 40, 45, 50]
all_segments = []

for Ts in Ts_list:
    alpha = (Ts - 30.0) / 20.0  # 0.0 for Ts=30 → 1.0 for Ts=50

    if Ts == 30:
        all_segments.extend(segments_30)
        continue
    if Ts == 50:
        all_segments.extend(segments_50)
        continue

    # Intermediate Ts (35, 40, 45) → blend 30 and 50
    for j in range(len(breakpoints) - 1):
        x0 = breakpoints[j]
        x1 = breakpoints[j + 1]
        mid = 0.5 * (x0 + x1)

        m30_mid, b30_mid = find_params(mid, segments_30)
        m50_mid, b50_mid = find_params(mid, segments_50)
        if m30_mid is None or m50_mid is None:
            # Skip intervals not covered by both sides
            continue

        # Blend slope/intercept
        m_blend = (1 - alpha) * m30_mid + alpha * m50_mid
        b_blend = (1 - alpha) * b30_mid + alpha * b50_mid

        all_segments.append({
            "Ts_in":    Ts,
            "Te_start": x0,
            "Te_end":   x1,
            "a":        m_blend,  # coefficient of Te_in (cold inlet)
            "d":        0.0,      # coefficient of Te_out (cold outlet)
            "e":        0.0,      # coefficient of Ts_in (warm inlet)
            "f":        0.0,      # coefficient of Ts_out (warm outlet)
            "g":        b_blend   # constant term (intercept)
        })

# ── 7) Create DataFrame and export CSV ───────────────────────────────────────────
df_out = pd.DataFrame(all_segments, columns=[
    "Ts_in", "Te_start", "Te_end",
    "a", "d", "e", "f", "g"
])
df_out.to_csv("piecewise_cop_equations.csv", index=False)

#
#
#
#
#
#
#
#
#
#
#
#

# ── 10) Simplified equations (unused - not considerd)

def fit_segments(data):
    Te  = np.array([d[0] for d in data])
    COP = np.array([d[4] for d in data])
    masks = {
        'lt6':   Te < 6,
        '6_10': (Te >= 6) & (Te <= 10),
        'gt10':  Te > 10
    }
    return {k: np.polyfit(Te[m], COP[m], 1) for k, m in masks.items()}

# fit once
fits30 = fit_segments(data_30)
fits50 = fit_segments(data_50)

def cop_simplified(Te, Ts):
    # pick segment
    key = 'lt6' if Te < 6 else '6_10' if Te <= 10 else 'gt10'
    if Ts <= 30:
        m, b = fits30[key]
    elif Ts >= 50:
        m, b = fits50[key]
    else:
        α     = (Ts - 30.0) / 20.0
        m30,b30 = fits30[key]
        m50,b50 = fits50[key]
        m      = (1-α)*m30 + α*m50
        b      = (1-α)*b30 + α*b50
    return m*Te + b

# ── Build grid and heatmap ─────────────────────────────────────────────────────
t_in_vals  = np.linspace(-20, 35, 56)   # Te_in from −20 to 35°C
ts_in_vals = np.linspace(30,  50, 41)   # Ts_in from 30 to 50°C

grid = pd.DataFrame([(t, ts) for t in t_in_vals for ts in ts_in_vals], columns=["Te_in","Ts_in"])

# attach to your existing grid
grid['COP_smpl'] = grid.apply(lambda r: cop_simplified(r.Te_in, r.Ts_in), axis=1)

# optional: compare heatmaps/plots using 'COP_smpl' vs 'COP'

# ── Extra: Combined fit plot for Ts_in=30 and Ts_in=50 ────────────────────────
def fit_segments_with_ts_out(data):
    Te      = np.array([d[0] for d in data])
    Ts_out  = np.array([d[3] for d in data])
    COP     = np.array([d[4] for d in data])

    masks = {
        'lt6':   Te < 6,
        '6_10': (Te >= 6) & (Te <= 10),
        'gt10':  Te > 10
    }

    fits = {}
    for key, mask in masks.items():
        X = np.vstack([Te[mask], Ts_out[mask], np.ones_like(Te[mask])]).T
        coeffs, *_ = np.linalg.lstsq(X, COP[mask], rcond=None)
        fits[key] = coeffs  # a, f, g
    return fits

# Fit both sets
fits30 = fit_segments_with_ts_out(data_30)
fits50 = fit_segments_with_ts_out(data_50)

# Original data
Te30 = np.array([d[0] for d in data_30])
COP30 = np.array([d[4] for d in data_30])
Te50 = np.array([d[0] for d in data_50])
COP50 = np.array([d[4] for d in data_50])

# Plot
plt.figure(figsize=(10, 6))
plt.scatter(Te30, COP30, color='C0', label='Data (Ts_out=35°C)', marker='o')
plt.scatter(Te50, COP50, color='C1', label='Data (Ts_out=55°C)', marker='s')

Te_range = np.linspace(min(Te30.min(), Te50.min()), max(Te30.max(), Te50.max()), 500)

# Plot fits for each region
for key in ['lt6', '6_10', 'gt10']:
    # Range
    if key == 'lt6':
        x_vals = Te_range[Te_range < 6]
    elif key == '6_10':
        x_vals = Te_range[(Te_range >= 6) & (Te_range <= 10)]
    else:
        x_vals = Te_range[Te_range > 10]

    # Fit 30
    a30, f30, g30 = fits30[key]
    y30 = a30 * x_vals + f30 * 35 + g30
    plt.plot(x_vals, y30, color='C0', linestyle='-', label=f'Fit 30°C ({key})')

    # Fit 50
    a50, f50, g50 = fits50[key]
    y50 = a50 * x_vals + f50 * 55 + g50
    plt.plot(x_vals, y50, color='C1', linestyle='--', label=f'Fit 50°C ({key})')

plt.title("EXTRA COP vs Te_in — Fitted Segments with Ts_out = 35°C / 55°C")
plt.xlabel("Te_in (°C)")
plt.ylabel("COP")
plt.grid(True, linestyle="--", alpha=0.4)
plt.legend(ncol=2, fontsize=8)
plt.tight_layout()
plt.show()


def print_equations(fits, Ts_out_label):
    print(f"\n--- EXTRA COP equations for Ts_out = {Ts_out_label}°C ---")
    for region, (a, f, g) in fits.items():
        print(f"{region}: COP = {a:.4f}·Te_in + {f:.4f}·Ts_out + {g:.4f}")

# Print equations
print_equations(fits30, 35)
print_equations(fits50, 55)