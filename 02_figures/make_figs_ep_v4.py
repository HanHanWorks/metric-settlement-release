# -*- coding: utf-8 -*-
"""Energy Policy v4 figures (Fig. 2 and Fig. 3 only; Fig. 1 untouched).

Reads the frozen paper tables in 01_data/paper_tables_v3 plus the per-farm-day
behaviour file, and writes vector PDF + 300-dpi PNG previews.

Design goals:
  - 2 x 2 panels, 7.16 in wide, Times New Roman / STIX maths, 8 pt base.
  - Okabe-Iito colour-blind safe palette; every colour also carries a marker or
    line-style cue so the figures survive grayscale printing.
  - Each panel answers one question and carries the key number on the panel.
"""
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TAB = os.path.join(ROOT, "01_data", "paper_tables_v3")
FIND = os.path.join(ROOT, "05_findings", "em_2024")

W = 7.16
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8.5,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "lines.linewidth": 1.0,
    "lines.markersize": 4.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

# Okabe-Ito
BLUE = "#0072B2"
SKY = "#56B4E9"
ORANGE = "#E69F00"
GREEN = "#009E73"
VERM = "#D55E00"
PURPLE = "#CC79A7"
GREY = "#666666"
LGREY = "#BDBDBD"


def panel(ax, letter, x=0.0, y=1.02):
    ax.text(x, y, "(%s)" % letter, transform=ax.transAxes, ha="left",
            va="bottom", fontsize=9, fontweight="bold")


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, "%s.%s" % (name, ext)),
                    dpi=300 if ext == "png" else None)
    # also refresh the submission copy
    sub = os.path.join(ROOT, "09_EP_submission", "figures")
    if os.path.isdir(sub):
        for ext in ("pdf", "png"):
            src = os.path.join(HERE, "%s.%s" % (name, ext))
            dst = os.path.join(sub, "%s.%s" % (name, ext))
            with open(src, "rb") as fh:
                data = fh.read()
            with open(dst, "wb") as fh:
                fh.write(data)


def bin_mid(s):
    nums = [float(x) for x in re.findall(r"[0-9.]+", s)]
    return 0.5 * (nums[0] + min(nums[1], 1.0))


