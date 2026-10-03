"""Step 6: charts.   ./venv/bin/python charts.py -> charts/00_cover.png, 01_zipf_heaps.png, 02_top_words.png, 03_whale_chapters.png, 04_dispersion.png"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).parent
R = HERE / "results"
INK, DIM, GRID, BG, BLUE, ORANGE, GRAY, GREEN = "#f2f2f0", "#8a8a87", "#1d1d1d", "#0b0b0b", "#3987e5", "#d95926", "#9a9a96", "#3aa876"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
                     "axes.edgecolor": "#3a3a3a", "axes.labelcolor": DIM, "xtick.color": DIM, "ytick.color": DIM,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 11, "axes.titlesize": 13,
                     "axes.titlelocation": "left", "axes.titlepad": 12})


def save(fig, name):
    fig.tight_layout(); fig.savefig(HERE / "charts" / name, dpi=150); plt.close(fig)


def top_words(ax):
    t = pd.read_csv(R / "top_words.csv"); t = t[t["list"] == "without stopwords"].head(20); y = np.arange(len(t))[::-1]
    ax.barh(y, t["count"], color=[ORANGE if w == "whale" else BLUE for w in t["word"]], height=0.7)
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.text(r["count"] + 12, yi, f"{r['count']:,}", va="center", color=INK, fontsize=9)
    ax.set_yticks(y); ax.set_yticklabels(t["word"]); ax.set_xlim(0, 1250); ax.set_xlabel("times used"); ax.grid(axis="y", visible=False); ax.set_title("The 20 most-used words, stop words removed")


def dispersion(ax):
    k = pd.read_csv(R / "key_words_by_tenth.csv")
    rows = [("whale_family_per_10k", "whale (any form)"), ("ahab_per_10k", "Ahab"), ("queequeg_per_10k", "Queequeg"), ("starbuck_per_10k", "Starbuck"), ("pequod_per_10k", "Pequod"), ("white_per_10k", "white"), ("ishmael_per_10k", "Ishmael")]
    m = np.array([k[c] for c, _ in rows]); norm = m / m.max(axis=1, keepdims=True)
    ax.imshow(norm, aspect="auto", cmap=LinearSegmentedColormap.from_list("d", ["#121212", "#1d4f8a", BLUE, "#9cc4f5"]))
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m[i, j]:.0f}", ha="center", va="center", fontsize=8.5, color=INK if norm[i, j] > 0.35 else DIM)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([n for _, n in rows]); ax.set_xticks(range(10)); ax.set_xticklabels([str(i) for i in range(1, 11)])
    ax.set_xlabel("tenth of the book, in order (uses per 10,000 words)"); ax.grid(False); ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Where in the book each word falls")


def main():
    (HERE / "charts").mkdir(exist_ok=True)
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={"width_ratios": [1.15, 1]})
    dispersion(a); top_words(b)
    for ax in (a, b):
        ax.title.set_fontsize(15)
    fig.suptitle("What is Moby-Dick made of? 213,516 words, counted", x=0.01, ha="left", fontsize=20, color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(HERE / "charts" / "00_cover.png", dpi=100); plt.close(fig)

    z = pd.read_csv(R / "zipf.csv"); zj = json.load(open(R / "zipf.json")); h = pd.read_csv(R / "heaps.csv"); hj = json.load(open(R / "heaps.json")); s = json.load(open(R / "summary.json"))
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.8))
    a.scatter(z["rank"], z["count"], s=6, color=BLUE, alpha=0.7, linewidths=0); xs = np.array([1, 1000]); a.plot(xs, 10 ** zj["intercept"] * xs ** zj["slope"], color=ORANGE, linewidth=1.6)
    for w in ("the", "whale", "ahab"):
        r = z[z["word"] == w].iloc[0]; a.annotate(w, (r["rank"], r["count"]), (r["rank"] * 1.5, r["count"] * 1.6), color=INK, fontsize=9, arrowprops={"arrowstyle": "-", "color": DIM, "linewidth": 0.6})
    a.set_xscale("log"); a.set_yscale("log"); a.set_xlabel("rank of the word, most common first"); a.set_ylabel("times used")
    a.text(1.4, 2, f"slope {zj['slope']:.2f}, R² {zj['r2']:.3f}", color=ORANGE, fontsize=10); a.set_title("Zipf's law: frequency against rank")
    b.plot(h["tokens"], h["distinct_words"], color=BLUE, linewidth=2); b.plot(h["tokens"], hj["k"] * h["tokens"] ** hj["beta"], color=ORANGE, linestyle="--", linewidth=1.2)
    b.text(h["tokens"].iloc[-1], h["distinct_words"].iloc[-1] + 500, f"{s['distinct_words']:,} words", ha="right", color=INK, fontsize=9); b.text(15000, 14000, f"vocabulary ∝ length^{hj['beta']:.2f}", color=ORANGE, fontsize=10)
    b.set_xlabel("words read so far"); b.set_ylabel("distinct words"); b.set_title("Heaps' law: the vocabulary keeps growing"); b.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x / 1000)}k"))
    save(fig, "01_zipf_heaps.png")

    fig, ax = plt.subplots(figsize=(10, 4.4)); top_words(ax); save(fig, "02_top_words.png")

    c = pd.read_csv(R / "chapters.csv"); c = c[c["key"].str.isdigit()].assign(n=lambda d: d["key"].astype(int)); fig, ax = plt.subplots(figsize=(10, 3.8))
    big = c.nlargest(5, "whale_per_1000")
    ax.bar(c["n"], c["whale_per_1000"], color=[ORANGE if n in set(big["n"]) else BLUE for n in c["n"]], width=0.8)
    for _, r in big.iterrows():
        ax.text(r["n"], r["whale_per_1000"] + 0.8, str(r["n"]), ha="center", color=INK, fontsize=9)
    ax.set_xlabel("chapter"); ax.set_ylabel("whale words per 1,000 words"); ax.set_xlim(0, 136); ax.grid(axis="x", visible=False)
    ax.set_title("Whale density by chapter: 24, 32 and 55 to 57 lead")
    save(fig, "03_whale_chapters.png")

    fig, ax = plt.subplots(figsize=(10, 4.0)); dispersion(ax); save(fig, "04_dispersion.png")


if __name__ == "__main__":
    main()
