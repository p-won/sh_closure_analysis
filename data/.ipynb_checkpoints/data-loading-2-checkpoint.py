## 자치구별 유동인구, 직장인구 데이터 테이블 정리

import pandas as pd

df_floating = pd.read_csv('길단위인구-자치구.csv', encoding='UTF-8')
df_worker = pd.read_csv('직장인구-행정동.csv', encoding='UTF-8')
df_franchise = pd.read_csv('annual_franchise_ratio.csv', encoding='UTF-8')
df_rent = pd.read_csv('annual_rent.csv', encoding='UTF-8')


# 자치구별 유동인구 정리
df_floating.info()
print(df_floating.head())

df_floating_preprocess = df_floating.copy()

# 1. 2019 데이터 행 지우기
df_floating_preprocess['연도'] = df_floating_preprocess['기준_년분기_코드'] // 10
df_floating_preprocess = df_floating_preprocess[df_floating_preprocess['연도'] != 2019].drop('연도', axis=1)

# 2. 자치구_코드_명 → '자치구명' 이름 변경
df_floating_preprocess.rename(columns={'자치구_코드_명': '자치구명'}, inplace=True)

# 3. 기준_년분기_코드에서 연도 추출해서 '기준년도' 열 생성
df_floating_preprocess['기준년도'] = df_floating_preprocess['기준_년분기_코드'] // 10

# 4. 년도별 자치구별로 그룹화하여 분기 합산
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

# 5. 컬럼 순서 정렬
column_order = [
    '기준년도',
    '자치구명',
    '총_유동인구_수',
    '연령대_10_유동인구_수',
    '연령대_20_유동인구_수',
    '연령대_30_유동인구_수',
    '연령대_40_유동인구_수',
    '연령대_50_유동인구_수',
    '연령대_60_이상_유동인구_수'
]

df_floating_preprocess = df_floating_preprocess[column_order]

print(df_floating_preprocess.head())

df_floating_preprocess = df_floating_preprocess[~df_floating_preprocess['기준년도'].isin([2024, 2025])]

# csv로 저장
df_floating_preprocess.to_csv('df_floating_preprocess.csv', index=False, encoding='utf-8')



## 자치구별 직장인구 정리
df_worker.info()
print(df_worker.head())

import pandas as pd

# 자치구 코드 매핑 (행정동_코드 앞 4자리)
gu_mapping = {
    1111: '종로구',
    1114: '중구',
    1117: '용산구',
    1120: '성동구',
    1121: '광진구',
    1123: '동대문구',
    1126: '중랑구',
    1129: '성북구',
    1130: '강북구',
    1132: '도봉구',
    1135: '노원구',
    1138: '은평구',
    1141: '서대문구',
    1144: '마포구',
    1147: '양천구',
    1150: '강서구',
    1153: '구로구',
    1154: '금천구',
    1156: '영등포구',
    1159: '동작구',
    1162: '관악구',
    1165: '서초구',
    1168: '강남구',
    1171: '송파구',
    1174: '강동구',
}

df_worker_preprocess = df_worker.copy()

# 1. 2019 데이터 행 지우기
df_worker_preprocess['연도'] = df_worker_preprocess['기준_년분기_코드'] // 10
df_worker_preprocess = df_worker_preprocess[df_worker_preprocess['연도'] != 2019].drop('연도', axis=1)

