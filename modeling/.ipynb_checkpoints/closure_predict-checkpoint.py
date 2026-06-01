import pandas as pd
import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

# 데이터 로드
df_growth = pd.read_csv('../data/df_growth_year.csv')
df_merge = pd.read_csv('../data/df_merge_ver.csv')

# 필요한 컬럼만 추출 후 조인
df_growth = df_growth[['자치구명', '기준연도', 'sh_closure_growth_ratio']]
df_merge = df_merge.rename(columns={'기준년도': '기준연도'})
df = df_merge.merge(df_growth, on=['자치구명', '기준연도'], how='inner')

print(f"병합 결과: {df.shape[0]}행, {df.shape[1]}열")

# 연령대 비율 피처 생성
df['20대_유동_비율'] = df['연령대_20_유동인구_수'] / df['총_유동인구_수']
df['30대_유동_비율'] = df['연령대_30_유동인구_수'] / df['총_유동인구_수']
df['40대_유동_비율'] = df['연령대_40_유동인구_수'] / df['총_유동인구_수']
df['50대_유동_비율'] = df['연령대_50_유동인구_수'] / df['총_유동인구_수']
df['60대이상_유동_비율'] = df['연령대_60_이상_유동인구_수'] / df['총_유동인구_수']
df['20대_직장_비율'] = df['연령대_20_직장_인구_수'] / df['총_직장_인구_수']
df['30대_직장_비율'] = df['연령대_30_직장_인구_수'] / df['총_직장_인구_수']
df['40대_직장_비율'] = df['연령대_40_직장_인구_수'] / df['총_직장_인구_수']
df['50대_직장_비율'] = df['연령대_50_직장_인구_수'] / df['총_직장_인구_수']
df['60대이상_직장_비율'] = df['연령대_60_이상_직장_인구_수'] / df['총_직장_인구_수']

feature_cols = [
    '총_유동인구_수', '총_직장_인구_수',
    '20대_유동_비율', '30대_유동_비율', '40대_유동_비율', '50대_유동_비율', '60대이상_유동_비율',
    '20대_직장_비율', '30대_직장_비율', '40대_직장_비율', '50대_직장_비율', '60대이상_직장_비율',
    '1층 임대료', '1층외 임대료', '전체점포수', '프랜차이즈비율(%)'
]

df_model = df[feature_cols + ['sh_closure_growth_ratio']].dropna()
X = df_model[feature_cols]
y = df_model['sh_closure_growth_ratio']

# 표준화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Ridge 회귀 (alpha는 CV로 자동 선택)
alphas = np.logspace(-3, 5, 100)
model = RidgeCV(alphas=alphas, cv=5)
model.fit(X_scaled, y)
y_pred = model.predict(X_scaled)

print(f"\n최적 alpha = {model.alpha_:.4f}")
print(f"R² = {r2_score(y, y_pred):.4f}")
print(f"절편 = {model.intercept_:.4f}")

# 표준화 계수 (변수 영향력 비교)
coef_df = pd.DataFrame({
    '변수': feature_cols,
    '표준화_계수': model.coef_
})
coef_df['절대값'] = coef_df['표준화_계수'].abs()
coef_df = coef_df.sort_values('절대값', ascending=False).reset_index(drop=True)

print("\n======= Ridge 회귀 계수 (영향력 순) =======")
print(coef_df[['변수', '표준화_계수']].to_string(index=False))
