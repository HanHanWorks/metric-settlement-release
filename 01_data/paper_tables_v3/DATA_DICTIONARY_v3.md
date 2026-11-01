# 论文取数包 v3.2｜说明与口径（DATA DICTIONARY）

**建立**：2026-10-29
**位置**：`01_data/paper_tables_v3/`
**生成**：`python3 01_data/build_paper_tables.py`（一条命令重建全部 15 张表）
**归档**：`01_data/archive/P1_paper_tables_v3.2_20261029.zip`

---

## 0. 三条铁律

1. **正文里的每个数字都必须能在本包的某张表里原样找到。** 找不到就不许写进去；要么补表，要么改句子。逐条对照见 `NUMBERS_LEDGER.csv`。
2. **一套口径，全年到底。** 头条口径 = 剔除 `cf ≤ 0.005` 的空转场站-日 + 剔除 `shrink` 未定义的记录；2024 年 n=15,191。凡与本口径不同的数（如 `em_alpha_curve_*.csv` 的未过滤均值），**不得引用**。
3. **单位不许混。** 分数是"点"（100 分制），`shrink`/`Δ`/`b*` 是无量纲，考核电量是 **MWh/场站-日**（不是钱），区间宽度是 **MW**。

---

## 1. 表与论文的对应关系

| 论文位置 | 用哪张表 | 行数 | 说明 |
|---|---|---|---|
| **Table I** 数据与考核参数 | `T1_coverage.csv` | 9 | 3 年 × (全部/风电/光伏) |
| **Table II** 三段分解 | `T2_decomposition.csv` | 9 | 同结构，含 95% CI 与 B<0 占比 |
| **Table III** 行为面板 | `T3_behavior.csv` | 3 | 全部/风/光，含 Δ 的日聚类 CI 与安慰剂 |
| **Fig. 1** 链路 | 无（示意图） | — | — |
| **Fig. 2(a)** 滑竿 | `F2a_alpha_slider.csv` | 81 | 3 年 × 9 α × 3 品类 |
| **Fig. 2(b)** 地板绑定分箱 | `F2b_floorbin.csv` | 12 | 三年合并，n=5,004 的精确零在末行 |
| **Fig. 2(c)** 两套口径最优缩放 | `F2c_bstar_quantiles.csv` + `S5_behavior_farmday_2024.csv` | 3 + 15,524 | 画图用 S5，正文引用用 F2c 的分位数 |
| **Fig. 3(a)** 分解瀑布 | `F3a_waterfall.csv` | 5 | 62.09 → +3.04 → +31.02 → −13.60 → 82.55 |
| **Fig. 3(b)** 考核电量 | `F3b_penalty_mwh.csv` | 2 | 风电/光伏，旧口径 vs 容量口径 |
| §III 头条 | `S1_headline.csv` | 3 | 三年全部头条数字，一眼可查 |
| §IV-A 权重结构 | `S2_weight_share.csv` | 39 | 13 个 PM/Cap 分箱 × 3 个品类 |
| §III-B 分数→MW | `S3_mw_bridge.csv` | 3 | 区间覆盖率、区间宽度、RMSE |
| §V-C 改法 | `S4_reference_normalizer.csv` | 3 | 新旧分数、合规率、ρ、漂移 |
| §IV-E 稳健性 | `S6_subsets_robustness.csv` | 23 | 子集符号检查 |
| §V-A 案例 | `S2_weight_share.csv:kind=W, PM/Cap≥0.5` | — | "14% 时间、3% 权重" |

---

## 2. 逐表说明

### T1_coverage.csv — Table I
| 列 | 含义 |
|---|---|
| `year, kind, kind_label` | 年；`ALL/W/S`；英文标签 |
| `n_farms` | 覆盖场站数（原始面板里出现过的） |
| `n_farms_used` | 头条口径下仍有有效记录的场站数 |
| `n_days, first_day, last_day` | 天数与起止日。**2025 只到 06-24（175 天）** |
| `cap_total_MW, cap_median_MW` | 装机合计与中位（MW） |
| `threshold_score` | 考核门槛：风电 60、光伏 65；`ALL` 行为空 |
| `n_farmdays` | 原始场站-日数 |
| `n_farmdays_used` | 头条口径下的场站-日数 |
| `floor_bind_median` | 地板绑定率中位（15 分钟区间占比） |
| `pm_mean_median` | 场站-日平均出力中位（MW） |
| `provincial_acc_paper, caliber_n_station` | 仅 `ALL` 行：`caliber_3y.csv` 的省级 ACC 与站数 |

> **写作注意**：2024 年 **覆盖 49 站、可用 48 站**（1 个光伏场站全年被排除规则滤掉）。Table I 写 "49 (48 usable)" 最稳；别只写 49 又让 Table III 的 n 对不上。

