"""
E-D1：三段分解 L0 → L1 → L2 → L3

L0 = 场站 ACC 的简单平均
L1 = Σ λ_i ACC_i                （λ_i = Cap_i/ΣCap，容量加权）
L2 = 100(1 − RMS(Σ λ_i x_i))     （x_i = (PM_i−PP_i)/Cap_i，允许抵消，仍用 Cap 作分母）
L3 = 100(1 − RMS(Σ e_t / D_t))   （e_t = Σ(PM−PP)，D_t = max(ΣPM_t, 0.2ΣCap)，真实省级口径）

weight = L1−L0（权重）   A = L2−L1（抵消）   B = L3−L2（归一化）
gain   = L3−L0 = weight + A + B

用法：python em_decomp.py 2024
"""
import os
import sys
import json
import numpy as np
import pandas as pd

R = os.path.expanduser("~/0NWXM")
S = R + "/2原始数据/3Second_data"
OUT = os.path.expanduser("~/hzh_RSI/04_experiments/P1_mechanism/results")


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


def day_terms(g):
    """一天的三段分解（只用当日仍有 >=90 点的场站）"""
    piv = g.pivot_table(index="data_time", columns="farm_id", values=["PM", "PP"], aggfunc="sum")
    if piv.empty or piv.shape[0] < 90:
        return None
    pm = piv["PM"].dropna(axis=1)
    pp = piv["PP"].dropna(axis=1)
    common = pm.columns.intersection(pp.columns)
    pm, pp = pm[common], pp[common]
    if len(pm) < 90 or len(common) == 0:
        return None
    caps = g.groupby("farm_id").Cap.first().reindex(pm.columns)
    lam = caps / caps.sum()
    x = (pm - pp) / caps              # 每站归一化误差（分母恒为 Cap）
    agg = (x * lam).sum(axis=1)       # 容量加权合成误差
    L2 = 100 * (1 - np.sqrt(np.mean(agg.values ** 2)))
    E = (pm - pp).sum(axis=1).values
    PMs = pm.sum(axis=1).values
    D = np.maximum(PMs, 0.2 * caps.sum())
    L3 = 100 * (1 - np.sqrt(np.mean((E / D) ** 2)))
    acc = []
    for f in pm.columns:
        d = np.maximum(pm[f].values, 0.2 * caps[f])
        acc.append(100 * (1 - np.sqrt(np.mean(((pp[f].values - pm[f].values) / d) ** 2))))
    acc = np.array(acc)
    L0 = acc.mean()
    L1 = float((acc * lam.values).sum())
    return dict(day=str(pm.index[0].date()), n_farm=len(acc), L0=L0, L1=L1, L2=L2, L3=L3)


def summarise(d, year, kind, rng):
    n = len(d)
    ci = {}
    for col in ["weight", "A", "B", "gain"]:
        v = d[col].values
        bs = v[rng.integers(0, n, (2000, n))].mean(axis=1)
        ci[col] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    return dict(year=year, kind=kind, n_day=int(n),
                L0=float(d.L0.mean()), L1=float(d.L1.mean()),
                L2=float(d.L2.mean()), L3=float(d.L3.mean()),
                weight=float(d.weight.mean()), A=float(d.A.mean()),
                B=float(d.B.mean()), gain=float(d.gain.mean()),
                ci=ci,
                A_pos_share=float((d.A > 0).mean()),
                B_neg_share=float((d.B < 0).mean()))


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    m = load(year)
    rng = np.random.default_rng(20261029)
    frames, summary = [], {}
    for kind in ("ALL", "W", "S"):
        sub = m if kind == "ALL" else m[m.kind == kind]
        rows = []
        for day, g in sub.groupby("day", sort=True):
            r = day_terms(g)
            if r:
                r["year"] = year
                r["kind"] = kind
                rows.append(r)
        d = pd.DataFrame(rows)
        if not len(d):
            continue
        d["weight"] = d.L1 - d.L0
        d["A"] = d.L2 - d.L1
        d["B"] = d.L3 - d.L2
        d["gain"] = d.L3 - d.L0
        frames.append(d)
        summary[kind] = summarise(d, year, kind, rng)
        s = summary[kind]
        print("== E-D1（%d, %s） n_day=%d ==" % (year, kind, s["n_day"]))
        print("  L0 %.2f | L1 %.2f | L2 %.2f | L3 %.2f" % (s["L0"], s["L1"], s["L2"], s["L3"]))
        for col in ["weight", "A", "B", "gain"]:
            print("  %-6s %+7.2f  95%%CI [%+.2f, %+.2f]"
                  % (col, s[col], s["ci"][col][0], s["ci"][col][1]))

    D = pd.concat(frames, ignore_index=True)
    D.to_csv(OUT + "/ed_decomp_%d.csv" % year, index=False, encoding="utf-8-sig")

    out = dict(summary["ALL"])
    out["by_kind"] = {k: summary[k] for k in ("W", "S") if k in summary}
    json.dump(out, open(OUT + "/ed_decomp_%d.json" % year, "w"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
