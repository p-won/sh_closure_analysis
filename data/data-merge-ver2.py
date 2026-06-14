import pandas as pd

df_merge = pd.read_csv('data_merge.csv', encoding='utf-8')
df_yearly = pd.read_csv('df_growth_yearly.csv', encoding='utf-8-sig')

df_yearly['closure'] = df_yearly['폐업_점포_수'] / df_yearly['점포_수']
df_closure = df_yearly[['기준연도', '자치구명', 'closure']].rename(columns={'기준연도': '기준년도'})

df_v2 = df_merge.drop(columns='sh_closure_growth_ratio')
df_v2 = df_v2.merge(df_closure, on=['기준년도', '자치구명'], how='left')

df_v2.to_csv('data_merge_ver2.csv', index=False, encoding='utf-8-sig')
print(f"✔ data_merge_ver2.csv 저장 완료 ({df_v2.shape[0]}행 x {df_v2.shape[1]}열)")