# ---------------------------------------------------------------------------
# Fig. 2
# ---------------------------------------------------------------------------
def fig2():
    w = pd.read_csv(os.path.join(TAB, "S2_weight_share.csv"))
    sl = pd.read_csv(os.path.join(TAB, "F2a_alpha_slider.csv"))
    fb = pd.read_csv(os.path.join(TAB, "F2b_floorbin.csv"))
    eb = pd.read_csv(os.path.join(FIND, "eb_behavior_2024.csv"))
    fd = pd.read_csv(os.path.join(FIND, "em_farmday_2024_full.csv"),
                     usecols=["farm_id", "kind", "day", "cf"])
    eb["day"] = pd.to_datetime(eb["day"])
    eb["farm_id"] = eb["farm_id"].astype("int64")
    fd["day"] = pd.to_datetime(fd["day"])
    fd["farm_id"] = fd["farm_id"].astype("int64")
    eb = eb.merge(fd, on=["farm_id", "kind", "day"], how="left",
                  validate="one_to_one")
    eb = eb[eb.cf > 0.005].copy()          # 与 T3 同一口径：剔除空转日

    t3 = pd.read_csv(os.path.join(TAB, "T3_behavior.csv")).set_index("kind")

    fig, ax = plt.subplots(2, 2, figsize=(W, 5.55))
    fig.subplots_adjust(left=0.085, right=0.975, bottom=0.085, top=0.95,
                        wspace=0.30, hspace=0.36)

    # (a) time share vs weight share ---------------------------------------
    a = ax[0, 0]
    for kind, col, mk_t, mk_w, lab in (
            ("W", BLUE, "s", "o", "Wind"),
            ("S", ORANGE, "^", "v", "Solar")):
        d = w[w.kind == kind].copy()
        d["x"] = d.pm_over_cap_bin.map(bin_mid)
        d = d.sort_values("x")
        a.plot(d.x, d.share_of_time, color=col, ls=":", lw=0.9,
               marker=mk_t, ms=3.4, mfc="white", mew=0.8, zorder=3,
               label="%s: share of time" % lab)
        a.plot(d.x, d.share_of_weight, color=col, ls="-", lw=1.2,
               marker=mk_w, ms=3.8, zorder=4,
               label="%s: share of weight" % lab)
    a.axvspan(0.0, 0.2, color="0.90", alpha=0.55, zorder=0, lw=0)
    a.axvline(0.2, color="0.45", lw=0.7, ls=(0, (3, 2)), zorder=1)
    a.axvline(0.5, color="0.45", lw=0.7, ls=(0, (3, 2)), zorder=1)
    a.set_xlim(0, 1.0)
    a.set_ylim(0, 1.0)
    a.set_xlabel("Output / installed capacity")
    a.set_ylabel("Share of time or of score weight")
    a.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    a.grid(True, ls=":", color="0.86", lw=0.5)
    a.legend(loc="upper right", bbox_to_anchor=(1.0, 0.78), frameon=False,
             ncol=2, handlelength=1.5, columnspacing=1.0,
             handletextpad=0.4, borderpad=0.15, labelspacing=0.25,
             fontsize=6.3)
    a.text(0.035, 0.955, "below 0.2 $C$:\nwind 80.8%, solar 90.8%\nof score weight",
           ha="left", va="top", fontsize=6.6, linespacing=1.2,
           bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.75",
                     lw=0.4, alpha=0.92))
    a.annotate("above 0.5 $C$: 14.3% of time,\n3.0% of weight (wind)",
               xy=(0.78, 0.05), xytext=(0.42, 0.36), fontsize=6.4,
               ha="left", va="bottom",
               arrowprops=dict(arrowstyle="-|>", lw=0.5, color="0.35",
                               shrinkA=0, shrinkB=2,
                               connectionstyle="arc3,rad=-0.25"))
    panel(a, "a")

    # (b) alpha sweep -------------------------------------------------------
    b = ax[0, 1]
    year_style = {2023: dict(c=SKY, ls="-", mk="s", lw=0.9),
                  2024: dict(c=BLUE, ls="-", mk="o", lw=1.5),
                  2025: dict(c="#003B5C", ls="-", mk="^", lw=0.9)}
    for yr, st in year_style.items():
        d = sl[(sl.year == yr) & (sl.kind == "ALL")].sort_values("alpha")
        b.plot(d.alpha, d.shrink_med, color=st["c"], ls=st["ls"],
               lw=st["lw"], marker=st["mk"], ms=3.8,
               mfc=st["c"] if yr != 2023 else "white", mew=0.8,
               label="%d" % yr, zorder=4 if yr == 2024 else 3)
        if yr == 2024:
            b.fill_between(d.alpha, d.lo, d.hi, color=BLUE, alpha=0.14,
                           lw=0, zorder=1)
    for kind, col, ls, mk, lab in (
            ("W", GREEN, (0, (5, 1.5, 1, 1.5)), "D", "2024 wind"),
            ("S", VERM, (0, (3, 1.2)), "o", "2024 solar")):
        d = sl[(sl.year == 2024) & (sl.kind == kind)].sort_values("alpha")
        b.plot(d.alpha, d.shrink_med, color=col, ls=ls, lw=1.0,
               marker=mk, ms=3.2, mfc="white", mew=0.8, label=lab, zorder=2)
    b.set_xscale("log")
    b.set_xlim(0.017, 1.15)
    b.set_ylim(-1.02, 0.10)
    b.axhline(0, color="0.25", lw=0.7, zorder=1)
    b.axvline(0.2, color="0.45", lw=0.7, ls=(0, (3, 2)), zorder=1)
    b.axvline(1.0, color="0.45", lw=0.7, ls=(0, (3, 2)), zorder=1)
    b.set_xticks([0.02, 0.05, 0.1, 0.2, 0.5, 1.0])
    b.set_xticklabels(["0.02", "0.05", "0.1", "0.2", "0.5", "1"])
    b.minorticks_off()
    b.set_xlabel(r"Floor level $\alpha$ in $d=\max(p,\alpha\,\mathrm{Cap})$")
    b.set_ylabel(r"Median reporting tilt  $m^{*}/\bar{p}-1$")
    b.grid(True, which="major", ls=":", color="0.86", lw=0.5)
    b.legend(loc="lower right", frameon=False, ncol=2, handlelength=1.4,
             columnspacing=1.0, handletextpad=0.4, borderpad=0.12,
             labelspacing=0.22, fontsize=6.2)
    b.text(0.2, 0.065, "regional 0.20", ha="center", va="bottom",
           fontsize=6.0, color="0.35")
    b.text(1.0, 0.065, "national 1.0", ha="right", va="bottom",
           fontsize=6.0, color="0.35")
    panel(b, "b")

    # (c) floor-binding dose response -------------------------------------
    c = ax[1, 0]
    d = fb.copy()
    d["x"] = d.fb.map(bin_mid)
    c.axvspan(0.6, 0.7, color=ORANGE, alpha=0.13, lw=0, zorder=0)
    c2 = c.twinx()
    c2.bar(d.x, d.share, width=0.075, color="0.80", alpha=0.55,
           edgecolor="none", zorder=0)
    c2.set_ylim(0, 0.26)
    c2.set_ylabel("Share of farm-days", color="0.45", fontsize=7)
    c2.tick_params(axis="y", colors="0.45", labelsize=6.5)
    c2.spines["right"].set_color("0.65")
    c2.spines["top"].set_visible(False)
    c.plot(d.x, d.shrink_med, color=BLUE, lw=1.3, zorder=3,
           label="Median tilt")
    c.scatter(d.x, d.shrink_med, s=np.sqrt(d.share.values) * 70,
              facecolors="white", edgecolors=BLUE, linewidths=0.9,
              zorder=4)
    c.axhline(0, color="0.25", lw=0.7, zorder=1)
    c.set_xlim(0, 1.02)
    c.set_ylim(-0.72, 0.12)
    c.set_xlabel("Share of intervals in which the floor binds")
    c.set_ylabel(r"Median reporting tilt  $m^{*}/\bar{p}-1$")
    c.grid(True, axis="y", ls=":", color="0.86", lw=0.5)
    c.annotate("peak $-0.645$\n(60--70% floor-bound)",
               xy=(0.65, -0.645), xytext=(0.26, -0.45),
               fontsize=6.4, ha="left", va="center",
               arrowprops=dict(arrowstyle="-|>", lw=0.55, color="0.30",
                               shrinkA=0, shrinkB=2,
                               connectionstyle="arc3,rad=-0.2"))
    c.annotate("fully floored: 0.000\n$n=5{,}004$ (14.8%)",
               xy=(0.995, 0.0), xytext=(0.55, 0.085),
               fontsize=6.4, ha="left", va="top",
               arrowprops=dict(arrowstyle="-|>", lw=0.55, color="0.30",
                               shrinkA=0, shrinkB=2,
                               connectionstyle="arc3,rad=0.25"))
    c.text(0.02, 0.97, "Dot size varies with share of farm-days",
           transform=c.transAxes, ha="left", va="top", fontsize=6.2)
    panel(c, "c")

    # (d) joint distribution of b* ----------------------------------------
    cell = ax[1, 1].get_subplotspec()
    ax[1, 1].set_visible(False)
    gs = gridspec.GridSpecFromSubplotSpec(
        2, 2, subplot_spec=cell, width_ratios=[4.0, 1.0],
        height_ratios=[1.0, 4.0], wspace=0.06, hspace=0.06)
    dmain = fig.add_subplot(gs[1, 0])
    dtop = fig.add_subplot(gs[0, 0], sharex=dmain)
    dright = fig.add_subplot(gs[1, 1], sharey=dmain)

    dd = eb.dropna(subset=["b_cap", "b_flo", "delta"]).copy()
    sub = dd[(dd.b_cap > 0.3) & (dd.b_cap < 1.9) &
             (dd.b_flo > 0.3) & (dd.b_flo < 1.9)]
    hb = dmain.hexbin(sub.b_cap, sub.b_flo, gridsize=52, cmap="cividis",
                      mincnt=1, bins="log", linewidths=0,
                      extent=(0.3, 1.9, 0.3, 1.9))
    dmain.plot([0.3, 1.9], [0.3, 1.9], color="0.25", lw=0.8,
               ls=(0, (3, 2)), zorder=5)
    mc, mf = dd.b_cap.median(), dd.b_flo.median()
    dm = dd.delta.median()
    share_neg = (dd.delta < 0).mean()
    dmain.plot([mc], [mf], marker="o", ms=5.0, mfc="white", mec="black",
               mew=1.0, zorder=8)
    dmain.set_xlim(0.3, 1.9)
    dmain.set_ylim(0.3, 1.9)
    dmain.set_xlabel(r"$b^{*}$ under capacity normaliser")
    dmain.set_ylabel(r"$b^{*}$ under floored normaliser")
    dmain.grid(True, ls=":", color="0.86", lw=0.5)
    dmain.text(0.325, 1.875,
               "$n=15{,}176$ (cf $>0.005$)\n"
               "median $b^{*}_{\\mathrm{cap}}=%.3f$\n"
               "median $b^{*}_{\\mathrm{flo}}=%.3f$\n"
               "median $\\Delta=%.3f$\n"
               "$%.1f\\%%$ below diagonal; placebo $0.000$"
               % (mc, mf, dm, 100 * share_neg),
               ha="left", va="top", fontsize=6.3, linespacing=1.2,
               bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.7",
                         lw=0.45, alpha=0.93), zorder=9)
    dmain.text(1.88, 0.33, "shade: log count", ha="right", va="bottom",
               fontsize=5.8, color="0.35")

    bins = np.linspace(0.3, 1.9, 42)
    dtop.hist([dd[dd.kind == "W"].b_cap, dd[dd.kind == "S"].b_cap],
              bins=bins, stacked=True, color=[BLUE, ORANGE], alpha=0.85,
              linewidth=0)
    dtop.axvline(mc, color="black", lw=0.7, ls=":")
    dtop.set_ylabel("")
    dtop.tick_params(axis="y", left=False, labelleft=False)
    dtop.tick_params(axis="x", bottom=False, labelbottom=False)

    hw, edges = np.histogram(dd[dd.kind == "W"].b_flo, bins=bins)
    hs, _ = np.histogram(dd[dd.kind == "S"].b_flo, bins=bins)
    centers = 0.5 * (edges[:-1] + edges[1:])
    dright.barh(centers, hw, height=bins[1] - bins[0], color=BLUE,
                alpha=0.85, linewidth=0)
    dright.barh(centers, hs, left=hw, height=bins[1] - bins[0],
                color=ORANGE, alpha=0.85, linewidth=0)
    dright.axhline(mf, color="black", lw=0.7, ls=":")
    dright.set_xlabel("")
    dright.tick_params(axis="x", bottom=False, labelbottom=False)
    dright.tick_params(axis="y", left=False, labelleft=False)

    dtop.set_title("(d)", loc="left", fontsize=9, fontweight="bold", pad=2)

    save(fig, "fig2_rules_cost")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fig. 3