### T2_decomposition.csv — Table II（核心表）
| 列 | 含义 |
|---|---|
| `L0` | 场站 ACC 简单平均 |
| `L1` | 容量加权 `Σ λ_i ACC_i` |
| `L2` | 允许抵消、仍以 Cap 为分母的聚合分 |
| `L3` | 真实省级口径 `100(1−RMS(Σe/D))`，`D=max(ΣPM, 0.2ΣCap)` |
| `weight = L1−L0` | 权重项 |
| `A = L2−L1` | 抵消项（≥0，与 Chebyshev 关联不等式一致） |
| `B = L3−L2` | 归一化项（**三年全为负**） |
| `gain = L3−L0` | 净差距 = weight + A + B |
| `*_ci_lo/hi` | 2000 次按日重抽的 95% CI |
| `B_negative_share` | B<0 的天数占比（**全部 1.0**，即每一天都为负） |

> **口径**：逐日算 L0–L3 再按日平均；与 `caliber_3y.csv` 的年度口径差 ≤0.5 分。论文固定用"按日平均"并加脚注。
> **写作注意**：`B_negative_share = 1.0` 比均值更有说服力——不是"平均为负"，是"**每一天都为负**"。这句话可以直接进 §IV-B。

### T3_behavior.csv — Table III
| 列 | 含义 |
|---|---|
| `b_cap_median/mean` | 容量口径下罚金最优的乘性缩放（衰减偏误使其系统性 <1） |
| `b_flo_median/mean` | 地板口径下的最优缩放 |
| `delta_median` | **Δ 的中位数**（−0.104） |
| `delta_mean, *_ci_*` | Δ 的均值与日聚类 bootstrap CI |
| `delta_plc_*` | 安慰剂（站内置换分母）的 Δ |
| `share_delta_negative` | Δ<0 的场站-日占比（85.9%） |
| `gain_pts_median/mean` | 偏离最优所让掉的分数 |

> **两个坑**：
> ① `delta_median = −0.104` 是 **median(Δ)**，不是 `median(b_flo) − median(b_cap) = −0.155`。图 2(c) 标的是前者，别写错。
> ② **不许用 `b_cap ≈ 1` 当验收**。衰减偏误 `E[PM²]/(E[PM²]+σ²) < 1` 是常态；`b_cap` 中位 1.024 只是"预测没有系统高估"的旁证。

### F2a_alpha_slider.csv — Fig. 2(a)
`alpha, kind, year, n, shrink_med, lo, hi, tax_med, floor_bind`。
81 行 = 3 年 × 9 个 α × 3 个品类。**α=0.20 一行与 `S1_headline.csv` 逐位相同**（2024: −0.2919 / 3.5848），这是本表可信的校验点。

> **写作注意**：α=1.00 处 `shrink_med` 与 `tax_med` 都是 0（机器精度 1e−16）。这不是"跑出来接近 0"，是**命题 1(i) 的精确端点**。正文可以写 "vanishes to machine precision"。

### F2b_floorbin.csv — Fig. 2(b)
`fb`（绑定率区间）、`n`、`share`、`shrink_med`、`tax_med`、`cf_med`、`cap_med`。
末行 `.99-1` 即"全程绑定"：n=5,004（14.8%），`shrink_med = tax_med = 0.000`。

> **写作注意**：这是"制度自己长出来的对照组"。审稿人问"零是不是算错了"，答案是那一块精确到 1e−15（`max|shrink| = 1.11e−15`）。

### F2c_bstar_quantiles.csv — Fig. 2(c) 的文字版
`variable, n, p01…p99, share_inside_0p3_1p9`。画图用 `S5`，正文引用分位数用本表。

> `b_cap` 的 1%/99% 是 0.035/4.75，**尾巴很长**；(c) 图只画 [0.3,1.9] 内的 81.2% 点，caption 已声明。

### F3a_waterfall.csv — Fig. 3(a)
`step, label, value, cumulative, kind`。5 行；`cumulative` 已算好，画瀑布直接用。

### F3b_penalty_mwh.csv — Fig. 3(b)
| 列 | 含义 |
|---|---|
| `penalty_old_MWh_per_farmday` | 旧口径下的考核电量（MWh/场站-日）：风电 221.12、光伏 629.15 |
| `penalty_new_MWh_per_farmday` | 容量口径：2.34 / 2.06 |
| `reduction_pct` | −98.9% / −99.7% |
| `paying_share_old/new` | 付费场站-日占比：风电 51.0%→1.4%，光伏 30.1%→0.2% |
| `total_old/new_MWh_2024` | 2024 全年合计：6.77×10⁶ → 3.32×10⁴（约 200 倍） |

