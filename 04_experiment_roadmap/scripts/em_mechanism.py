"""
E-M 机制面板 + E-B3 + MW 桥（服务器端执行）

用法：
    ~/anaconda3/envs/torch39/bin/python em_mechanism.py 2024

输出（~/hzh_RSI/04_experiments/P1_mechanism/results/）：
    em_farmday_<year>.csv    逐场站-日：shrink / tax / floor_bind / b_obs / rmse_mw
    em_alpha_curve.csv       按 α 与品类聚合的 shrink / tax
    em_summary_<year>.json   关键数字

口径沿用 03_code/caliber_3y.py：
    PM = real_power（75-电站实际功率）
    PP = predict_power 且 data_source=='1'（81-短期预测功率表）
    Cap = filtered_56_farm.csv 的 capability，Cap>10
    d   = max(PM, α·Cap)，α=0.2
    一天有效点 >= 90
"""
import os
import sys
import json
import numpy as np
import pandas as pd

R = os.path.expanduser("~/0NWXM")
S = R + "/2原始数据/3Second_data"
OUT = os.path.expanduser("~/hzh_RSI/04_experiments/P1_mechanism/results")
ALPHAS = [0.10, 0.15, 0.20, 0.30, 0.50]


def load(year):
    cap = pd.read_csv(R + "/4处理后数据/filtered_56_farm.csv")
    cap.columns = [c.strip().lstrip("\ufeff") for c in cap.columns]
    cap["farm_id"] = cap["farm_id"].astype(str).str.strip()
    cap["Cap"] = pd.to_numeric(cap["capability"].astype(str).str.strip(" '"), errors="coerce")
    cap["kind"] = (cap["farm_no"].astype(str).str.strip(" '").str[:2]
                   .map({"EE": "W", "GF": "S"}).fillna("X"))
    cap = cap[cap.Cap > 10]

    real = pd.read_csv(
        S + "/75-电站实际功率%d-bs_data_real_fifteen_%d.csv" % (year, year),
        usecols=["farm_id", "data_time", "real_power"],
        dtype={"farm_id": str}, parse_dates=["data_time"])
    real["farm_id"] = real["farm_id"].str.strip()

    fc = pd.read_csv(
        S + "/81-短期预测功率表%d-bs_data_short_power_%d.csv" % (year, year),
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


def acc_of(pm, pp, d):
    r = (pp - pm) / d
    return 100.0 * (1.0 - np.sqrt(np.mean(r ** 2)))


def metrics(g, alphas):
    pm = g.PM.values.astype(float)
    pp = g.PP.values.astype(float)
    C = float(g.Cap.iloc[0])
    if len(pm) < 90:
        return None
    mu = pm.mean()
    row = dict(farm_id=g.farm_id.iloc[0], kind=g.kind.iloc[0], day=str(g.day.iloc[0].date()),
               cap=C, n=len(pm), pm_mean=mu,
               cf=mu / C if C > 0 else np.nan,
               floor_bind=float((pm < 0.2 * C).mean()),
               rmse_mw=float(np.sqrt(np.mean((pm - pp) ** 2))),
               b_obs=float((pp * pm).sum() / (pp ** 2).sum()) if (pp ** 2).sum() > 0 else np.nan)
    d = np.maximum(pm, 0.2 * C)
    row["acc_flo"] = acc_of(pm, pp, d)
    row["acc_cap"] = acc_of(pm, pp, np.full_like(pm, C))
    for a in alphas:
        da = np.maximum(pm, a * C)
        w = 1.0 / da ** 2
        mstar = (w * pm).sum() / w.sum()
        row["shrink_a%.2f" % a] = mstar / mu - 1.0
        row["tax_a%.2f" % a] = acc_of(pm, mstar, da) - acc_of(pm, mu, da)
    row["mstar"] = (1.0 / d ** 2 * pm).sum() / (1.0 / d ** 2).sum()
    row["shrink"] = row["shrink_a0.20"]
    row["tax"] = row["tax_a0.20"]
    return row


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    os.makedirs(OUT, exist_ok=True)
    print("[load] %d ..." % year, flush=True)
    m = load(year)
    print("[load] rows=%d farms=%d days=%d" % (len(m), m.farm_id.nunique(), m.day.nunique()), flush=True)

    rows = []
    for _, g in m.groupby(["farm_id", "day"], sort=False):
        r = metrics(g, ALPHAS)
        if r is not None:
            rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(OUT + "/em_farmday_%d.csv" % year, index=False, encoding="utf-8-sig")
    print("[out] farmday rows=%d" % len(df), flush=True)
    if "--farmday-only" in sys.argv:
        return

    # α 曲线：按品类聚合并做按日 block bootstrap 的 95% CI
    rec = []
    rng = np.random.default_rng(20261029)
    for a in ALPHAS:
        for kind in ["W", "S", "ALL"]:
            sub = df if kind == "ALL" else df[df.kind == kind]
            if len(sub) == 0:
                continue
            days = sub.day.unique()
            boot = []
            for _ in range(200):
                pick = rng.choice(days, len(days), replace=True)
                idx = np.concatenate([np.where(sub.day.values == dd)[0] for dd in pick])
                boot.append(sub["shrink_a%.2f" % a].values[idx].mean())
            rec.append(dict(alpha=a, kind=kind, n=len(sub),
                            shrink=float(sub["shrink_a%.2f" % a].mean()),
                            shrink_lo=float(np.percentile(boot, 2.5)),
                            shrink_hi=float(np.percentile(boot, 97.5)),
                            tax=float(sub["tax_a%.2f" % a].mean())))
    pd.DataFrame(rec).to_csv(OUT + "/em_alpha_curve_%d.csv" % year, index=False)

    def med(s):
        return float(np.median(s.dropna())) if len(s.dropna()) else float("nan")

    summ = dict(year=year, n_farmday=int(len(df)), n_farm=int(df.farm_id.nunique()),
                shrink_med=med(df.shrink), shrink_mean=float(df.shrink.mean()),
                tax_med=med(df.tax), tax_mean=float(df.tax.mean()),
                floor_bind_med=med(df.floor_bind), floor_bind_mean=float(df.floor_bind.mean()),
                b_obs_med=med(df.b_obs), b_obs_mean=float(df.b_obs.mean()),
                by_kind={k: dict(n=int(len(v)), shrink_med=med(v.shrink), tax_med=med(v.tax),
                                 floor_bind_mean=float(v.floor_bind.mean()),
                                 cf_mean=float(v.cf.mean()), b_obs_med=med(v.b_obs))
                         for k, v in df.groupby("kind")})
    with open(OUT + "/em_summary_%d.json" % year, "w") as f:
        json.dump(summ, f, indent=2, ensure_ascii=False)
    print(json.dumps(summ, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
