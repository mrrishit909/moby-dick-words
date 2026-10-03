"""Steps 2-4: split the book into chapters, tokenise, count, and test two laws of language (Zipf and Heaps), then see where the words fall.

    ./venv/bin/python analyze.py
        -> results/summary.json  tokenization.csv  top_words.csv  stopwords.txt  zipf.csv  zipf.json  heaps.csv  heaps.json  chapters.csv  key_words_by_tenth.csv  distinctive.csv
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

HERE = Path(__file__).parent
R = HERE / "results"
HEAD = re.compile(r"^(CHAPTER (\d+)\.[^\n]*|ETYMOLOGY\.|EXTRACTS[^\n]*|Epilogue)[ \t\r]*$", re.M)
KEY_WORDS = ["queequeg", "ishmael", "ahab", "starbuck", "pequod", "white"]
STOP = sorted(ENGLISH_STOP_WORDS)


def sections():
    """Step 2. Cut off the Gutenberg licence, then split at the headings. The contents list repeats every heading, so the LAST match of each is the real one."""
    t = open(HERE / "data" / "pg2701.txt", encoding="utf-8").read().replace("\r", "")
    body = t[t.index("*** START OF THE PROJECT GUTENBERG EBOOK"):t.index("*** END OF THE PROJECT GUTENBERG EBOOK")]
    body = body[body.index("\n", 0) + 1:]
    last = {}
    for m in HEAD.finditer(body):
        last[m.group(2) or m.group(1).split(" ")[0].rstrip(".")] = m
    marks = sorted(last.values(), key=lambda m: m.start())
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        out.append({"key": m.group(2) or m.group(1).split(" ")[0].rstrip(".").title(), "heading": m.group(1).strip(), "text": body[m.end():end]})
    return out


def tokens(text, hyphens="keep", possessive="strip"):
    """Lower-case words. Curly quotes and dashes are normalised, the em dash separates words, hyphens are kept inside a word (or split), 's is dropped (or kept)."""
    t = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", " ").replace("–", " ")
    words = re.findall(r"[a-z]+(?:['-][a-z]+)*", t) if hyphens == "keep" else re.findall(r"[a-z]+(?:'[a-z]+)*", t)
    return [re.sub(r"'s$", "", w) for w in words] if possessive == "strip" else words