> **单位纪律**：这是**考核电量**，不是钱。换算金额要乘考核单价，论文不给单价。
> **论点纪律**：这一格证明的不是"旧规则太狠"，而是"**两套门槛不可比**"——60/65 是按 62 分的分布标的，容量口径把分布挪到 88，几乎无人付费。**换分母必须同时重标门槛。**

### S1_headline.csv — 三年头条
一页看全：`shrink/tax/floor_bind/b_obs/rmse_over_cap` 的中位与均值、分品类、`acc_flo_mean`、`acc_cap_mean`、`gap_formula_points`。

> 2024：`acc_flo 62.48` vs `acc_cap 88.33`，差 **25.84** 点（摘要写 "62 vs 88"）。

### S2_weight_share.csv — 权重结构
`kind, pm_over_cap_bin, n_intervals, share_of_time, share_of_weight, mean_abs_error_cost`。

> 风电 `PM/Cap ≥ 0.5` 的五档（0.5–0.6 … 0.9–1.0）合计：时间占比 **14.3%**、权重占比 **3.0%**。这就是摘要里 "14% of wind operating time but only 3% of the weight"。

### S3_mw_bridge.csv — 分数→MW
`share_rmse_inside_interval`（三年 92.1/93.5/95.4%）、`median_interval_width_MW`（2024: 23.57）、`median_rmse_MW`（8.92）、`median_rmse_over_cap`（10.1%）。

> 论点：同一个分数对应的 MW 区间宽 23.6 MW，而真实 RMSE 只有 8.9 MW ⇒ **地板口径的分数不可反演成 MW**，只能给区间。

### S4_reference_normalizer.csv — E-N 改法
`acc_old/new`, `score_drift_median`, `compliance_old/new`, `spearman_old_new`, `shrink_new_max_abs`。

> 关键：`spearman = 0.610`（**不是**"排序几乎不变"——42/49 个场站的ρ低于 0.9，见 findings §11），合规率 60.6%→51.0%，光伏 −19.6 pt、风电 +2.0 pt。**改法能消扭曲，但会重新分配达标**，必须配门槛重标定与过渡期。

### S5_behavior_farmday_2024.csv
E-B 的逐场站-日原表（15,524 行）：`b_cap, b_flo, delta, delta_plc, gain_pts`。供 Fig. 2(c) 与复算。

### S6_subsets_robustness.csv
23 个子集的 `shrink/tax/floor_bind`。**符号全负**，最弱 −0.013（低 CF 档，机制预测的零）。

### NUMBERS_LEDGER.csv
`number_id, value, unit, used_in, source, note`。**24 行**，覆盖摘要、三张图、正文关键句里的每个数。

> 用法：写完一段就查一遍——句子里出现的数必须在 `value` 列里能找到（或由两列相除得到）。

---

## 3. 不许用的三份（留档但不引用）

| 文件 | 为什么不能用 |
|---|---|
| `05_findings/em_2024/em_alpha_curve_*.csv` | **未过滤、取均值**（2024 n=15,968，α=0.20 给 −0.3101），不是头条口径 |
| `05_findings/em_2024/em_farmday_*_full.csv` 的 `tax_a*` 列 | 行级原值，未过滤；可复算，不可直接报数 |
| `01_data/all_experiments.csv`、`summary_all.csv`、`e2_*`、`e3_*` | 属已删除的 §V（agent 部分），与 P1 主张无关 |

---

## 4. 五处已知口径坑（写作时逐条核）

| # | 坑 | 正确做法 |
|---|---|---|
| 1 | `caliber_3y.csv` 是**年度口径**，与 T2 的**按日平均**差 ≤0.5 分 | 论文固定按日平均，脚注说明；别在同一段混用两个口径 |
| 2 | 2025 只到 **06-24（175 天）** | Table I 显式写 period；同比只在 2023/2024 之间做 |
| 3 | `acc_monthly_2024.csv` 只覆盖 25 站/200 场站-月/1,630 assessed days | 它**不是**全样本，别拿它算全省合计 |
| 4 | 79,431 MWh 是 25 站 200 场站-月的合计 | **不是** 2024 全年 49 站合计（后者见 `F3b`） |
| 5 | `delta_median ≠ median(b_flo) − median(b_cap)` | 引用 Δ 一律用 `T3.delta_median` |

---

## 5. 重建与归档

```bash
# 重建（需要 05_findings/em_2024/ 下的服务器结果）
python3 01_data/build_paper_tables.py

# 归档（每次改口径后重新打包，文件名带日期）
cd 01_data && zip -r archive/P1_paper_tables_v3.2_$(date +%Y%m%d).zip paper_tables_v3 build_paper_tables.py
```

**版本**：v3.2（2026-10-29）。若 `S1`～`S4` 任一数字变动，必须同步改：`05_findings/EM_实测结果_2023-2025.md`、`NUMBERS_LEDGER.csv`、`03_outline/PAPER_ROUTE_v3.md` §2.2 摘要。