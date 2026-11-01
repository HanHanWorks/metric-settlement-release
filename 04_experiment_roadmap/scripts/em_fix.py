"""
E-N：事前固定的参考分母（C5）

d* = max(R_i(month), 0.2·Cap_i)，R 取上一年同月平均出力，年初固定。
性质：d* 与当期实现值无关、与上报无关 → 罚金最优上报 = 当日均值（无扭曲）。

用法：python em_fix.py 2024 2023
"""
import os
import sys
import numpy as np
import pandas as pd

R = os.path.expanduser("~/0NWXM")
S = R + "/2原始数据/3Second_data"
OUT = os.path.expanduser("~/hzh_RSI/04_experiments/P1_mechanism/results")


def load(year, need_pp=True):
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
    real["PM"] = pd.to_numeric(real.real_power, errors="coerce")
    real = real.dropna(subset=["PM"])
    real = real[real.PM >= 0]
    out = real.merge(cap[["farm_id", "Cap", "kind"]], on="farm_id", how="inner")
    if need_pp:
        fc = pd.read_csv(S + "/81-短期预测功率表%d-bs_data_short_power_%d.csv" % (year, year),
                         usecols=["farm_id", "data_time", "predict_power", "data_source"],
                         dtype={"farm_id": str, "data_source": str}, parse_dates=["data_time"])
        fc = fc[fc.data_source.str.strip() == "1"][["farm_id", "data_time", "predict_power"]]
        fc["farm_id"] = fc["farm_id"].str.strip()
        fc = fc.drop_duplicates(["farm_id", "data_time"])
        out = out.merge(fc, on=["farm_id", "data_time"], how="inner")
        out["PP"] = pd.to_numeric(out.predict_power, errors="coerce")
        out = out.dropna(subset=["PP"])
    out["month"] = out.data_time.dt.month
    out["day"] = out.data_time.dt.normalize()
    return out


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    ref_year = int(sys.argv[2]) if len(sys.argv) > 2 else year - 1
    print("[ref] %d -> R_i(month)" % ref_year, flush=True)
    ref = load(ref_year, need_pp=False)
    Rm = ref.groupby(["farm_id", "month"]).PM.mean().rename("R").reset_index()
    print("[ref] entries=%d" % len(Rm), flush=True)

    m = load(year, need_pp=True)
    m = m.merge(Rm, on=["farm_id", "month"], how="left")
    miss = m.R.isna().mean()
    m["R"] = m.R.fillna(m.Cap)          # 新站回退到装机
    print("[main] rows=%d  R 缺失回退比例=%.3f" % (len(m), miss), flush=True)
    m["d_new"] = np.maximum(m.R, 0.2 * m.Cap)
    m["d_old"] = np.maximum(m.PM, 0.2 * m.Cap)

    rows = []
    for (fid, day), g in m.groupby(["farm_id", "day"], sort=False):
        if len(g) < 90:
            continue
        pm, pp = g.PM.values, g.PP.values
        dn, do = g.d_new.values, g.d_old.values
        a_new = 100 * (1 - np.sqrt(np.mean(((pp - pm) / dn) ** 2)))
        a_old = 100 * (1 - np.sqrt(np.mean(((pp - pm) / do) ** 2)))
        # 新规则下的最优常数上报：d_new 在日内恒定 → m* = mean(PM)
        w = 1.0 / dn ** 2
        mstar = (w * pm).sum() / w.sum()
        rows.append(dict(farm_id=fid, kind=g.kind.iloc[0], day=str(day.date()),
                         cap=float(g.Cap.iloc[0]), acc_new=a_new, acc_old=a_old,
                         shrink_new=mstar / pm.mean() - 1 if pm.mean() > 0 else np.nan))
    d = pd.DataFrame(rows)
    d.to_csv(OUT + "/en_fix_%d.csv" % year, index=False, encoding="utf-8-sig")

    rho_all = d[["acc_new", "acc_old"]].corr(method="spearman").iloc[0, 1]
    per = d.groupby("farm_id").apply(lambda g: g[["acc_new", "acc_old"]].corr(method="spearman").iloc[0, 1])
    print("\n== E-N 结果（%d） ==" % year)
    print("场站-日 n=%d" % len(d))
    print("总体 Spearman ρ = %.4f" % rho_all)
    print("逐站 ρ：中位数 %.4f，最小 %.4f，<0.90 的站数 %d/%d"
          % (per.median(), per.min(), int((per < 0.90).sum()), len(per)))
    print("分数漂移：新−旧 中位数 %.2f 分，均值 %.2f 分，95 分位 %.2f"
          % ((d.acc_new - d.acc_old).median(), (d.acc_new - d.acc_old).mean(),
             (d.acc_new - d.acc_old).quantile(.95)))
    print("新规则下 shrink：中位数 %.4f，绝对值中位数 %.4f"
          % (d.shrink_new.median(), d.shrink_new.abs().median()))
    print("旧规则 acc 均值 %.2f → 新规则 %.2f" % (d.acc_old.mean(), d.acc_new.mean()))


if __name__ == "__main__":
    main()
