# 图件台账 v4.0（2026-10-31）

**生成脚本**：Fig. 2/3 由 `02_figures/make_figs_ep_v4.py` 生成；**Fig. 1 由 `02_figures/fig1_chain.svg` 手写**，用 `rsvg-convert` 转 PDF/PNG（不经过任何作图包）。
**命令**：`python3 02_figures/make_figs_ep_v4.py`；`rsvg-convert -f pdf -o 02_figures/fig1_chain.pdf 02_figures/fig1_chain.svg`
**输出**：每张图一份矢量 `*.pdf`（投稿用）+ 一份 `*.png` 300 dpi（预览用）；自动同步到 `09_EP_submission/figures/`
**规格**：双栏宽 7.16 in；Fig. 2/3 为 2×2 面板；Fig. 1 为单幅链路图；字号 6–9 pt；Okabe-Ito 色盲安全；PDF 字体嵌入为 Type 42

| 图 | 文件 | 尺寸 | 状态 |
|---|---|---|---|
| **Fig. 1** | `02_figures/fig1_chain.svg`（源）→ `fig1_chain.pdf` | 7.16 × 3.87 in（0.45 页） | ✅ v4 手写 SVG |
| **Fig. 2** | `02_figures/fig2_rules_cost.pdf` | 7.16 × 5.55 in（0.55 页） | ✅ v4 重绘 |
| **Fig. 3** | `02_figures/fig3_consequences.pdf` | 7.16 × 5.55 in（0.55 页） | ✅ v4 重绘 |

Fig. 1–3 合计约 **1.55 页**。

---

## Fig. 1｜评估与结算链路（v4 手写 SVG）

**内容**：上行物理链路（数值天气 + 场站 SCADA → 日前预测 $P_{\mathrm{ref}}$ → 日前计划 → 调度 → 实际出力 $P_{\mathrm{meas}}$）；下行两个泛函：同一个误差 $e_t$ → 场站分数 $R_t$（分母 $d_t=\max(p_t,\alpha C)$）→ 结算罚金 $\pi_t$ → 考核电量；同一个误差 → 先对场站求和 → 省级分数 → 合同指标。红色虚线从 $P_{\mathrm{meas}}$ 回到 $d_t$，标出“分母依赖实际出力”这一关键反馈。三个 badge：(1) denominator，(2) aggregation，(3) threshold θ。

> **Fig. 1. The assessment and settlement chain.** The upper row is the operational chain that produces the day-ahead forecast $P_{\mathrm{ref}}$ and the realised output $P_{\mathrm{meas}}$. The lower row shows two distinct functionals of the same forecast error $e_t$: a plant-level score $R_t$ whose denominator is $d_t=\max(p_t,\alpha C)$, mapped through the settlement penalty to assessed energy; and a provincial score obtained by summing the errors across plants before scoring, mapped to a contract target. The red dashed feedback marks the first design choice: the denominator depends on the realised output. The badges mark the two places where the chain is cut---the denominator inside the score (1) and the aggregation before the sum (2)---and the threshold $\theta$ is the third design choice (3). Neither functional can be recovered from the other.

**源文件说明**：`02_figures/fig1_chain.svg` 是**手写 SVG**，不依赖 matplotlib/TikZ/draw.io；`fig1_chain.pdf` 仅由 `rsvg-convert` 做格式转换，字体为 Times New Roman（Type 42 嵌入）。

**写作注意**：合同指标那一格写的是 `contract target`，**不写 80%**——省级 80% 的文本出处尚未落证（E-0，路线 §5）。等 E-0 完成后再决定是否在图里写数字。

---

## Fig. 2｜规则的代价（核心图，v4）

四格：(a) 出力分箱下的时间占比 vs 权重占比；(b) α 滑竿（三年 + 2024 风电/光伏）；(c) 地板绑定率分箱（气泡大小 = 场站日占比，灰柱 = 右轴占比）；(d) 两套归一化下的最优缩放联合分布 + 边际直方图。

> **Fig. 2. Tilt, weight concentration and rescaling under the settlement rule.** (a) Share of operating time and share of score weight by output/capacity bin, 2024; the weight of an interval is $d_t^{-2}$. (b) Median reporting tilt as a function of the floor level $\alpha$ in $d=\max(x,\alpha C)$, for 2023, 2024 and 2025; the thick line is 2024, the shaded band is its confidence interval, and the dashed lines are wind and solar in 2024. The regional rule ($\alpha=0.20$) and the national standard ($\alpha=1$) are two settings of one parameter; at $\alpha=1$ the tilt vanishes to machine precision. (c) Median tilt against the share of intervals in which the floor binds, pooled over 2023–2025 (33,831 farm-days); dot size is the share of farm-days and the grey bars report that share on the right axis. Where the floor binds in every interval (14.8% of farm-days) the denominator is constant and the tilt is exactly zero. (d) Joint distribution of the penalty-optimal rescaling $b^{*}$ under the two denominators, 2024; top and right marginals are wind (blue) and solar (orange); the dashed diagonal marks equal rescaling, the white marker is the median, and 85.9% of farm-days lie below the diagonal. The placebo gives $\Delta=0.000$.

