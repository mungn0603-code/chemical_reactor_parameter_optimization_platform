"""eda/sample.py — 데모용 반응기 데이터셋 생성.

EDA Assistant 를 바로 체험할 수 있도록, 실제 계산 엔진(CSTR)을 이용해 온도·압력을
스윕한 합성 데이터셋을 만든다. 일부 결측치·중복·이상치를 일부러 섞어 전처리 기능을
시연할 수 있게 한다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_sample_dataset(n: int = 120, seed: int = 7) -> pd.DataFrame:
    """반응기 운전 데이터를 흉내 낸 데모 데이터프레임을 만든다.

    계산 엔진을 실제로 호출하되, 실패해도 되도록 순수 수식 근사로 폴백한다.
    """
    rng = np.random.default_rng(seed)
    temps = rng.uniform(40, 120, n)          # °C
    pressures = rng.uniform(1, 10, n)        # bar
    residence = rng.uniform(30, 300, n)      # s
    ea = rng.normal(50, 3, n)                # kJ/mol

    # Arrhenius 근사로 전환율 계산(엔진과 무관한 데모용 근사).
    R = 8.314
    A = 1e6
    k = A * np.exp(-(ea * 1000) / (R * (temps + 273.15)))
    x = 1 - 1 / (1 + k * residence)          # 0~1 범위 근사
    x = np.clip(x + rng.normal(0, 0.02, n), 0, 1)
    yield_ = np.clip(x * rng.uniform(0.85, 0.98, n), 0, 1)
    profit = x * pressures * 1000 - residence * 2 + rng.normal(0, 50, n)

    catalyst = rng.choice(["Pt", "Pd", "Ni"], n)

    df = pd.DataFrame({
        "Temperature": np.round(temps, 2),
        "Pressure": np.round(pressures, 2),
        "ResidenceTime": np.round(residence, 1),
        "ActivationEnergy": np.round(ea, 2),
        "Conversion": np.round(x, 4),
        "Yield": np.round(yield_, 4),
        "Profit": np.round(profit, 1),
        "Catalyst": catalyst,
    })

    # 전처리 시연을 위해 일부러 흠집을 낸다.
    miss_idx = rng.choice(n, size=max(1, n // 25), replace=False)
    df.loc[miss_idx, "Temperature"] = np.nan
    # 이상치 몇 개 주입.
    out_idx = rng.choice(n, size=3, replace=False)
    df.loc[out_idx, "Pressure"] = df["Pressure"].max() * 5
    # 중복행 몇 개.
    df = pd.concat([df, df.iloc[:3]], ignore_index=True)

    return df
