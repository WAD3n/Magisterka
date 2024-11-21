import pandas as pd

predictionsFile = 'model_results.csv'
df = pd.read_csv(predictionsFile)
for row in df.itertuples(index=False):
    print(row)