# ---------------------------------------------------------------------------
def fig3():
    dec = pd.read_csv(os.path.join(TAB, "F3a_waterfall.csv"))
    t2 = pd.read_csv(os.path.join(TAB, "T2_decomposition.csv"))
    pen = pd.read_csv(os.path.join(TAB, "F3b_penalty_mwh.csv"))
    ref = pd.read_csv(os.path.join(TAB, "S4_reference_normalizer.csv"))
    d = pd.read_csv(os.path.join(FIND, "em_farmday_2024_full.csv"))
    d = d[(d.cf > 0.005) & d.acc_flo.notna() & d.acc_cap.notna()]

    fig, ax = plt.subplots(2, 2, figsize=(W, 5.55))
    fig.subplots_adjust(left=0.085, right=0.975, bottom=0.085, top=0.95,
                        wspace=0.30, hspace=0.36)

    # (a) waterfall --------------------------------------------------------
    a = ax[0, 0]
    base = 55.0
    vals = dec.value.values
    tops = dec.cumulative.values
    bottoms = np.array([base, dec.cumulative.values[0],
                        dec.cumulative.values[1], dec.cumulative.values[2],
                        base])
    names = ["Plant\nmean", "Capacity\nweighting", "Error\ncancellation",
             "Denominator", "Provincial\nscore"]
    cols = [SKY, GREEN, GREEN, VERM, SKY]
    for i in range(5):
        a.bar(i, tops[i] - bottoms[i], bottom=bottoms[i], width=0.62,
              color=cols[i], edgecolor="black", lw=0.7, zorder=2)
        lab = ("82.6" if i == 4 else
               ("%.1f" % vals[i] if i == 0 else "%+.1f" % vals[i]))
        if i in (0, 4) or vals[i] >= 0:
            a.text(i, tops[i] + 1.0, lab, ha="center", va="bottom",
                   fontsize=7.2)
        else:
            a.text(i, tops[i] - 1.0, lab, ha="center", va="top",
                   fontsize=7.2)
    for i in range(4):
        a.plot([i + 0.31, i + 1 - 0.31], [tops[i], tops[i]], color="0.25",
               lw=0.6, ls=":", zorder=1)
    a.set_xticks(range(5))
    a.set_xticklabels(names, fontsize=6.6)
    a.set_ylim(base, 101)
    a.set_ylabel("Accuracy score (points)")
    a.grid(True, axis="y", ls=":", color="0.86", lw=0.5)

    r24 = t2[(t2.year == 2024) & (t2.kind == "ALL")].iloc[0]
    a.text(2.0, 56.2,
           "net gap %.1f = %.1f + %.1f $-$ %.1f\n"
           "A$>0$ and B$<0$ on 366/366 days"
           % (r24.gain, r24.weight, r24.A, -r24.B),
           ha="center", va="bottom", fontsize=6.5,
           linespacing=1.25,
           bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.75",
                     lw=0.45, alpha=0.92))
    panel(a, "a")

    # (b) score distributions ---------------------------------------------
    b = ax[0, 1]
    bins = np.linspace(-50, 100, 61)
    b.hist(d.acc_flo, bins=bins, density=True, histtype="stepfilled",
           color=BLUE, alpha=0.20, edgecolor=BLUE, lw=1.0, zorder=2,
           label="Regional formula (mean 62.5)")
    b.hist(d.acc_cap, bins=bins, density=True, histtype="stepfilled",
           color=GREEN, alpha=0.18, edgecolor=GREEN, lw=1.0,
           linestyle="--", zorder=3,
           label="National formula (mean 88.3)")
    b.axvline(d.acc_flo.mean(), color=BLUE, lw=0.9, ls="--", zorder=4)
    b.axvline(d.acc_cap.mean(), color=GREEN, lw=0.9, ls="--", zorder=4)
    for th in (60, 65):
        b.axvline(th, color="0.35", lw=0.7, ls=":", zorder=1)
    b.text(57.5, 0.041, "thresholds\n60 / 65", ha="right", va="top",
           fontsize=6.2, color="0.35", linespacing=1.1)
    b.set_xlim(-50, 100)
    b.set_ylim(0, 0.047)
    b.set_xlabel("Accuracy score (points)")
    b.set_ylabel("Density")
    b.grid(True, axis="y", ls=":", color="0.86", lw=0.5)
    b.legend(loc="lower left", frameon=False, handlelength=1.3,
             borderpad=0.05, labelspacing=0.25, fontsize=6.4)
    yarrow = 0.0405
    b.annotate("", xy=(88.3, yarrow), xytext=(62.5, yarrow),
               arrowprops=dict(arrowstyle="<->", lw=0.7, color="0.25"))
    b.text(75.4, yarrow - 0.0012, "25.8 points", ha="center", va="top",
           fontsize=6.4, color="0.25")
    panel(b, "b")

    # (c) assessed energy --------------------------------------------------
    c = ax[1, 0]
    kinds = ["Wind", "Solar"]
    old = pen.penalty_old_MWh_per_farmday.values
    new = pen.penalty_new_MWh_per_farmday.values
    ypos = [1.0, 0.0]
    ccols = [BLUE, ORANGE]
    for y, o, n, col, lab in zip(ypos, old, new, ccols, kinds):
        c.plot([o, n], [y, y], color=col, lw=1.4, zorder=2)
        c.plot([o], [y], marker="o", ms=6.0, color=col, mec="black",
               mew=0.7, zorder=3)
        c.plot([n], [y], marker="o", ms=6.0, mfc="white", mec=col,
               mew=1.2, zorder=3)
        c.text(o * 1.13, y + 0.13, "%.1f" % (o + 1e-9), ha="left",
               va="bottom", fontsize=7.0, color=col) if o <= 500 else c.text(
            o * 0.85, y + 0.13, "%.1f" % (o + 1e-9), ha="right",
            va="bottom", fontsize=7.0, color=col)
        c.text(n * 1.13, y - 0.17, "%.1f" % (n + 1e-9), ha="left",
               va="top", fontsize=7.0, color=col)
        red = 100 * (1.0 - n / o)
        c.text(0.5 * (o + n) * 0.95, y + 0.10, "%.1f%% lower" % red,
               ha="center", va="bottom", fontsize=6.4, color="0.30")
    c.set_xscale("log")
    c.set_xlim(1.0, 1200)
    c.set_ylim(-0.45, 1.55)
    c.set_yticks(ypos)
    c.set_yticklabels(kinds)
    c.set_xticks([1, 10, 100, 1000])
    c.minorticks_off()
    c.set_xlabel("Assessed energy (MWh per farm-day, log scale)")
    c.grid(True, axis="x", which="major", ls=":", color="0.86", lw=0.5)
    c.plot([], [], marker="o", ms=5.0, color="0.35", ls="none",
           label="Floored denominator (current)")
    c.plot([], [], marker="o", ms=5.0, mfc="white", mec="0.35", mew=1.0,
           ls="none", label="Capacity denominator")
    c.legend(loc="upper right", frameon=False, handlelength=1.2,
             borderpad=0.05, fontsize=6.3)
    c.text(0.02, 0.03,
           "Share of farm-days with a penalty: "
           "51.0% $\\rightarrow$ 1.4% (wind); 30.1% $\\rightarrow$ 0.2% (solar)",
           transform=c.transAxes, ha="left", va="bottom", fontsize=6.4,
           bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="0.75",
                     lw=0.4, alpha=0.92))
    panel(c, "c")

    # (d) compliance shift under the reference curve ----------------------
    dax = ax[1, 1]
    rr = ref.set_index("kind")
    series = [
        ("Wind", 100 * rr.loc["W", "compliance_old"], 100 * rr.loc["W", "compliance_new"], BLUE),
        ("Solar", 100 * rr.loc["S", "compliance_old"], 100 * rr.loc["S", "compliance_new"], ORANGE),
        ("All", 100 * rr.loc["ALL", "compliance_old"], 100 * rr.loc["ALL", "compliance_new"], GREY),
    ]
    xs = [0, 1]
    # 右端点三条线的 y1 相差不到 1 pp，标签按排序错开后用点线引回端点
    ends = sorted(series, key=lambda s: s[2])
    lab_y = {s[0]: ends[0][2] + k * 1.7 for k, s in enumerate(ends)}
    for lab, y0, y1, col in series:
        ls = (0, (3, 1.5)) if lab == "All" else "-"
        dax.plot(xs, [y0, y1], color=col, ls=ls, lw=1.3, marker="o",
                 ms=5.0, mfc="white", mew=1.0, zorder=3)
        dax.text(-0.06, y0, "%.1f%%" % y0, ha="right", va="center",
                 fontsize=6.6, color=col)
        yl = lab_y[lab]
        dax.plot([1.0, 1.05], [y1, yl], color=col, lw=0.5, ls=(0, (1, 1)),
                 zorder=2)
        dax.text(1.06, yl, "%.1f%%" % y1, ha="left", va="center",
                 fontsize=6.6, color=col)
        dax.text(1.30, yl, "%+.1f pp" % (y1 - y0), ha="left", va="center",
                 fontsize=6.4, color=col)
    dax.set_xlim(-0.35, 1.62)
    dax.set_ylim(40, 75)
    dax.set_xticks(xs)
    dax.set_xticklabels(["Current rule\n(existing $\\theta$)",
                         "Reference curve\n(existing $\\theta$)"])
    dax.set_ylabel("Share meeting threshold (%)")
    dax.grid(True, axis="y", ls=":", color="0.86", lw=0.5)
    # 新旧两条线交叉处（排序反转）
    w0, w1 = 100 * rr.loc["W", "compliance_old"], 100 * rr.loc["W", "compliance_new"]
    s0, s1 = 100 * rr.loc["S", "compliance_old"], 100 * rr.loc["S", "compliance_new"]
    tc = (s0 - w0) / ((w1 - w0) - (s1 - s0))
    yc = w0 + (w1 - w0) * tc
    dax.annotate("ranking\nreverses", xy=(tc, yc), xytext=(0.62, 46.6),
                 ha="left", va="top", fontsize=6.2, color="0.35",
                 linespacing=1.05,
                 arrowprops=dict(arrowstyle="-|>", lw=0.5, color="0.35",
                                 shrinkA=0, shrinkB=2,
                                 connectionstyle="arc3,rad=0.2"),
                 bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none",
                           alpha=0.85))
    theta = float(rr.loc["ALL", "theta_calibrated"])
    dax.text(0.02, 0.035,
             "recalibrated $\\theta$=%.1f:\n"
             "all %.1f%%, wind %.1f%%, solar %.1f%%"
             % (theta,
                100 * rr.loc["ALL", "compliance_new_calibrated"],
                100 * rr.loc["W", "compliance_new_calibrated"],
                100 * rr.loc["S", "compliance_new_calibrated"]),
             transform=dax.transAxes, ha="left", va="bottom", fontsize=6.2,
             linespacing=1.15,
             bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="0.75",
                       lw=0.4, alpha=0.92))
    panel(dax, "d")

    save(fig, "fig3_consequences")
    plt.close(fig)


if __name__ == "__main__":
    fig2()
    fig3()
    print("written: fig2_rules_cost, fig3_consequences")
