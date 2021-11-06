import numpy as np
import matplotlib.pyplot as plt

normal_ratings = np.loadtxt("ratings_normal.csv", dtype=np.int16, delimiter=",", skiprows=1)

cheater_ratings = np.loadtxt("ratings_cheat.csv", dtype=np.int16, delimiter=",", skiprows=1)

classical_rapid_deltas = (normal_ratings[:,0]-normal_ratings[:,3])
classical_rapid_deltas_cheat = (cheater_ratings[:,0]-cheater_ratings[:,3])

classical_blitz_deltas = (normal_ratings[:,0]-normal_ratings[:,6])
classical_blitz_deltas_cheat = (cheater_ratings[:,0]-cheater_ratings[:,6])

_ = plt.hist(classical_rapid_deltas_cheat, bins=range(-300,300,60))  # arguments are passed to np.histogram

plt.title("Rating deltas classical-rapid cheating players. Bin size 20")
plt.savefig("cheaters.png")

_ = plt.hist(classical_rapid_deltas, bins=range(-300,320,60))  # arguments are passed to np.histogram

plt.title("Rating deltas classical-rapid unmarked players. Bin size 20")
plt.savefig("unmarked.png")

