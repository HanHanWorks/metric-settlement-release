# -*- coding: utf-8 -*-
"""P1 v3.2 论文表格生成脚本（写作取数唯一入口）。

输入（相对 P1_paper/）：
  05_findings/em_2024/em_farmday_{year}_full.csv   场站-日面板（9 个 α）
  05_findings/em_2024/em_summary_{year}.json       年度头条
  05_findings/em_2024/ef_alpha_slider_3y.csv       E-F 滑竿
  05_findings/em_2024/ef_floorbin_3y.csv           E-F 地板绑定分箱
  05_findings/em_2024/eb_behavior_2024.csv         E-B 逐场站-日
  05_findings/em_2024/en_fix_2024.csv              E-N 参考曲线
  05_findings/em_2024/ed_decomp_{year}.csv         E-D1（含 kind 列）
  01_data/caliber_3y.csv                           权威省级口径表

输出：01_data/paper_tables_v3/ 下 12 张 CSV + NUMBERS_LEDGER.csv

用法：python3 01_data/build_paper_tables.py
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "05_findings", "em_2024")
OUT = os.path.join(ROOT, "01_data", "paper_tables_v3")
YEARS = (2023, 2024, 2025)
THR = {"W": 60.0, "S": 65.0}
RNG = np.random.default_rng(20261029)
B = 2000


def p(*a):
    print(*a)


def ensure():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)


def save(df, name, note=None):
    path = os.path.join(OUT, name)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    p("  [out] %-34s rows=%d" % (name, len(df)))


def load_farmday(year, full=True):
    f = "em_farmday_%d%s.csv" % (year, "_full" if full else "")
    d = pd.read_csv(os.path.join(SRC, f))
    d["year"] = year
    d["day"] = pd.to_datetime(d["day"])
    return d


# ---------------------------------------------------------------- T1 覆盖表
def t1():
    rows = []
    cal = pd.read_csv(os.path.join(ROOT, "01_data", "caliber_3y.csv"))
    for y in YEARS:
        d = load_farmday(y)
        use = d[d.cf > 0.005].dropna(subset=["shrink", "tax"])
        for kind, label in (("ALL", "all"), ("W", "wind"), ("S", "solar")):
            g = d if kind == "ALL" else d[d.kind == kind]
            u = use if kind == "ALL" else use[use.kind == kind]
            if not len(g):
                continue
            row = dict(year=y, kind=kind, kind_label=label,
                       n_farms=int(g.farm_id.nunique()),
                       n_days=int(g.day.nunique()),
                       first_day=str(g.day.min().date()),
                       last_day=str(g.day.max().date()),
                       cap_total_MW=round(float(g.groupby("farm_id").cap.first().sum()), 1),
                       cap_median_MW=round(float(g.groupby("farm_id").cap.first().median()), 1),
                       threshold_score=(THR.get(kind) if kind != "ALL" else np.nan),
                       n_farms_used=int(u.farm_id.nunique()),
                       n_farmdays=int(len(g)),
                       n_farmdays_used=int(len(u)),
                       floor_bind_median=round(float(u.floor_bind.median()), 3),
                       pm_mean_median=round(float(u.pm_mean.median()), 2))
            if kind == "ALL":
                c = cal[(cal.year == y)]
                row["provincial_acc_paper"] = round(float(c.acc_prov.iloc[0]), 2)
                row["caliber_n_station"] = int(c.n_station.iloc[0])
            rows.append(row)
    df = pd.DataFrame(rows)
    save(df, "T1_coverage.csv")
    return df


# ------------------------------------------------------------ T2 三段分解
def t2():
    frames = []
    for y in YEARS:
        f = os.path.join(SRC, "ed_decomp_%d.csv" % y)
        if not os.path.exists(f):
            p("  [!] missing", f)
            continue
        d = pd.read_csv(f)
        if "kind" not in d.columns:
            d["kind"] = "ALL"
        frames.append(d)
    if not frames:
        return None
    d = pd.concat(frames, ignore_index=True)
    rows = []
    for (y, k), g in d.groupby(["year", "kind"]):
        r = dict(year=int(y), kind=k, n_day=len(g),
                 L0=round(g.L0.mean(), 2), L1=round(g.L1.mean(), 2),
                 L2=round(g.L2.mean(), 2), L3=round(g.L3.mean(), 2),
                 weight=round(g.weight.mean(), 2), A=round(g.A.mean(), 2),
                 B=round(g.B.mean(), 2), gain=round(g.gain.mean(), 2))
        for col in ("weight", "A", "B", "gain"):
            v = g[col].values
            bs = v[RNG.integers(0, len(v), (B, len(v)))].mean(axis=1)
            r["%s_ci_lo" % col] = round(float(np.percentile(bs, 2.5)), 2)
            r["%s_ci_hi" % col] = round(float(np.percentile(bs, 97.5)), 2)
        r["B_negative_share"] = round(float((g.B < 0).mean()), 3)
        rows.append(r)
    df = pd.DataFrame(rows).sort_values(["year", "kind"]).reset_index(drop=True)
    save(df, "T2_decomposition.csv")
    return df


def load_bstar_filtered():
    """b* 场站-日面板，与 2024 场站-日面板合并且剔除空转日（cf<=0.005）。

    剔除口径与头条一致：2024 raw 15,968 → zero-output 429（不进 b*）→
    b* raw 15,524 → 再剔 348 个 cf<=0.005 且 b* 有定义的场站-日 → 15,176。
    """
    eb = pd.read_csv(os.path.join(SRC, "eb_behavior_2024.csv"))
    eb["day"] = pd.to_datetime(eb["day"])
    eb["farm_id"] = eb["farm_id"].astype("int64")
    fd = load_farmday(2024)
    fd["farm_id"] = fd["farm_id"].astype("int64")
    key = fd[["farm_id", "kind", "day", "cf"]].copy()
    m = eb.merge(key, on=["farm_id", "kind", "day"], how="left",
                 validate="one_to_one")
    if len(m) != len(eb):
        raise ValueError("b* 合并产生重复行：%d -> %d" % (len(eb), len(m)))
    if m.cf.isna().any():
        raise ValueError("b* 面板有 %d 行未匹配到 cf" % int(m.cf.isna().sum()))
    return m[m.cf > 0.005].copy()


# -------------------------------------------------------------- T3 行为表
def t3():
    d = load_bstar_filtered()
    rng = np.random.default_rng(20261029)   # 独立随机流，保证 CI 可复现
    rows = []
    for kind in ("ALL", "W", "S"):
        g = d if kind == "ALL" else d[d.kind == kind]
        g = g.dropna(subset=["b_cap", "b_flo", "delta", "delta_plc"])
        byd = g.groupby("day")[["delta", "delta_plc"]].mean()
        v = byd.delta.values
        bs = v[rng.integers(0, len(v), (B, len(v)))].mean(axis=1)
        vp = byd.delta_plc.values
        bsp = vp[rng.integers(0, len(vp), (B, len(vp)))].mean(axis=1)
        rows.append(dict(
            kind=kind, n_farmdays=int(len(g)), n_days=int(g.day.nunique()),
            b_cap_median=round(float(g.b_cap.median()), 4),
            b_cap_mean=round(float(g.b_cap.mean()), 4),
            b_flo_median=round(float(g.b_flo.median()), 4),
            b_flo_mean=round(float(g.b_flo.mean()), 4),
            delta_median=round(float(g.delta.median()), 4),
            delta_mean=round(float(v.mean()), 4),
            delta_mean_ci_lo=round(float(np.percentile(bs, 2.5)), 4),
            delta_mean_ci_hi=round(float(np.percentile(bs, 97.5)), 4),
            delta_plc_mean=round(float(vp.mean()), 5),
            delta_plc_ci_lo=round(float(np.percentile(bsp, 2.5)), 5),
            delta_plc_ci_hi=round(float(np.percentile(bsp, 97.5)), 5),
            share_delta_negative=round(float((g.delta < 0).mean()), 3),
            gain_pts_median=round(float(g.gain_pts.median()), 2),
            gain_pts_mean=round(float(g.gain_pts.mean()), 2)))
    df = pd.DataFrame(rows)
    save(df, "T3_behavior.csv")
    return df


# --------------------------------------------------------------- F2 三格
def f2():
    sl = pd.read_csv(os.path.join(SRC, "ef_alpha_slider_3y.csv"))
    sl = sl.sort_values(["alpha", "kind"]).reset_index(drop=True)
    save(sl, "F2a_alpha_slider.csv")

    fb = pd.read_csv(os.path.join(SRC, "ef_floorbin_3y.csv"))
    save(fb, "F2b_floorbin.csv")

    d = load_bstar_filtered().dropna(subset=["b_cap", "b_flo", "delta"])
    inside = d[(d.b_cap > 0.3) & (d.b_cap < 1.9) & (d.b_flo > 0.3) & (d.b_flo < 1.9)]
    rows = []
    for col in ("b_cap", "b_flo", "delta"):
        q = d[col].quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
        rows.append(dict(variable=col, n=len(d),
                         p01=round(float(q.iloc[0]), 4), p05=round(float(q.iloc[1]), 4),
                         p25=round(float(q.iloc[2]), 4), median=round(float(q.iloc[3]), 4),
                         p75=round(float(q.iloc[4]), 4), p95=round(float(q.iloc[5]), 4),
                         p99=round(float(q.iloc[6]), 4),
                         share_inside_0p3_1p9=round(float(
                             ((d[col] > 0.3) & (d[col] < 1.9)).mean()), 3)))
    df = pd.DataFrame(rows)
    save(df, "F2c_bstar_quantiles.csv")
    p("       F2c: joint points inside plotted range = %.3f" % (len(inside) / float(len(d))))
    return df


# --------------------------------------------------------------- F3 两格
def f3():
    js = json.load(open(os.path.join(SRC, "ed_decomp_2024.json"), encoding="utf-8"))
    steps = [("station mean", js["L0"], 0),
             ("capacity weighting", js["weight"], 1),
             ("error cancellation", js["A"], 2),
             ("normalizer", js["B"], 3),
             ("provincial score", js["L3"], 4)]
    rows, cum = [], js["L0"]
    for label, val, i in steps:
        if i in (0, 4):
            rows.append(dict(step=i, label=label, value=round(val, 2),
                             cumulative=round(val, 2), kind="level"))
            cum = val
        else:
            cum = cum + val
            rows.append(dict(step=i, label=label, value=round(val, 2),
                             cumulative=round(cum, 2), kind="delta"))
    df = pd.DataFrame(rows)
    save(df, "F3a_waterfall.csv")

    d = load_farmday(2024)
    d = d[d.cf > 0.005]              # 与头条口径一致（剔除空转日）
    rows = []
    for kind, label in (("W", "wind"), ("S", "solar")):
        g = d[d.kind == kind].dropna(subset=["acc_flo", "acc_cap"])
        thr = THR[kind]
        k = 0.2 if kind == "W" else 1.0
        old = g.cap * k * np.maximum(0.0, thr - g.acc_flo)
        new = g.cap * k * np.maximum(0.0, thr - g.acc_cap)
        rows.append(dict(kind=kind, kind_label=label, n_farmdays=int(len(g)),
                         threshold=thr, hinge_factor=k,
                         penalty_old_MWh_per_farmday=round(float(old.mean()), 2),
                         penalty_new_MWh_per_farmday=round(float(new.mean()), 2),
                         reduction_pct=round(float(100 * (1 - new.mean() / old.mean())), 1),
                         paying_share_old=round(float((old > 0).mean()), 3),
                         paying_share_new=round(float((new > 0).mean()), 3),
                         total_old_MWh_2024=round(float(old.sum()), 0),
                         total_new_MWh_2024=round(float(new.sum()), 0)))
    df = pd.DataFrame(rows)
    save(df, "F3b_penalty_mwh.csv")
    return df


# ------------------------------------------------------------ S1 头条数字
def s1():
    rows = []
    for y in YEARS:
        js = json.load(open(os.path.join(SRC, "em_summary_%d.json" % y), encoding="utf-8"))
        row = dict(year=y, n_farmdays_raw=js["n_farmday_raw"], n_farmdays=js["n_farmday"],
                   n_farms=js["n_farm"], n_days=js["n_day"],
                   shrink_median=round(js["shrink_med"], 4),
                   shrink_mean=round(js["shrink_mean"], 4),
                   tax_median=round(js["tax_med"], 4),
                   tax_mean=round(js["tax_mean"], 4),
                   floor_bind_median=round(js["floor_bind_med"], 4),
                   floor_bind_mean=round(js["floor_bind_mean"], 4),
                   b_obs_median=round(js["b_obs_med"], 4),
                   rmse_over_cap_median=round(js["rmse_over_cap_med"], 4))
        for k in ("W", "S"):
            b = js["by_kind"].get(k, {})
            row["shrink_median_%s" % k] = round(b.get("shrink_med", np.nan), 4)
            row["tax_median_%s" % k] = round(b.get("tax_med", np.nan), 4)
            row["acc_flo_mean_%s" % k] = round(b.get("acc_flo_mean", np.nan), 3)
            row["n_farmdays_%s" % k] = b.get("n", np.nan)
        rows.append(row)
    for y in YEARS:
        d = load_farmday(y)
        d = d[d.cf > 0.005].dropna(subset=["shrink", "tax"])
        rows[YEARS.index(y)]["acc_flo_mean"] = round(float(d.acc_flo.mean()), 2)
        rows[YEARS.index(y)]["acc_cap_mean"] = round(float(d.acc_cap.mean()), 2)
        rows[YEARS.index(y)]["gap_formula_points"] = round(
            float(d.acc_cap.mean() - d.acc_flo.mean()), 2)
    df = pd.DataFrame(rows)
    save(df, "S1_headline.csv")
    return df


# ------------------------------------------------------- S2 权重结构（分箱）
def s2():
    d = pd.read_csv(os.path.join(SRC, "em_weight_share_2024.csv"))
    d.columns = [c.lstrip("\ufeff") for c in d.columns]
    d["pm_over_cap_bin"] = ["[%.2f,%.2f)" % (a, b) for a, b in zip(d.lo, d.hi)]
    d = d.rename(columns={"n": "n_intervals", "n_share": "share_of_time",
                          "w_share": "share_of_weight",
                          "mean_error_cost": "mean_abs_error_cost"})
    out = d[["kind", "pm_over_cap_bin", "n_intervals", "share_of_time",
             "share_of_weight", "mean_abs_error_cost"]].copy()
    for c in ("share_of_time", "share_of_weight"):
        out[c] = out[c].round(4)
    save(out, "S2_weight_share.csv")
    return out


# --------------------------------------------------------- S3 分数→MW 桥
def s3():
    rows = []
    for y in YEARS:
        d = load_farmday(y).dropna(subset=["acc_flo", "rmse_mw"])
        d = d[d.cf > 0.005]
        lo = (1 - d.acc_flo / 100.0) * 0.2 * d.cap
        hi = (1 - d.acc_flo / 100.0) * d.cap
        inside = (d.rmse_mw >= lo) & (d.rmse_mw <= hi)
        rows.append(dict(year=y, n_farmdays=int(len(d)),
                         share_rmse_inside_interval=round(float(inside.mean()), 3),
                         median_interval_width_MW=round(float((hi - lo).median()), 2),
                         median_rmse_MW=round(float(d.rmse_mw.median()), 2),
                         median_rmse_over_cap=round(float((d.rmse_mw / d.cap).median()), 4)))
    df = pd.DataFrame(rows)
    save(df, "S3_mw_bridge.csv")
    return df


# --------------------------------------------------- S4 参考曲线改法（E-N）
def solve_theta(acc_new, target, lo=0.0, hi=100.0, step=0.1):
    """在 [lo,hi] 上按 0.1 分分辨率扫描公共新阈值 theta，
    取使 (acc_new >= theta) 的合规率最接近 target 的那个阈值。"""
    grid = np.round(np.arange(lo, hi + step / 2.0, step), 1)
    rates = np.array([(acc_new >= t).mean() for t in grid])
    return float(grid[int(np.argmin(np.abs(rates - target)))])


def s4():
    d = pd.read_csv(os.path.join(SRC, "en_fix_2024.csv"))
    d["day"] = pd.to_datetime(d["day"])
    d["farm_id"] = d["farm_id"].astype("int64")
    fd = load_farmday(2024)
    fd["farm_id"] = fd["farm_id"].astype("int64")
    # cf / acc_cap 只从场站-日面板取；cap 已在 en_fix 内，避免重名
    key = fd[["farm_id", "kind", "day", "cf", "acc_cap"]]
    d = d.merge(key, on=["farm_id", "kind", "day"], how="left",
                validate="one_to_one")
    if d.cf.isna().any():
        raise ValueError("en_fix 有 %d 行未匹配到 cf" % int(d.cf.isna().sum()))
    d = d[d.cf > 0.005].copy()       # 与头条口径一致：剔除空转日

    thr_old = np.where(d.kind == "W", 60.0, 65.0)
    comp_old_all = float((d.acc_old >= thr_old).mean())
    theta = solve_theta(d.acc_new.values, comp_old_all)
    p("       S4: n=%d, old-rate=%.4f, theta*=%.1f, new-rate=%.4f"
      % (len(d), comp_old_all, theta, (d.acc_new >= theta).mean()))

    # 容量三分位：按 farm 级 cap 切分（cap 在 farm 内不变，故分组与
    # farm-day 级三分位完全一致）
    cap_farm = d.groupby("farm_id")["cap"].first().values
    q1, q2 = np.quantile(cap_farm, [1.0 / 3.0, 2.0 / 3.0])
    cap_grp = np.where(d.cap <= q1, "cap_small",
                       np.where(d.cap <= q2, "cap_mid", "cap_large"))
    d["cap_grp"] = cap_grp

    new_ids = set()
    if os.path.exists(os.path.join(SRC, "em_farmday_2023_full.csv")):
        fd23 = pd.read_csv(os.path.join(SRC, "em_farmday_2023_full.csv"))
        new_ids = set(fd["farm_id"].unique()) - set(fd23.farm_id.unique())

    def row(kind, g, group, note=""):
        thr = np.where(g.kind == "W", THR["W"], THR["S"])   # 旧阈值（逐行按 kind）
        rho = g[["acc_old", "acc_new"]].corr(method="spearman").iloc[0, 1]
        return dict(kind=kind, group=group, n_farmdays=int(len(g)),
                    n_farms=int(g.farm_id.nunique()),
                    acc_old_mean=round(float(g.acc_old.mean()), 2),
                    acc_new_mean=round(float(g.acc_new.mean()), 2),
                    score_drift_median=round(float((g.acc_new - g.acc_old).median()), 2),
                    compliance_old=round(float((g.acc_old >= thr).mean()), 3),
                    compliance_new=round(float((g.acc_new >= thr).mean()), 3),
                    spearman_old_new=round(float(rho), 3),
                    shrink_new_max_abs=round(float(g.shrink_new.abs().max()), 6),
                    theta_calibrated=theta,
                    compliance_new_calibrated=round(float((g.acc_new >= theta).mean()), 3),
                    note=note)

    rows = []
    for kind in ("ALL", "W", "S"):
        g = d if kind == "ALL" else d[d.kind == kind]
        rows.append(row(kind, g, "overall",
                        "旧阈值反事实：W>=60 / S>=65" if kind == "ALL"
                        else "旧阈值 %d" % THR[kind]))
    for grp, lab in (("cap_small", "small"), ("cap_mid", "mid"),
                     ("cap_large", "large")):
        g = d[d.cap_grp == grp]
        rows.append(row(grp, g, "capacity_tertile",
                        "%s tertile, farm-level cap cut q1=%.1f q2=%.1f MW"
                        % (lab, q1, q2)))
    if new_ids:
        g = d[d.farm_id.isin(new_ids)]
        rows.append(row("new_farm_2024", g, "new_farm",
                        "2024 出现 / 2023 未出现的 %d 个 farm（其中 1 个在 cf 过滤后无样本）"
                        % len(new_ids)))
    g = d[np.isclose(d.acc_new, d.acc_cap, atol=1e-6)]
    rows.append(row("fallback_capacity_norm", g, "fallback",
                    "acc_new == acc_cap（<1e-6），无 prior-year reference 时回退容量分母"))

    df = pd.DataFrame(rows)
    save(df, "S4_reference_normalizer.csv")
    return df


# ------------------------------------------------------ S5 行为面板（原表副本）
def s5():
    d = pd.read_csv(os.path.join(SRC, "eb_behavior_2024.csv"))
    save(d, "S5_behavior_farmday_2024.csv")


# ------------------------------------------------------ S6 子集稳健性
def s6():
    d = pd.read_csv(os.path.join(SRC, "ef_subsets_filtered.csv"))
    save(d, "S6_subsets_robustness.csv")
    return d


# ---------------------------------------------------------- 数字台账
def ledger():
    """正文/摘要/图里出现的每个数，都在这儿有出处。"""
    R = []

    def add(nid, val, unit, where, source, note=""):
        R.append(dict(number_id=nid, value=val, unit=unit, used_in=where,
                      source=source, note=note))

    add("abstract_tilt", "-0.27 ~ -0.30", "fraction", "Abstract; §I; Fig.2",
        "S1_headline.csv:shrink_median", "三年中位 −0.266/−0.292/−0.304，摘要写 27–30%")
    add("abstract_weight_time", "14%", "share of intervals", "Abstract; §IV-A",
        "S2_weight_share.csv", "风电 PM≥0.5Cap 的时间占比 14.3%")
    add("abstract_weight_score", "3%", "share of weight", "Abstract; §IV-A",
        "S2_weight_share.csv", "风电 PM≥0.5Cap 的权重占比 3.0%")
    add("abstract_score_floored", "62", "points", "Abstract; §III", "S1_headline.csv:acc_flo_mean",
        "2024 = 62.07")
    add("abstract_score_capacity", "88", "points", "Abstract; §III", "S1_headline.csv:acc_cap_mean",
        "2024 = 88.33")
    add("ci_weight", "+3.0", "points", "Abstract; Fig.3a; Table II", "T2_decomposition.csv:weight",
        "2024 ALL")
    add("ci_cancel", "+31.0", "points", "Abstract; Fig.3a; Table II", "T2_decomposition.csv:A",
        "2024 ALL")
    add("ci_normalizer", "-13.6", "points", "Abstract; Fig.3a; Table II", "T2_decomposition.csv:B",
        "2024 ALL；三年 −10.98/−13.60/−15.65")
    add("understatement", "44%", "ratio", "Abstract; §IV-B", "T2_decomposition.csv",
        "13.60/31.02")
    add("delta_median", "-0.110", "dimensionless", "Fig.2c; Table III; §IV-C",
        "T3_behavior.csv:delta_median",
        "median of Δ（n=15,176，已剔 cf<=0.005）；不是中位数之差")
    add("delta_mean_ci", "[-0.196, -0.178]", "dimensionless", "Table III",
        "T3_behavior.csv", "Δ 均值的日聚类 bootstrap CI（2,000 次按 day 重采样）")
    add("placebo", "0.0000 (median)", "dimensionless", "Fig.2c; Table III",
        "T3_behavior.csv:delta_plc_mean",
        "站内置换分母后的 Δ：中位 0.0000，均值 0.0002，CI [0.00002, 0.0003]")
    add("gain_pts", "5.4", "points", "§IV-C", "T3_behavior.csv:gain_pts_median",
        "偏离最优的收益中位（wind 5.1 / solar 5.7）")
    add("bstar_n", "15,176", "farm-days", "Table III; Fig.2d",
        "T3_behavior.csv:n_farmdays",
        "b* raw 15,524 → 剔 348 个低出力日 → 15,176（wind 6,827 / solar 8,349）")
    add("bstar_medians", "1.036 / 0.877 / -0.110", "dimensionless", "Table III; Fig.2d",
        "T3_behavior.csv", "b_cap / b_flo / Δ 中位；Δ<0 占 87.1%")
    add("delta_negative_share", "87.1%", "share", "Fig.2d; Table III",
        "T3_behavior.csv:share_delta_negative", "Δ<0 的场站-日占比（旧口径 85.9%）")
    add("en_rho", "0.61", "Spearman", "§V-C", "S4_reference_normalizer.csv",
        "参考曲线改法下新旧分数的秩相关")
    add("en_compliance", "60.5% -> 49.8%", "share", "§V-C; Fig.3d",
        "S4_reference_normalizer.csv",
        "旧阈值下：光伏 69.9%→49.5%，风电 49.0%→50.3%（n=15,191）")
    add("theta_calibrated", "53.4", "points", "§V-C; Fig.3d",
        "S4_reference_normalizer.csv:theta_calibrated",
        "公共新阈值，0–100 按 0.1 扫描，使新分母总体合规率=旧分母 60.5%")
    add("calibrated_compliance", "60.5 / 57.4 / 63.0", "percent", "§V-C; Fig.3d",
        "S4_reference_normalizer.csv:compliance_new_calibrated",
        "θ*=53.4 下的 all / wind / solar 合规率")
    add("calibrated_tertiles", "52.6 / 53.8 / 75.2", "percent", "§V-C",
        "S4_reference_normalizer.csv:cap_small/mid/large",
        "farm 级容量三分位（q1=73.4, q2=120.3 MW）在 θ*=53.4 下的合规率")
    add("new_farm_proxy", "68.0 -> 97.6 -> 98.5", "percent", "§V-C",
        "S4_reference_normalizer.csv:new_farm_2024",
        "9 个 2024 新增 farm_id；1 个在 cf 过滤后为空 → 8 个 farm / 1,314 场站-日")
    add("fallback_proxy", "65.1 -> 99.3 -> 99.8", "percent", "§V-C",
        "S4_reference_normalizer.csv:fallback_capacity_norm",
        "acc_new==acc_cap（3,693 场站-日，24.3%）：旧阈值 / 旧θ新分母 / 校准θ")
    add("alt_treatment", "62.07 / 88.45 / -0.280", "points; fraction", "§V-D robustness",
        "em_farmday_2024_full.csv",
        "保留 zero-output+低出力日（n=15,968）：acc_flo/acc_cap 均值与 tilt 中位；主样本 62.48/88.33/-0.292")
    add("alpha_national_zero", "<=1.1e-16", "fraction", "Fig.2a; §II-B", "F2a_alpha_slider.csv",
        "α=1.00 时 |shrink| 上界，三年")
    add("alpha_020", "-0.292", "fraction", "Fig.2a", "F2a_alpha_slider.csv",
        "2024 中位；与 S1 逐位一致")
    add("floorbin_exact", "5,004 (14.8%)", "farm-days", "Fig.2b; §IV-B", "F2b_floorbin.csv",
        "floor_bind=1 时 shrink=tax=0，精确到 1e-15；占 33,831 场站-日的 14.8%")
    add("penalty_wind", "221.1 -> 2.3", "MWh/farm-day", "Fig.3b; §V", "F3b_penalty_mwh.csv",
        "−98.9%")
    add("penalty_solar", "629.2 -> 2.1", "MWh/farm-day", "Fig.3b; §V", "F3b_penalty_mwh.csv",
        "−99.7%")
    add("mw_interval", "[0.2Cap, Cap]", "MW", "§III-B", "S3_mw_bridge.csv",
        "地板口径下分数不可逆；93.9% 的场站-日落在此区间内")
    add("mw_median", "8.92", "MW", "§III-B", "S3_mw_bridge.csv:median_rmse_MW",
        "RMSE 中位，占容量 10.1%")
    add("gap_caliber", "20.75", "points", "§I ¶2 (motivation only)", "01_data/caliber_3y.csv",
        "2024 acc_prov − acc_station；**不是贡献**")
    add("off_visible", "0.20%", "share", "§I ¶2 (motivation only)", "01_data/caliber_3y.csv",
        "2024；9 格均值 0.51%")
    df = pd.DataFrame(R)
    save(df, "NUMBERS_LEDGER.csv")
    return df


def main():
    ensure()
    p("[1] T1 coverage"); t1()
    p("[2] T2 decomposition"); t2()
    p("[3] T3 behavior"); t3()
    p("[4] F2 panels"); f2()
    p("[5] F3 panels"); f3()
    p("[6] S1 headline"); s1()
    p("[7] S2 weight share"); s2()
    p("[8] S3 mw bridge"); s3()
    p("[9] S4 reference normalizer"); s4()
    p("[10] S5 behavior panel"); s5()
    p("[11] S6 subsets"); s6()
    p("[12] numbers ledger"); ledger()
    p("done ->", OUT)


if __name__ == "__main__":
    main()