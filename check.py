"""Step 5: the project's check. Recount everything from the raw Gutenberg text with different code from analyze.py: a character-by-character scanner instead of a
regular expression, headings found line by line, least squares written out by hand, and only the standard library (the stop-word list is read from results/stopwords.txt).

    ./venv/bin/python check.py
"""
import csv
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
R = HERE / "results"
KEY_WORDS = ["queequeg", "ishmael", "ahab", "starbuck", "pequod", "white"]
n_ok = 0


def same(label, got, want, tol=1e-9):
    global n_ok
    n_ok += 1
    assert abs(float(got) - float(want)) <= tol * max(1.0, abs(float(want))), f"{label}: recount {got} != results {want}"


def table(name):
    return list(csv.DictReader(open(R / name)))


def scan(text, hyphens=True, possessive_strip=True):
    """a word is letters, with an apostrophe or hyphen allowed only between two letters"""
    text = text.lower().replace("’", "'").replace("‘", "'")
    out, cur, i = [], "", 0
    while i < len(text):
        c = text[i]
        if "a" <= c <= "z":
            cur += c
        elif c in "'-" and cur and i + 1 < len(text) and "a" <= text[i + 1] <= "z" and (c == "'" or hyphens):
            cur += c
        else:
            if cur:
                out.append(cur)
            cur = ""
        i += 1
    if cur:
        out.append(cur)
    return [w[:-2] if possessive_strip and w.endswith("'s") else w for w in out]


def sections():
    lines = open(HERE / "data" / "pg2701.txt", encoding="utf-8").read().replace("\r", "").split("\n")
    s = next(i for i, l in enumerate(lines) if l.startswith("*** START OF THE PROJECT GUTENBERG EBOOK"))
    e = next(i for i, l in enumerate(lines) if l.startswith("*** END OF THE PROJECT GUTENBERG EBOOK"))
    where = {}
    for i in range(s + 1, e):
        l = lines[i].rstrip()
        parts = l.split(" ")
        if l.startswith("CHAPTER ") and len(parts) > 1 and parts[1].endswith(".") and parts[1][:-1].isdigit():
            where[parts[1][:-1]] = i                             # the last line with this heading is the real one
        elif l == "ETYMOLOGY.":
            where["Etymology"] = i
        elif l.startswith("EXTRACTS"):
            where["Extracts"] = i
        elif l == "Epilogue":
            where["Epilogue"] = i
    order = sorted(where.items(), key=lambda kv: kv[1])
    return [(k, "\n".join(lines[i + 1:(order[j + 1][1] if j + 1 < len(order) else e)])) for j, (k, i) in enumerate(order)]