def main():
    R.mkdir(exist_ok=True)
    secs = sections()
    toks = [tokens(s["text"]) for s in secs]
    book = [w for ts in toks for w in ts]
    cnt = Counter(book)
    n, v = len(book), len(cnt)
    hapax = sum(1 for c in cnt.values() if c == 1)
    (R / "stopwords.txt").write_text("\n".join(STOP) + "\n")

    # Step 3a: how much do the tokenising choices matter?
    rows = []
    for name, kw in [("hyphens kept, 's dropped (used here)", {}), ("hyphens split", {"hyphens": "split"}), ("'s kept as part of the word", {"possessive": "keep"})]:
        ws = [w for s in secs for w in tokens(s["text"], **kw)]
        c = Counter(ws)
        rows.append({"choice": name, "tokens": len(ws), "distinct_words": len(c), "hapax": sum(1 for x in c.values() if x == 1), "whale_rank": sorted(c, key=lambda w: (-c[w], w)).index("whale") + 1})
    pd.DataFrame(rows).to_csv(R / "tokenization.csv", index=False)

    summary = {"sections": len(secs), "chapters": sum(1 for s in secs if s["key"].isdigit()), "tokens": n, "distinct_words": v, "hapax": hapax,
               "hapax_share_of_vocabulary_pct": 100 * hapax / v, "hapax_share_of_tokens_pct": 100 * hapax / n,
               "mean_word_length": sum(len(w) for w in book) / n, "whale_family_tokens": sum(1 for w in book if "whal" in w),
               "whale_family_per_1000": 1000 * sum(1 for w in book if "whal" in w) / n}
    json.dump(summary, open(R / "summary.json", "w"), indent=2)

    stop = set(STOP)
    top = pd.DataFrame([{"word": w, "count": c, "per_10k": round(10000 * c / n, 1), "stopword": w in stop} for w, c in sorted(cnt.items(), key=lambda t: (-t[1], t[0]))[:400]])
    pd.concat([top.head(25).assign(list="all words"), top[~top["stopword"]].head(25).assign(list="without stopwords")]).to_csv(R / "top_words.csv", index=False)

    # Step 3b: Zipf's law (frequency against rank on log-log axes) and Heaps' law (vocabulary against length)
    ranked = sorted(cnt.items(), key=lambda t: (-t[1], t[0]))
    z = pd.DataFrame({"rank": np.arange(1, len(ranked) + 1), "word": [w for w, _ in ranked], "count": [c for _, c in ranked]})
    z.head(1000).to_csv(R / "zipf.csv", index=False)
    f = z[z["rank"] <= 1000]
    b, a = np.polyfit(np.log10(f["rank"]), np.log10(f["count"]), 1)
    r2 = np.corrcoef(np.log10(f["rank"]), np.log10(f["count"]))[0, 1] ** 2
    json.dump({"ranks_fitted": 1000, "slope": float(b), "intercept": float(a), "r2": float(r2), "the_share_pct": 100 * cnt["the"] / n, "top10_share_pct": 100 * sum(c for _, c in ranked[:10]) / n,
               "top100_share_pct": 100 * sum(c for _, c in ranked[:100]) / n}, open(R / "zipf.json", "w"), indent=2)
    seen, growth = set(), []
    for i, w in enumerate(book, 1):
        seen.add(w)
        if i % 1000 == 0:
            growth.append((i, len(seen)))
    h = pd.DataFrame(growth, columns=["tokens", "distinct_words"]); h.to_csv(R / "heaps.csv", index=False)
    hb, ha = np.polyfit(np.log10(h["tokens"]), np.log10(h["distinct_words"]), 1)
    json.dump({"beta": float(hb), "k": float(10 ** ha), "r2": float(np.corrcoef(np.log10(h["tokens"]), np.log10(h["distinct_words"]))[0, 1] ** 2)}, open(R / "heaps.json", "w"), indent=2)

    # Step 4: chapters, where the key words fall, and what changes between the first and last third of the book
    ch = []
    for s, ts in zip(secs, toks):
        c = Counter(ts)
        ch.append({"key": s["key"], "heading": s["heading"], "words": len(ts), "whale_family": sum(1 for w in ts if "whal" in w), **{k: c[k] for k in KEY_WORDS}})
    ch = pd.DataFrame(ch); ch["whale_per_1000"] = (1000 * ch["whale_family"] / ch["words"]).round(1); ch.to_csv(R / "chapters.csv", index=False)
    tenth = [min(9, i * 10 // n) for i in range(n)]
    kt = pd.DataFrame({"tenth": tenth, "word": book}); kt["whale_family"] = kt["word"].str.contains("whal")
    k = pd.DataFrame({"tenth": range(1, 11)}); sizes = kt.groupby("tenth").size().to_numpy()
    k["words"] = sizes
    for w in KEY_WORDS:
        k[w + "_per_10k"] = (10000 * kt[kt["word"] == w].groupby("tenth").size().reindex(range(10), fill_value=0).to_numpy() / sizes).round(1)
    k["whale_family_per_10k"] = (10000 * kt.groupby("tenth")["whale_family"].sum().to_numpy() / sizes).round(1)
    k.to_csv(R / "key_words_by_tenth.csv", index=False)
    third = n // 3
    a_, b_ = Counter(book[:third]), Counter(book[-third:])
    na, nb = sum(a_.values()), sum(b_.values())
    rows = []
    for w in set(a_) | set(b_):
        if w in stop or a_[w] + b_[w] < 25:
            continue
        rows.append({"word": w, "first_third": a_[w], "last_third": b_[w], "log_ratio": math.log(((b_[w] + 0.5) / (nb + 0.5)) / ((a_[w] + 0.5) / (na + 0.5)))})
    d = pd.DataFrame(rows).sort_values("log_ratio")
    pd.concat([d.head(12).assign(side="first third"), d.tail(12).iloc[::-1].assign(side="last third")]).round(3).to_csv(R / "distinctive.csv", index=False)

    print(json.dumps(summary, indent=1)); print(pd.DataFrame(rows).shape); print(pd.read_csv(R / "tokenization.csv").to_string(index=False))
    print(pd.read_csv(R / "top_words.csv").query("list=='without stopwords'").head(12).to_string(index=False))
    print(open(R / "zipf.json").read(), open(R / "heaps.json").read()); print(ch.sort_values("whale_per_1000", ascending=False).head(6)[["key", "heading", "words", "whale_per_1000"]].to_string(index=False))
    print(k.to_string(index=False)); print(pd.read_csv(R / "distinctive.csv").to_string(index=False))


if __name__ == "__main__":
    main()
