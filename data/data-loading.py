import pandas as pd

df_single_h = pd.read_csv('raw data/1인가구_연령별_2019_2024.csv', encoding='UTF-8')
df_all_h = pd.read_csv('raw data/상주인구-자치구-201901_202601.csv', encoding='UTF-8')
df_store = pd.read_csv('raw data/점포-자치구-201901_202601.csv', encoding='UTF-8')


# 1인가구 수 정리 (소계 컬럼 직접 사용)
df_single_h = df_single_h[df_single_h['자치구별(1)'] == '합계'][
    ['자치구별(2)', '시점', '소계']
].rename(columns={'자치구별(2)': '자치구명', '시점': '기준연도', '소계': '1인_가구_수'})

# 2025년 1인가구 추정 (직전 증가율 적용: 2023→2024 증가율)
df_2023 = df_single_h[df_single_h['기준연도'] == 2023].set_index('자치구명')['1인_가구_수']
df_2024 = df_single_h[df_single_h['기준연도'] == 2024].set_index('자치구명')['1인_가구_수']
growth_rate = (df_2024 / df_2023).reset_index()
growth_rate.columns = ['자치구명', 'growth_rate']

df_2025 = df_2024.reset_index()
df_2025.columns = ['자치구명', '1인_가구_수']
df_2025 = df_2025.merge(growth_rate, on='자치구명')
df_2025['1인_가구_수'] = (df_2025['1인_가구_수'] * df_2025['growth_rate']).round().astype(int)
df_2025['기준연도'] = 2025
df_2025 = df_2025[['자치구명', '기준연도', '1인_가구_수']]

df_single_h = pd.concat([df_single_h, df_2025], ignore_index=True)


# 전체가구 수 정리
df = df_all_h[['기준_년분기_코드', '자치구_코드_명', '총_가구_수']].copy()
df['기준연도'] = df['기준_년분기_코드'].astype(str).str[:4].astype(int)
df = df[(df['기준연도'] >= 2019) & (df['기준연도'] <= 2025)]
df = df.groupby(['자치구_코드_명', '기준연도'], as_index=False)['총_가구_수'].sum()


# 폐업 데이터 정리
target_stores = ['청과상','수산물판매','육류판매','미곡판매','주류도매','편의점','슈퍼마켓','커피-음료','호프-간이주점',
    '분식전문점','치킨전문점','패스트푸드점','제과점','양식음식점','일식음식점','중식음식점','한식음식점']

df_food = df_store[df_store['서비스_업종_코드_명'].isin(target_stores)][
    ['기준_년분기_코드', '자치구_코드_명', '전체_점포_수', '폐업_점포_수']].copy()
df_food['기준연도'] = df_food['기준_년분기_코드'].astype(str).str[:4].astype(int)
df_food = df_food[(df_food['기준연도'] >= 2019) & (df_food['기준연도'] <= 2025)]
df_food = df_food.groupby(['자치구_코드_명', '기준연도'], as_index=False).agg({
    '전체_점포_수': 'mean',
    '폐업_점포_수': 'sum'
})


# 데이터 병합
df = df.rename(columns={'자치구_코드_명': '자치구명'})
df = df.merge(df_single_h, on=['자치구명', '기준연도'], how='left')
df = df.merge(
    df_food.rename(columns={'자치구_코드_명': '자치구명', '전체_점포_수': '점포_수'}),
    on=['자치구명', '기준연도'], how='left'
)


# 1인가구 증가에 따른 폐업률 계산
df_growth = df.copy()
df_growth = df_growth.sort_values(['자치구명', '기준연도'])

df_growth['1인가구_비중'] = df_growth['1인_가구_수'] / df_growth['총_가구_수']
df_growth['1인가구비중_증가율'] = df_growth.groupby('자치구명')['1인가구_비중'].pct_change()
df_growth['폐업_증가율'] = df_growth.groupby('자치구명')['폐업_점포_수'].pct_change()
df_growth['sh_closure_growth_ratio'] = (
    df_growth['폐업_증가율'] / df_growth['1인가구비중_증가율']
)

df_growth = df_growth[df_growth['기준연도'] != 2019]
df_growth = df_growth.drop(columns='기준연도').groupby('자치구명', as_index=False).mean()

print("======1인 가구 증가에 따른 폐업률 보기=======")
print(df_growth[['자치구명', 'sh_closure_growth_ratio']].sort_values(by='sh_closure_growth_ratio', ascending=False))

df_growth.to_csv('df_growth.csv', index=False, encoding='utf-8')
print("\n✔ df_growth.csv 저장 완료")
