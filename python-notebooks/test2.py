import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('../data/activity_19473006788.csv')
df.head


def paceformat(pace_string):
    try: 
        parts = pace_string.split(':')
        return int(parts[0]) + int(parts[1])/60
    except (IndexError, ValueError):
        return None
    
def labelformat(pace_float):
    try:
        minutes = int(pace_float)
        seconds = int(round((pace_float-minutes)*60))
        return f"{minutes}:{seconds:02d}"
    except:
        return None

df['Formattedpace'] = df['Avg Pacemin/km'].apply(paceformat)

    

pace = df['Formattedpace'].iloc[:-1]
heartrate = df['Avg HRbpm'].iloc[:-1]
cadence = df['Avg Run Cadencespm'].iloc[:-1]

distance = df['Distancekm'].cumsum().iloc[:-1]

pace_np = pace.to_numpy()
heartrate_np = heartrate.to_numpy()
cadence_np = cadence.to_numpy()

distance_np = distance.to_numpy()

pace_np = np.insert(pace_np, 0, pace_np[0])
heartrate_np = np.insert(heartrate_np, 0, heartrate_np[0])
cadence_np = np.insert(cadence_np, 0, cadence_np[0])

distance_np = np.insert(distance_np, 0, 0)

fig, axs = plt.subplots(nrows=3, sharex=True)
fig.text(0.5, 0.04, 'Distance (km)', ha='center')

axs[0].step(distance_np, pace_np, where='pre')
axs[0].set_ylabel('Pace (min/km)')
axs[0].yaxis.set_inverted(True)

yticks = axs[0].get_yticks()
yticklabels = [labelformat(tick) for tick in yticks]
axs[0].set_yticklabels(yticklabels)

axs[1].step(distance_np, heartrate_np, where='pre')
axs[1].set_ylabel('Heart rate (bpm)')

axs[2].step(distance_np, cadence_np, where='pre')
axs[2].set_ylabel('Cadence (spm)')


