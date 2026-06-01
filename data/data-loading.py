import pandas as pd

df_single_h = pd.read_csv('raw data/1인가구_성별_연령.csv', encoding='UTF-8')
df_all_h = pd.read_csv('raw data/상주인구_자치구.csv', encoding='UTF-8')
df_store = pd.read_csv('raw data/점포_자치구.csv', encoding='UTF-8')


# 1인가구 비율 계산 = (5년 평균 1인가구 수 / 5년 평균 전체가구 수)

# 1인가구 수 계산
# print(df_single_h.head())
df_single_h = df_single_h.groupby(['자치구명', '기준연도'], as_index=False).sum(numeric_only=True)
df_single_h['sum_all_ages'] = df_single_h.iloc[:, 2:].sum(axis=1)
# print(df_single_h.head(20))

# 전체가구 수 계산
# print(df_all_h.info())
# 필요한 컬럼만 선택
df = df_all_h[
    ['기준_년분기_코드', '자치구_코드_명', '총_가구_수']].copy()
# 연도 컬럼 생성
df['기준연도'] = (df['기준_년분기_코드'].astype(str).str[:4].astype(int))
# 2019 ~ 2023만 필터링
df = df[(df['기준연도'] >= 2019) &(df['기준연도'] <= 2023)]
# 자치구 + 연도 기준으로 분기 평균 (분기 합산 시 4배 오류 방지)
df = (df.groupby(['자치구_코드_명', '기준연도'], as_index=False)['총_가구_수'].mean())
# print(df.head(20))


# 페업 비율 계산 = (5년 평균 폐업점포 수 / 5년 평균 전체점포 수)
# print(df_store.info())
# print(df_store['서비스_업종_코드_명'].unique())

target_stores = ['커피-음료','호프-간이주점','분식전문점','치킨전문점','패스트푸드점','제과점','양식음식점','일식음식점','중식음식점','한식음식점']
# 필요한 업종 + 컬럼만 선택
df_food = df_store[df_store['서비스_업종_코드_명'].isin(target_stores)][
    ['기준_년분기_코드','자치구_코드_명','점포_수','폐업_점포_수']].copy()
# 연도 추출
df_food['기준연도'] = (df_food['기준_년분기_코드'].astype(str).str[:4].astype(int))
# 2019~2023 필터링
df_food = df_food[(df_food['기준연도'] >= 2019) &(df_food['기준연도'] <= 2023)]
# 연 단위 집계
df_food = (df_food.groupby(['자치구_코드_명', '기준연도'], as_index=False)
    .agg({
        '점포_수': 'mean',
        '폐업_점포_수': 'sum'
    }))

# 데이터 병합

# 1인 가구 수만 추출 + 컬럼명 변경
df_single_merge = df_single_h[['자치구명', '기준연도', 'sum_all_ages']].rename(columns={'sum_all_ages': '1인_가구_수'})
# df_food 필요한 컬럼만
df_food_merge = df_food[['자치구_코드_명', '기준연도', '점포_수', '폐업_점포_수']]
# df 컬럼명 통일
df = df.rename(columns={'자치구_코드_명': '자치구명'})
# 1인 가구 merge
df = df.merge(df_single_merge,on=['자치구명', '기준연도'],how='left')
# 음식업 데이터 merge
df = df.merge(df_food_merge.rename(columns={'자치구_코드_명': '자치구명'}),on=['자치구명', '기준연도'],how='left')


# 1인가구 대비 폐업률 계산
df_mean = (df.drop(columns='기준연도').groupby('자치구명', as_index=False).mean())
print(df_mean.head(30))

df_mean['sh_closure_ratio'] = (
    (df_mean['폐업_점포_수'] / df_mean['점포_수']) /
    (df_mean['1인_가구_수'] / df_mean['총_가구_수']))

print("======1인가구 대비 폐업률 보기=======")
print(df_mean[['자치구명', 'sh_closure_ratio']].sort_values(by='sh_closure_ratio',ascending=False))



# 그 해 비율 계산 (전년도 대비 아님)

df_byyear = df.copy()
df_byyear = df_byyear.sort_values(['자치구명', '기준연도'])

# 2020~2023만 (df_merge_ver.csv와 맞춤)
df_byyear = df_byyear[df_byyear['기준연도'] >= 2020]

# 1인가구비율 = 1인가구수 / 전체가구수
df_byyear['1인가구비율'] = df_byyear['1인_가구_수'] / df_byyear['총_가구_수']

# 폐업점포비율 = 폐업점포수 / 전체점포수
df_byyear['폐업점포비율'] = df_byyear['폐업_점포_수'] / df_byyear['점포_수']

print("======그 해 비율 보기 (25구 x 4년 = 100행)=======")
print(df_byyear[['자치구명', '기준연도', '1인가구비율', '폐업점포비율']].head(20))

# 년도별 행 저장 (25구 x 4년 = 100행)
df_byyear[['자치구명', '기준연도', '1인가구비율', '폐업점포비율']].to_csv('df_growth_byyear.csv', index=False, encoding='utf-8')