# 2. 행정동_코드 앞 4자리로 자치구명 매핑
# 행정동_코드 // 10000 = 앞 4자리 추출
df_worker_preprocess['자치구_코드'] = (df_worker_preprocess['행정동_코드'] // 10000).astype(int)
df_worker_preprocess['자치구명'] = df_worker_preprocess['자치구_코드'].map(gu_mapping)

# 3. 기준년도 추출
df_worker_preprocess['기준년도'] = df_worker_preprocess['기준_년분기_코드'] // 10

# 같은 자치구끼리 sum으로 합산하고, 분기별 데이터는 mean으로 평균화
# 먼저 행정동별로 sum하고, 그 다음 자치구별로 mean 계산
groupby_cols = ['기준_년분기_코드', '자치구명']
agg_dict = {
    '총_직장_인구_수': 'sum',
    '연령대_10_직장_인구_수': 'sum',
    '연령대_20_직장_인구_수': 'sum',
    '연령대_30_직장_인구_수': 'sum',
    '연령대_40_직장_인구_수': 'sum',
    '연령대_50_직장_인구_수': 'sum',
    '연령대_60_이상_직장_인구_수': 'sum',
}

# 먼저 행정동을 자치구 단위로 합산
df_worker_preprocess = df_worker_preprocess.groupby(groupby_cols, as_index=False).agg(agg_dict)

# 그 다음 년도별로 분기를 mean으로 평균화
groupby_cols_final = ['기준년도', '자치구명']
df_worker_preprocess['기준년도'] = df_worker_preprocess['기준_년분기_코드'] // 10

agg_dict_final = {
    '총_직장_인구_수': 'mean',
    '연령대_10_직장_인구_수': 'mean',
    '연령대_20_직장_인구_수': 'mean',
    '연령대_30_직장_인구_수': 'mean',
    '연령대_40_직장_인구_수': 'mean',
    '연령대_50_직장_인구_수': 'mean',
    '연령대_60_이상_직장_인구_수': 'mean',
}

df_worker_preprocess = df_worker_preprocess.groupby(groupby_cols_final, as_index=False).agg(agg_dict_final)

# 평균값을 정수로 반올림
for col in ['총_직장_인구_수', '연령대_10_직장_인구_수', '연령대_20_직장_인구_수',
            '연령대_30_직장_인구_수', '연령대_40_직장_인구_수', '연령대_50_직장_인구_수',
            '연령대_60_이상_직장_인구_수']:
    df_worker_preprocess[col] = df_worker_preprocess[col].round().astype(int)

# 컬럼 순서 정렬
column_order = [
    '기준년도',
    '자치구명',
    '총_직장_인구_수',
    '연령대_10_직장_인구_수',
    '연령대_20_직장_인구_수',
    '연령대_30_직장_인구_수',
    '연령대_40_직장_인구_수',
    '연령대_50_직장_인구_수',
    '연령대_60_이상_직장_인구_수'
]

df_worker_preprocess = df_worker_preprocess[column_order]

df_worker_preprocess = df_worker_preprocess[ ~df_worker_preprocess['기준년도'].isin([2024, 2025])]

# CSV 저장
df_worker_preprocess.to_csv('df_worker_preprocess.csv', index=False, encoding='utf-8')


# 프랜차이즈 비율 데이터 형식 변환
df_franchise.info()
print(df_franchise.head(10))

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
df_franchise_preprocess.rename(columns={
    '자치구': '자치구명',
    '년도': '기준년도'
}, inplace=True)

df_franchise_preprocess['기준년도'] = df_franchise_preprocess['기준년도'].astype(int)
df_franchise_preprocess = df_franchise_preprocess[df_franchise_preprocess['기준년도'] >= 2020]

df_franchise_preprocess = df_franchise_preprocess[['기준년도', '자치구명', '전체점포수', '프랜차이즈비율(%)']].sort_values(['기준년도', '자치구명']).reset_index(drop=True)

df_franchise_preprocess.to_csv('df_franchise_preprocess.csv', index=False, encoding='utf-8')

print(df_franchise_preprocess.head(20))
print(f"\n행 수: {len(df_franchise_preprocess)}")


# 임대료 데이터 형식 변환
df_rent.info()
print(df_rent.head())

df_rent_preprocess = (
    df_rent.rename(columns={'자치구': '자치구명'})
      .melt(id_vars='자치구명', var_name='항목', value_name='임대료')
      .assign(
          기준년도=lambda x: x['항목'].str.extract(r'(\d{4})').astype(int),
          구분=lambda x: x['항목'].str.extract(r'_(.*)')
      )
      .query('기준년도 != 2019')
      .pivot(index=['기준년도', '자치구명'], columns='구분', values='임대료')
      .reset_index()
      .rename(columns={
          '전체': '전체 임대료',
          '1층': '1층 임대료',
          '1층외': '1층외 임대료'
      })
)

print(df_rent_preprocess.head())

df_rent_preprocess.to_csv('df_rent_preprocess.csv', index=False, encoding='utf-8')
print(df_rent_preprocess.head())