import pandas as pd

df_floating_pre = pd.read_csv('df_floating_preprocess.csv', encoding='UTF-8')
df_worker_pre = pd.read_csv('df_worker_preprocess.csv', encoding='UTF-8')
df_franchise_pre = pd.read_csv('df_franchise_preprocess.csv', encoding='UTF-8')
df_growth = pd.read_csv('df_growth.csv', encoding='UTF-8')

# 연도별 자치구 단위 병합
df_merge = (
    df_floating_pre
    .merge(df_worker_pre, on=['기준년도', '자치구명'])
    .merge(df_franchise_pre, on=['기준년도', '자치구명'])
)

# sh_closure_growth_ratio를 자치구명 기준으로 join (자치구별 고정값)
sh_ratio = df_growth[['자치구명', 'sh_closure_growth_ratio']]
df_merge = df_merge.merge(sh_ratio, on='자치구명', how='left')

print(df_merge.head())
print(f"\n연도 범위: {df_merge['기준년도'].min()} ~ {df_merge['기준년도'].max()}")
print(f"행 수: {len(df_merge)}")

df_merge.to_csv('data_merge.csv', index=False, encoding='utf-8')
print("\n✔ data_merge.csv 저장 완료")