**口径注意**：
1. (a) 的 13 个输出/容量分箱来自 `S2_weight_share.csv`；三箱合并即 Table I 的 14.3/3.0、62.3/80.8、78.8/90.8。
2. (b) 的纵轴是**场站-日中位数**；α=0.20 与 `em_summary_*.json` 的头条数字逐位相同；阴影带是 `F2a` 的 `lo/hi`。
3. (c) 的 `share` 是场站日占比，气泡大小只作视觉编码；右轴灰柱给出精确占比。
4. (d) 的 `Δ` 标注的是 **median(Δ) = −0.104**，不是 median($b^*_{flo}$) − median($b^*_{cap}$)（后者是 −0.155）。两个坐标轴截到 [0.3, 1.9]；全样本 1%/99% 分位是 0.035/4.75，截断只为可读性。

**为什么这是新贡献**：(b) 把"两套公式"变成"一个可标定的参数"；(c) 给出制度自己长出来的零 tilt 对照组；(a) 把 Table I 的三箱扩成连续分布；(d) 在同一批预测上分离分母效应与预测偏差。四格都不依赖 G3（行为数据）即可成立。

---

## Fig. 3｜后果（v4）

四格：(a) 2024 年 20.5 点差距的三段分解瀑布；(b) 两套公式下的场站日分数分布 + 60/65 门槛；(c) 两套归一化下的考核电量（对数轴）+ 受罚场站日占比；(d) 参考曲线改革下的合规率变化（风电/光伏/全部）。

> **Fig. 3. Decomposition, score distribution, assessed energy and compliance.** (a) Decomposition of the 2024 gap between the plant mean (62.1) and the provincial score (82.6): capacity weighting contributes $+3.0$ points, error cancellation $+31.0$, and the denominator returns $-13.6$; the net gap is 20.5. The vertical axis is truncated at 55%. (b) Distribution of farm-day accuracy scores under the regional and national formulas, 2024 (15,191 farm-days); dashed vertical lines are the 60 and 65 thresholds, and the level shift between the two means is 25.8 points. (c) Assessed energy per farm-day under the two denominators, log scale: 221.1 → 2.3 MWh for wind ($-98.9\%$) and 629.2 → 2.1 MWh for solar ($-99.7\%$); the share of farm-days with a penalty falls from 51.0% to 1.4% for wind and from 30.1% to 0.2% for solar. (d) Share of farm-days meeting the existing thresholds under the current rule and under the reference-curve denominator: wind 50.9% → 52.9%, solar 69.0% → 49.4%, all 60.6% → 51.0%.

**口径注意**：
1. (a) 的纵轴**从 55% 起**，caption 已声明截断；论证要用表里的数字，不用柱高比。
2. (b) 是**场站日分数分布**（15,191 行，`em_farmday_2024_full.csv`，`cf>0.005`）；均值 62.5/88.3 与 Table I 的 L0/L2 口径不同，图里只用于展示 level shift，不替代均值表。
3. (c) 是**考核电量（MWh/日）**，不是钱；换算金额要乘考核单价，论文不给单价。
4. (d) 来自 `S4_reference_normalizer.csv`；合规率是场站日占比，不是容量加权。

---

## 与旧图的关系

`02_figures/` 下的 `caliber_six.png`、`mechanism.png`、`e2_final.png`、`e3_final.png` 都属 v1/v2 口径，**v4 一律不用**。v3.2 的 Fig. 2/3 已被 v4 的四格图替换，旧版留在 `09_EP_submission/archive/EP_v1.0_20261031.zip`。

**保留用途**：`caliber_six.png` 可作答辩/汇报用，不进论文。

---

## 待办

| 项 | 说明 |
|---|---|
| Fig. 1 源文件 | 已是手写 SVG（`fig1_chain.svg`）；若期刊要求纯 TikZ 图源，再按同一布局改写 |
| 图的英文润色 | caption 我已写成投稿语气，但**未经母语编辑**；与正文一起送审前统一改 |
| 灰度打印检查 | v4 图用 Okabe-Ito 色 + 标记/线型双编码；打印成黑白后仍可分。建议投稿前目视检查一次 (a) 的四条线、(d) 的蓝/橙边际直方图。 |
| Fig. 1 维护 | 改图改 `fig1_chain.svg`，再用 `rsvg-convert` 生成 PDF/PNG；不要直接改 `fig1_chain.pdf`。 |