"""
E-M5：分数权重按出力分位的分布

回答：地板化功能归一下，高分位出力的误差被"计价"了多少？
用法：python em_weights.py 2024
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
R = os.path.expanduser("~/0NWXM")
S = R + "/2原始数据/3Second_data"
OUT = os.path.expanduser("~/hzh_RSI/04_experiments/P1_mechanism/results")
EDGES = np.array([0, .02, .05, .1, .15, .2, .3, .4, .5, .6, .7, .8, .9, 1.01])


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
    m = real.merge(cap[["farm_id", "Cap", "kind"]], on="farm_id", how="inner")
    m["PM"] = pd.to_numeric(m.real_power, errors="coerce")
    m = m.dropna(subset=["PM"])
    m = m[m.PM >= 0]
    return m


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    m = load(year)
    cf = (m.PM / m.Cap).values
    d = np.maximum(m.PM.values, 0.2 * m.Cap.values)
    w = 1.0 / d ** 2
    idx = np.clip(np.digitize(cf, EDGES) - 1, 0, len(EDGES) - 2)
    k = m.kind.values

    rows = []
    for kind in ["W", "S", "ALL"]:
        sel = np.ones(len(m), bool) if kind == "ALL" else (k == kind)
        wt = w[sel]
        share_w = wt / wt.sum()
        ii = idx[sel]
        for b in range(len(EDGES) - 1):
            mk = ii == b
            if mk.sum() == 0:
                continue
            rows.append(dict(kind=kind, lo=EDGES[b], hi=EDGES[b + 1],
                             n=int(mk.sum()), n_share=float(mk.mean()),
                             w_share=float(share_w[mk].sum()),
                             mean_error_cost=float(share_w[mk].sum() / mk.mean())))
    df = pd.DataFrame(rows)
    df.to_csv(OUT + "/em_weight_share_%d.csv" % year, index=False, encoding="utf-8-sig")
    for kind in ["W", "S"]:
        sub = df[df.kind == kind]
        top = sub[sub.lo >= 0.5]
        print("%s: intervals>=0.5CF share=%.1f%%  weight share=%.1f%%"
              % (kind, 100 * top.n_share.sum(), 100 * top.w_share.sum()))
        print("   <=0.2CF: share=%.1f%%  weight share=%.1f%%"
              % (100 * sub[sub.hi <= 0.2].n_share.sum(), 100 * sub[sub.hi <= 0.2].w_share.sum()))
    print(df[df.kind == "ALL"].to_string(index=False))


if __name__ == "__main__":
    main()
