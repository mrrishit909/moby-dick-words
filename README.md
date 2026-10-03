# What is Moby-Dick made of?

Every word of *Moby-Dick*, counted: how many words, how many different ones, which are used most, whether the text obeys two famous laws of language
(Zipf's and Heaps'), where the whale and the characters fall in the book, and what changes between its first and last third.

The questions follow DataCamp's "Word Frequency in Classic Novels" project (scrape a novel from Project Gutenberg, clean it, count the words).

Build log: https://mrrishit909.github.io/projects/moby-dick-words/

## Data

*Moby Dick; Or, The Whale* by Herman Melville, Project Gutenberg ebook #2701 (public domain in the United States; Gutenberg's own record says it was most
recently updated on 7 September 2026), pulled 2026-10-03. `download.py` fetches the plain text and records the pull; the text (1.3 MB) is not committed.
Other editions differ a little in spelling and front matter, so counts will differ slightly.

```
./venv/bin/pip install pandas numpy scikit-learn certifi      # in a venv (scikit-learn only for its stop-word list)
./venv/bin/python download.py    # data/pg2701.txt
./venv/bin/python analyze.py     # results/*
./venv/bin/python check.py
./venv/bin/python charts.py
```

## Steps

1. **Download** the text.
2. **Split** it: cut the Gutenberg licence off both ends and split at the headings into Etymology, Extracts, 135 chapters and the Epilogue. The contents list
   repeats every heading, so the last match of each heading is the real one.
3. **Tokenise:** lower-case, curly quotes and dashes normalised, the em dash separates words, hyphenated compounds stay whole ("sperm-whale"), a trailing "'s" is
   dropped. `tokenization.csv` shows what each choice changes.
4. **Count:** words, distinct words, words used once, the top words with and without stop words (scikit-learn's list, saved as `results/stopwords.txt`),
   Zipf's law (log frequency against log rank, ranks 1 to 1,000) and Heaps' law (vocabulary against length).
5. **Place the words:** whale words per 1,000 words in each chapter; Ahab, Queequeg, Ishmael, Starbuck, the Pequod and "white" in each tenth of the book; and the words
   most distinctive of the first and the last third (smoothed log ratio, words used at least 25 times, stop words removed).
6. **Check.** `check.py` recounts everything from the raw text with different code: a character-by-character scanner instead of a regular expression, headings found
   line by line, least squares written out by hand. 1,527 numbers agree with `results/`.
7. **Charts.**

## Results

- **The size of it:** 213,516 words in 138 sections, 18,281 distinct words, 8,617 of them used exactly once: 47.1% of the vocabulary but only 4.0% of the words.
  Words average 4.47 letters.
- **Tokenising choices matter.** Splitting hyphenated words gives 216,070 words but 17,014 distinct ones (1,267 fewer), and "whale" moves from 23rd place to 21st; keeping
  "'s" gives 18,629 distinct words.
- **Most-used words** without stop words: whale 1,095, like 581, Ahab 511, man 502, ship 469, old 443, ye 430, sea 384. Counting every word that contains "whal" (whale, whales, whaling,
  sperm-whale and so on) gives 1,819 words, 8.5 per 1,000, about one in 117.
- **Zipf's law holds:** frequency falls with rank on a log-log line of slope -1.08 (R squared 0.995 over the top 1,000 words). "The" is 6.8% of all words, the top 10 words 23.9%
  and the top 100 51.3%.
- **Heaps' law holds:** the vocabulary grows as length to the power 0.63 (R squared 0.996); it never stops growing.
- **Whale density by chapter:** Cetology (chapter 32) 32.1 whale words per 1,000, The Advocate (24) 30.5, and the three chapters about pictures of whales (55 to 57) 27.2, 25.5 and 23.6.
  The Extracts at the front, a collection of quotations about whales, are at 32.1.
- **Where the words fall:** Queequeg peaks in the second tenth (61.8 uses per 10,000 words) and never passes 11.2 in a later one; Ahab is barely named in the first tenth (2.8) and peaks in
  the last (76.8); "white" peaks in the fourth tenth (39.3); Ishmael is named rarely, and not at all in five of the ten tenths.
- **First against last third:** the first is Bildad, Peleg, Jonah, landlord, pipe, shipmates, harpooneer, bed; the last is Parsee, oars, carpenter, Pip, flukes, boat, helm.

## Not done, and caveats

- No stemming: "whale" and "whales" are counted separately in the top-words list, and the whale family is found by the letters "whal". Archaic words (ye, thou) are not in the stop list, so they appear.
- A tenth of the book is a tenth of its words, not a set of chapters.
- This is word counting, not reading: it says nothing about meaning, irony or why the book lingers on whales.
