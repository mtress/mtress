#3Variable_COP_noRegions
data_30 = [
    ( -5,   0, 30, 35, 2.90),
    (  7,  12, 30, 35, 4.10),
    ( 25,  30, 30, 35, 5.90),
    ( 30,  35, 30, 35, 6.40),
]
data_50 = [
    ( 0,   -5, 50, 55, 2.30),
    (10,    5, 50, 55, 3.20),
    (25,   20, 50, 55, 4.00),
    (30,   35, 50, 55, 4.50),
]


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
        'lt25': Te_in <= 25,
        #'6_10': (Te_in >= 6) & (Te_in <= 10),
        'gt25': Te_in > 25
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

for region in ['lt25', 'gt25']:
    # Te range
    if region == 'lt25':
        x_vals = Te_range[Te_range < 25]
    elif region == 'gt25':
        x_vals = Te_range[(Te_range >= 25) #& (Te_range <= 10)
                          ]
    """ else:
        x_vals = Te_range[Te_range > 10] """

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
