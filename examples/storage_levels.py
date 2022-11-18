import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

time_index = range(0, 25, 3)

df = pd.DataFrame(
    index=time_index,
    data={
        "storage_level":
            [0.46, 0.32, 0.05, 0.14, 0.69, 0.48, 0.92, 0.61, 0.53]
    })

df["Y_3"] = np.minimum(np.floor(df["storage_level"]/0.3), np.full(9, 0.3))
df["Y_6"] = np.minimum(np.floor(df["storage_level"]/0.6), np.full(9, 0.6))
df["Y_9"] = np.minimum(np.floor(df["storage_level"]/0.9), np.full(9, 0.9))

plt.figure(tight_layout=True)

plt.step(df.index, df["Y_3"], linestyle="dotted", label="0.3 level active", lw=2)
plt.step(df.index, df["Y_6"], linestyle="dashed", label="0.6 level active", lw=2)
plt.step(df.index, df["Y_9"], linestyle="dashdot", label="0.9 level active", lw=2)
plt.plot(df["storage_level"], "k-", label="storage content", lw=2)

plt.grid()
plt.xlim(0, 24)
plt.xticks(time_index)
plt.ylim(0, 1)
plt.legend()
plt.xlabel("Time")
plt.ylabel("Storage content (normalised)\nor Level activity (if >0)")
plt.show()
