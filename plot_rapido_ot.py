import matplotlib.pyplot as plt
import glob
import sys
import pandas as pd

try:
    ext = sys.argv[1]
except:
    ext = 'txt'

for file in glob.glob(f'./OTs/*{ext}'):
    df = pd.read_csv(file, sep=';', decimal=',')
    fig, ax = plt.subplots(1, 1)
    ax.plot(df['Tau'], df["G'"])
    ax.plot(df['Tau'], df["G''"])
    ax.set(xscale='log', yscale='log', title=file)
    fig.savefig(file[:-4] + '.png')
