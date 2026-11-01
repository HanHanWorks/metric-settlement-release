"""
E-M 聚合：读 em_farmday_<year>.csv，出 α 曲线 + 摘要（按日 cluster bootstrap）

用法：python em_aggregate.py 2024
"""
import os
import sys
import json
import numpy as np
import pandas as pd

OUT = os.path.expanduser("~/hzh_RSI/04_experiments/P1_mechanism/results")
ALPHAS = [0.10, 0.15, 0.20, 0.30, 0.50]
BOOT = 2000
SEED = 20261029


def cluster_boot_ci(day_mean, rng, boot=BOOT):
    v = day_mean.values
    n = len(v)
    if n < 5:
        return (np.nan, np.nan)
    idx = rng.integers(0, n, size=(boot, n))
    m = v[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    df = pd.read_csv(OUT + "/em_farmday_%d.csv" % year)
    df["day"] = df.day.astype(str)
    n0 = len(df)

    # 剔除 pm_mean<=0（全天零出力，shrink 无定义）
    zero = df[df.pm_mean <= 1e-9]
    df = df[df.pm_mean > 1e-9].copy()
    # 剔除容量因子异常低的日子（<0.5%）：这些日子 m* 的分母几乎全是地板，数值上不稳定
    df = df[df.cf > 0.005].copy()

    rng = np.random.default_rng(SEED)
    rec = []
    for a in ALPHAS:
        col, tcol = "shrink_a%.2f" % a, "tax_a%.2f" % a
        for kind in ["W", "S", "ALL"]:
            sub = df if kind == "ALL" else df[df.kind == kind]
            sub = sub.dropna(subset=[col])
            if len(sub) < 100:
                continue
            dm = sub.groupby("day")[col].mean()
            lo, hi = cluster_boot_ci(dm, rng)
            rec.append(dict(alpha=a, kind=kind, n=len(sub), n_day=int(len(dm)),
                            shrink=float(sub[col].mean()), lo=lo, hi=hi,
                            tax=float(sub[tcol].mean()),
                            floor_bind=float(sub.floor_bind.mean())))
    cur = pd.DataFrame(rec)
    cur.to_csv(OUT + "/em_alpha_curve_%d.csv" % year, index=False, encoding="utf-8-sig")

    def med(x):
        x = x.dropna()
        return float(np.median(x)) if len(x) else float("nan")

    summ = dict(year=year, n_farmday_raw=int(n0), n_farmday=int(len(df)),
                dropped_zero=int(len(zero)), dropped_lowcf=int(len(zero)) * 0 + int(n0 - len(zero) - len(df)),
                n_farm=int(df.farm_id.nunique()), n_day=int(df.day.nunique()),
                shrink_med=med(df.shrink), shrink_mean=float(df.shrink.mean()),
                tax_med=med(df.tax), tax_mean=float(df.tax.mean()),
                floor_bind_med=med(df.floor_bind), floor_bind_mean=float(df.floor_bind.mean()),
                b_obs_med=med(df.b_obs), b_obs_mean=float(df.b_obs.mean()),
                rmse_over_cap_med=med(df.rmse_mw / df.cap),
                by_kind={k: dict(n=int(len(v)), shrink_med=med(v.shrink), shrink_mean=float(v.shrink.mean()),
                                 tax_med=med(v.tax), tax_mean=float(v.tax.mean()),
                                 floor_bind_mean=float(v.floor_bind.mean()),
                                 cf_mean=float(v.cf.mean()), b_obs_med=med(v.b_obs),
                                 acc_flo_mean=float(v.acc_flo.mean()))
                         for k, v in df.groupby("kind")})
    with open(OUT + "/em_summary_%d.json" % year, "w") as f:
        json.dump(summ, f, indent=2, ensure_ascii=False)
    print(json.dumps(summ, indent=2, ensure_ascii=False))
    print("\n== alpha curve ==")
    print(cur.to_string(index=False))


if __name__ == "__main__":
    main()
