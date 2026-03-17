import pandas as pd

pop_df = pd.read_csv('../data/population/bgd_admpop_adm2_2022.csv')
print(pop_df.columns.tolist())
print(pop_df.head(3))