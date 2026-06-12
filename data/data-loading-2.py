import pandas as pd

df_floating = pd.read_csv('raw data/길단위인구-자치구-201901_202601.csv', encoding='UTF-8')
df_worker = pd.read_csv('raw data/직장인구-행정동-201901_202601.csv', encoding='UTF-8')
df_franchise = pd.read_csv('raw data/annual_franchise_ratio.csv', encoding='UTF-8')


# 자치구별 유동인구 정리
df_floating_preprocess = df_floating.copy()

df_floating_preprocess['연도'] = df_floating_preprocess['기준_년분기_코드'] // 10
df_floating_preprocess = df_floating_preprocess[df_floating_preprocess['연도'] != 2019].drop('연도', axis=1)

df_floating_preprocess.rename(columns={'자치구_코드_명': '자치구명'}, inplace=True)
df_floating_preprocess['기준년도'] = df_floating_preprocess['기준_년분기_코드'] // 10

groupby_cols = ['기준년도', '자치구_코드', '자치구명']
agg_dict = {
    '총_유동인구_수': 'sum',
    '연령대_10_유동인구_수': 'sum',
    '연령대_20_유동인구_수': 'sum',
    '연령대_30_유동인구_수': 'sum',
    '연령대_40_유동인구_수': 'sum',
    '연령대_50_유동인구_수': 'sum',
    '연령대_60_이상_유동인구_수': 'sum'
}
df_floating_preprocess = df_floating_preprocess.groupby(groupby_cols, as_index=False).agg(agg_dict)

column_order = [
    '기준년도', '자치구명', '총_유동인구_수',
    '연령대_10_유동인구_수', '연령대_20_유동인구_수', '연령대_30_유동인구_수',
    '연령대_40_유동인구_수', '연령대_50_유동인구_수', '연령대_60_이상_유동인구_수'
]
df_floating_preprocess = df_floating_preprocess[column_order]

# 2025년까지 포함 (2026년 제외)
df_floating_preprocess = df_floating_preprocess[df_floating_preprocess['기준년도'] <= 2025]

df_floating_preprocess.to_csv('df_floating_preprocess.csv', index=False, encoding='utf-8')
print("✔ df_floating_preprocess.csv 저장 완료")


# 자치구별 직장인구 정리
gu_mapping = {
    1111: '종로구', 1114: '중구', 1117: '용산구', 1120: '성동구',
    1121: '광진구', 1123: '동대문구', 1126: '중랑구', 1129: '성북구',
    1130: '강북구', 1132: '도봉구', 1135: '노원구', 1138: '은평구',
    1141: '서대문구', 1144: '마포구', 1147: '양천구', 1150: '강서구',
    1153: '구로구', 1154: '금천구', 1156: '영등포구', 1159: '동작구',
    1162: '관악구', 1165: '서초구', 1168: '강남구', 1171: '송파구',
    1174: '강동구',
}

df_worker_preprocess = df_worker.copy()

df_worker_preprocess['연도'] = df_worker_preprocess['기준_년분기_코드'] // 10
df_worker_preprocess = df_worker_preprocess[df_worker_preprocess['연도'] != 2019].drop('연도', axis=1)

df_worker_preprocess['자치구_코드'] = (df_worker_preprocess['행정동_코드'] // 10000).astype(int)
df_worker_preprocess['자치구명'] = df_worker_preprocess['자치구_코드'].map(gu_mapping)
df_worker_preprocess['기준년도'] = df_worker_preprocess['기준_년분기_코드'] // 10

agg_dict = {
    '총_직장_인구_수': 'sum', '연령대_10_직장_인구_수': 'sum',
    '연령대_20_직장_인구_수': 'sum', '연령대_30_직장_인구_수': 'sum',
    '연령대_40_직장_인구_수': 'sum', '연령대_50_직장_인구_수': 'sum',
    '연령대_60_이상_직장_인구_수': 'sum',
}
df_worker_preprocess = df_worker_preprocess.groupby(['기준_년분기_코드', '자치구명'], as_index=False).agg(agg_dict)

df_worker_preprocess['기준년도'] = df_worker_preprocess['기준_년분기_코드'] // 10

agg_dict_final = {
    '총_직장_인구_수': 'mean', '연령대_10_직장_인구_수': 'mean',
    '연령대_20_직장_인구_수': 'mean', '연령대_30_직장_인구_수': 'mean',
    '연령대_40_직장_인구_수': 'mean', '연령대_50_직장_인구_수': 'mean',
    '연령대_60_이상_직장_인구_수': 'mean',
}
df_worker_preprocess = df_worker_preprocess.groupby(['기준년도', '자치구명'], as_index=False).agg(agg_dict_final)

for col in ['총_직장_인구_수', '연령대_10_직장_인구_수', '연령대_20_직장_인구_수',
            '연령대_30_직장_인구_수', '연령대_40_직장_인구_수', '연령대_50_직장_인구_수',
            '연령대_60_이상_직장_인구_수']:
    df_worker_preprocess[col] = df_worker_preprocess[col].round().astype(int)

column_order = [
    '기준년도', '자치구명', '총_직장_인구_수',
    '연령대_10_직장_인구_수', '연령대_20_직장_인구_수', '연령대_30_직장_인구_수',
    '연령대_40_직장_인구_수', '연령대_50_직장_인구_수', '연령대_60_이상_직장_인구_수'
]
df_worker_preprocess = df_worker_preprocess[column_order]

# 2025년까지 포함 (2026년 제외)
df_worker_preprocess = df_worker_preprocess[df_worker_preprocess['기준년도'] <= 2025]

df_worker_preprocess.to_csv('df_worker_preprocess.csv', index=False, encoding='utf-8')
print("✔ df_worker_preprocess.csv 저장 완료")


# 프랜차이즈 비율 데이터 형식 변환
df_franchise_preprocess = df_franchise.melt(
    id_vars=['자치구'],
    var_name='year_column',
    value_name='value'
)

df_franchise_preprocess[['년도', '지표']] = df_franchise_preprocess['year_column'].str.extract(r'(\d{4})년_(.+)')

df_franchise_preprocess = df_franchise_preprocess.pivot_table(
    index=['자치구', '년도'],
    columns='지표',
    values='value',
    aggfunc='first'
).reset_index()

df_franchise_preprocess.columns.name = None
df_franchise_preprocess.rename(columns={'자치구': '자치구명', '년도': '기준년도'}, inplace=True)
df_franchise_preprocess['기준년도'] = df_franchise_preprocess['기준년도'].astype(int)
df_franchise_preprocess = df_franchise_preprocess[df_franchise_preprocess['기준년도'] >= 2020]

df_franchise_preprocess = df_franchise_preprocess[
    ['기준년도', '자치구명', '전체점포수', '프랜차이즈비율(%)']
].sort_values(['기준년도', '자치구명']).reset_index(drop=True)

df_franchise_preprocess.to_csv('df_franchise_preprocess.csv', index=False, encoding='utf-8')
print("✔ df_franchise_preprocess.csv 저장 완료")
print(f"  연도 범위: {df_franchise_preprocess['기준년도'].min()} ~ {df_franchise_preprocess['기준년도'].max()}")
