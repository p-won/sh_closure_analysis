## 테이블 병합

import pandas as pd

df_floating_pre = pd.read_csv('df_floating_preprocess.csv', encoding='UTF-8')
df_worker_pre = pd.read_csv('df_worker_preprocess.csv', encoding='UTF-8')
df_rent_pre = pd.read_csv('df_rent_preprocess.csv', encoding='UTF-8')
df_franchise_pre = pd.read_csv('df_franchise_preprocess.csv', encoding='UTF-8')
# df_growth = pd.read_csv('df_growth.csv', encoding='UTF-8')


print(df_floating_pre.info)
print(df_worker_pre.info)
print(df_rent_pre.info)
print(df_franchise_pre.info)
# print(df_growth.info)

# 병합
df_merge_ver = (
    df_floating_pre
    .merge(df_worker_pre, on=['기준년도', '자치구명'])
    .merge(df_rent_pre, on=['기준년도', '자치구명'])
    .merge(df_franchise_pre, on=['기준년도', '자치구명'])
)

print(df_merge_ver.head())

# 영역_면적_평균 추가 (관광특구 제외, 25개 구 기준)
df_area = pd.read_csv('seoul_commercial_area_by_gu.csv', encoding='UTF-8-sig')
df_area = df_area[~df_area['구명'].str.contains('관광특구')][['구명', '영역_면적_평균']]
df_area = df_area.rename(columns={'구명': '자치구명'})
df_merge_ver = df_merge_ver.merge(df_area, on='자치구명', how='left')

df_merge_ver.to_csv('df_merge_ver.csv', index=False, encoding='utf-8')