def fit(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx, sxy, syy = sum((x - mx) ** 2 for x in xs), sum((x - mx) * (y - my) for x, y in zip(xs, ys)), sum((y - my) ** 2 for y in ys)
    return sxy / sxx, my - sxy / sxx * mx, sxy * sxy / (sxx * syy)


def main():
    secs = sections()
    toks = [(k, scan(t)) for k, t in secs]
    book = [w for _, ts in toks for w in ts]
    cnt, n = Counter(book), len(book)
    stop = set(open(R / "stopwords.txt").read().split())
    s = json.load(open(R / "summary.json"))
    same("sections", len(secs), s["sections"], 0); same("chapters", sum(k.isdigit() for k, _ in secs), s["chapters"], 0)
    same("tokens", n, s["tokens"], 0); same("distinct words", len(cnt), s["distinct_words"], 0)
    hapax = sum(1 for c in cnt.values() if c == 1)
    same("hapax", hapax, s["hapax"], 0); same("hapax share of vocabulary", 100 * hapax / len(cnt), s["hapax_share_of_vocabulary_pct"]); same("hapax share of tokens", 100 * hapax / n, s["hapax_share_of_tokens_pct"])
    same("mean word length", sum(map(len, book)) / n, s["mean_word_length"]); wf = sum(1 for w in book if "whal" in w)
    same("whale family", wf, s["whale_family_tokens"], 0); same("whale family per 1000", 1000 * wf / n, s["whale_family_per_1000"])

    for r in table("tokenization.csv"):                                   # the effect of the tokenising choices
        ws = book if r["choice"].startswith("hyphens kept") else scan("\n".join(t for _, t in secs), hyphens=False) if r["choice"] == "hyphens split" else scan("\n".join(t for _, t in secs), possessive_strip=False)
        c = Counter(ws)
        same(r["choice"] + " tokens", len(ws), r["tokens"], 0); same(r["choice"] + " distinct", len(c), r["distinct_words"], 0)
        same(r["choice"] + " hapax", sum(1 for x in c.values() if x == 1), r["hapax"], 0)
        same(r["choice"] + " rank of whale", 1 + sorted(c, key=lambda w: (-c[w], w)).index("whale"), r["whale_rank"], 0)

    ranked = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
    plain = [(w, c) for w, c in ranked if w not in stop]
    all_rows = [r for r in table("top_words.csv")]
    for lst, src in (("all words", ranked), ("without stopwords", plain)):
        for i, r in enumerate([r for r in all_rows if r["list"] == lst]):
            assert src[i][0] == r["word"], f"{lst} #{i}: {src[i][0]} vs {r['word']}"
            same(f"{lst} {r['word']} count", src[i][1], r["count"], 0); same(f"{lst} {r['word']} per 10k", 10000 * src[i][1] / n, r["per_10k"], 0.0501)
    for i, r in enumerate(table("zipf.csv")):
        assert ranked[i][0] == r["word"] and ranked[i][1] == int(r["count"]), f"zipf row {i}"
    same("zipf rows", len(table("zipf.csv")), 1000, 0)
    zs, zi, zr2 = fit([math.log10(i + 1) for i in range(1000)], [math.log10(c) for _, c in ranked[:1000]])
    z = json.load(open(R / "zipf.json"))
    same("zipf slope", zs, z["slope"], 1e-9); same("zipf intercept", zi, z["intercept"], 1e-9); same("zipf r2", zr2, z["r2"], 1e-9)
    same("share of 'the'", 100 * cnt["the"] / n, z["the_share_pct"]); same("top 10 share", 100 * sum(c for _, c in ranked[:10]) / n, z["top10_share_pct"]); same("top 100 share", 100 * sum(c for _, c in ranked[:100]) / n, z["top100_share_pct"])
    seen, growth = set(), []
    for i, w in enumerate(book, 1):
        seen.add(w)
        if i % 1000 == 0:
            growth.append((i, len(seen)))
    for r in table("heaps.csv"):
        assert growth[int(r["tokens"]) // 1000 - 1] == (int(r["tokens"]), int(r["distinct_words"])), f"heaps {r['tokens']}"
    same("heaps rows", len(table("heaps.csv")), len(growth), 0)
    hb, ha, hr2 = fit([math.log10(i) for i, _ in growth], [math.log10(v) for _, v in growth])
    h = json.load(open(R / "heaps.json"))
    same("heaps beta", hb, h["beta"], 1e-9); same("heaps k", 10 ** ha, h["k"], 1e-9); same("heaps r2", hr2, h["r2"], 1e-9)

    for (k, ts), r in zip(toks, table("chapters.csv")):                    # chapters
        c = Counter(ts)
        assert k == r["key"], f"chapter order {k} vs {r['key']}"
        same(f"{k} words", len(ts), r["words"], 0); same(f"{k} whale family", sum(1 for w in ts if "whal" in w), r["whale_family"], 0)
        same(f"{k} whale per 1000", 1000 * sum(1 for w in ts if "whal" in w) / len(ts), r["whale_per_1000"], 0.0501)
        for w in KEY_WORDS:
            same(f"{k} {w}", c[w], r[w], 0)
    for i, r in enumerate(table("key_words_by_tenth.csv")):                # the ten tenths of the book, by word position
        part = [w for j, w in enumerate(book) if min(9, j * 10 // n) == i]
        same(f"tenth {i + 1} words", len(part), r["words"], 0); same(f"tenth {i + 1} whale family", 10000 * sum(1 for w in part if "whal" in w) / len(part), r["whale_family_per_10k"], 0.0501)
        c = Counter(part)
        for w in KEY_WORDS:
            same(f"tenth {i + 1} {w}", 10000 * c[w] / len(part), r[w + "_per_10k"], 0.0501)
    third = n // 3
    a, b = Counter(book[:third]), Counter(book[-third:])
    na, nb = sum(a.values()), sum(b.values())
    ratio = {w: math.log(((b[w] + 0.5) / (nb + 0.5)) / ((a[w] + 0.5) / (na + 0.5))) for w in set(a) | set(b) if w not in stop and a[w] + b[w] >= 25}
    low, high = sorted(ratio, key=lambda w: ratio[w])[:12], sorted(ratio, key=lambda w: -ratio[w])[:12]
    rows = table("distinctive.csv")
    assert [r["word"] for r in rows[:12]] == low and [r["word"] for r in rows[12:]] == high, "distinctive words differ"
    for r in rows:
        same(r["word"] + " first third", a[r["word"]], r["first_third"], 0); same(r["word"] + " last third", b[r["word"]], r["last_third"], 0); same(r["word"] + " log ratio", ratio[r["word"]], r["log_ratio"], 0.0006)
    print(f"check.py: {n_ok} recounts agree with results/")


if __name__ == "__main__":
    main()
