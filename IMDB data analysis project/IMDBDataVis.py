import pandas as pd
import numpy as np
import plotly.express as px


# read csv data
df = pd.read_csv('IMDB_top1000.csv')

# x-axis; a measure of Movie Male/Female voter demographic, relative to IMDB demographic (more M voters on IMDB)
# np.log() produces a more linear relationship
dataColSum = df.sum()
imdbDemographic = dataColSum[13]/dataColSum[14]
df['Normalized M F movie demographic (ln((Votes_M/Votes_F)/4.69))'] = np.log((df['Votes_M']/df['Votes_F'])/imdbDemographic)

# y-axis; relative Male/Female vote ratio
# np.log() produces a more linear relationship
df['M F rating bias (ln(AvgRating_M/AvgRating_F)'] = np.log((df['AvgRating_M']/df['AvgRating_F']))

df['Avg. movie rating'] = (df['Votes_10']*10 + df['Votes_9']*9 + df['Votes_8']*8 + df['Votes_7']*7 + df['Votes_6']*6 + df['Votes_5']*5 + df['Votes_4']*4 + df['Votes_3']*3 + df['Votes_2']*2 + df['Votes_1'])/(df['Votes_10'] + df['Votes_9'] + df['Votes_8'] + df['Votes_7'] + df['Votes_6'] + df['Votes_5'] + df['Votes_4'] + df['Votes_3'] + df['Votes_2'] + df['Votes_1'])

fig1 = px.scatter(df, x="Normalized M F movie demographic (ln((Votes_M/Votes_F)/4.69))", y="M F rating bias (ln(AvgRating_M/AvgRating_F)", hover_data=['Title','Rank'])
fig1.show()

#fig2 uses total vote average as y-axis
fig2 = px.scatter(df, x="Normalized M F movie demographic (ln((Votes_M/Votes_F)/4.69))", y="Avg. movie rating", hover_data=['Title','Rank'])
fig2.show()