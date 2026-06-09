import pandas as pd
df = pd.read_csv('../data/abt/fake_account_abt.csv')
print("=== ftype value_counts ===")
print(df['ftype'].value_counts())
print("\n=== unique ftype values ===")
print(df['ftype'].unique())
