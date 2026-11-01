"""
E-B：行为面板（Δ 与安慰剂）

b*_cap = Σ PP·PM / Σ PP²                     （d ≡ Cap，权重为常数）
b*_flo = Σ w·PP·PM / Σ w·PP²,  w = 1/d²      （d = max(PM, 0.2Cap)）
Δ      = b*_flo − b*_cap                     （分母的净效应，扣除共同的衰减偏误）
安慰剂：把 d 在本站内随机置换，破坏"d 依赖 PM"，重算 Δ_plc（应≈0）

用法：python em_behavior.py 2024
"""
import os
import sys
import numpy as np
import pandas as pd

R = os.path.expanduser("~/0NWXM")
S = R + "/2原始数据/3Second_data"
OUT = os.path.expanduser("~/hzh_RSI/04_experiments/P1_mechanism/results")
NPLC = 20


def load(year):
    cap = pd.read_csv(R + "/4处理后数据/filtered_56_farm.csv")
    cap.columns = [c.strip().lstrip("\ufeff") for c in cap.columns]
    cap["farm_id"] = cap["farm_id"].astype(str).str.strip()
    cap["Cap"] = pd.to_numeric(cap["capability"].astype(str).str.strip(" '"), errors="coerce")
    cap["kind"] = (cap["farm_no"].astype(str).str.strip(" '").str[:2]
                   .map({"EE": "W", "GF": "S"}).fillna("X"))
    cap = cap[cap.Cap > 10]
    real = pd.read_csv(S + "/75-电站实际功率%d-bs_data_real_fifteen_%d.csv" % (year, year),
                       usecols=["farm_id", "data_time", "real_power"],
                       dtype={"farm_id": str}, parse_dates=["data_time"])
    real["farm_id"] = real["farm_id"].str.strip()
    fc = pd.read_csv(S + "/81-短期预测功率表%d-bs_data_short_power_%d.csv" % (year, year),
                     usecols=["farm_id", "data_time", "predict_power", "data_source"],
                     dtype={"farm_id": str, "data_source": str}, parse_dates=["data_time"])
    fc = fc[fc.data_source.str.strip() == "1"][["farm_id", "data_time", "predict_power"]]
    fc["farm_id"] = fc["farm_id"].str.strip()
    fc = fc.drop_duplicates(["farm_id", "data_time"])
    m = real.merge(fc, on=["farm_id", "data_time"], how="inner").merge(
        cap[["farm_id", "Cap", "kind"]], on="farm_id", how="inner")
    m["PM"] = pd.to_numeric(m.real_power, errors="coerce")
    m["PP"] = pd.to_numeric(m.predict_power, errors="coerce")
    m = m.dropna(subset=["PM", "PP"])
    m = m[m.PM >= 0]
    m["day"] = m.data_time.dt.normalize()
    return m


def one(g, rng):
    pm = g.PM.values.astype(float)
    pp = g.PP.values.astype(float)
    C = float(g.Cap.iloc[0])
    s2 = (pp ** 2).sum()
    if s2 <= 0 or pm.mean() <= 0:
        return None
    d = np.maximum(pm, 0.2 * C)
    w = 1.0 / d ** 2
    b_cap = (pp * pm).sum() / s2
    b_flo = (w * pp * pm).sum() / (w * pp ** 2).sum()
    # 安慰剂：本站内置换 d
    plc = []
    for _ in range(NPLC):
        dp = rng.permutation(d)
        wp = 1.0 / dp ** 2
        plc.append((wp * pp * pm).sum() / (wp * pp ** 2).sum())
    def acc(b):
        dd = np.maximum(pm, 0.2 * C)
        return 100 * (1 - np.sqrt(np.mean(((b * pp - pm) / dd) ** 2)))
    return dict(farm_id=g.farm_id.iloc[0], kind=g.kind.iloc[0], day=str(g.day.iloc[0].date()),
                cap=C, b_cap=b_cap, b_flo=b_flo, delta=b_flo - b_cap,
                delta_plc=float(np.mean(plc)) - b_cap, gain_pts=acc(b_flo) - acc(1.0))


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    m = load(year)
    rng = np.random.default_rng(20261029)
    rows = []
    for _, g in m.groupby(["farm_id", "day"], sort=False):
        if len(g) < 90:
            continue
        r = one(g, rng)
        if r:
            rows.append(r)
    d = pd.DataFrame(rows)
    d.to_csv(OUT + "/eb_behavior_%d.csv" % year, index=False, encoding="utf-8-sig")

    # 按日 cluster bootstrap
    days = d.day.unique()
    idx = {k: np.where(d.day.values == k)[0] for k in days}

    def boot_ci(col, n=2000):
        vals = []
        for _ in range(n):
            pick = rng.choice(days, len(days), replace=True)
            ii = np.concatenate([idx[k] for k in pick])
            vals.append(d[col].values[ii].mean())
        return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))

    print("== E-B（%d） n=%d ==" % (year, len(d)))
    for col in ["b_cap", "b_flo", "delta", "delta_plc", "gain_pts"]:
        print("  %-10s median %8.4f  mean %8.4f" % (col, d[col].median(), d[col].mean()))
    lo, hi = boot_ci("delta")
    print("  Δ 的 95%% CI: [%.4f, %.4f]" % (lo, hi))
    lo2, hi2 = boot_ci("delta_plc")
    print("  Δ_placebo 的 95%% CI: [%.4f, %.4f]" % (lo2, hi2))
    for k, g in d.groupby("kind"):
        print("  %s: Δ median %+.4f   Δ_plc median %+.4f   gain %.2f 分"
              % (k, g.delta.median(), g.delta_plc.median(), g.gain_pts.median()))


if __name__ == "__main__":
    main()
