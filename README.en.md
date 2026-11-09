# Salvos Archive

[🇧🇷 Português](README.md) · 🇬🇧 English

Turns your **X (Twitter) bookmarks** and an **Instagram saved collection** into a personal, **local, offline** archive: search, filter, categorize and organize everything in a dashboard, with photos and videos downloaded to your computer.

- 🔒 Everything runs on your machine. No account, no server, nothing is uploaded.
- 🆓 Free tools only, no paid AI.
- 🔎 Obsidian-style search: `tag:genart -logo cor:azul fonte:ig "exact phrase"`. Searching **blue** (or *azul*) also finds images that are visually blue.
- 🏷️ Suggests **tags and categories** automatically (genart, animation, motion, 3d, ceramics…); accept with one click.
- 🖼️ 4 views: masonry, grid, list, timeline. Every item shows which folder/collection it came from.
- 📓 Bonus: export an Obsidian *vault*.

> The UI and some search operators are in Portuguese (`tag:`, `cat:`, `fonte:` = source, `pasta:` = folder, `autor:` = author, `cor:` = colour, `tipo:` = type). Colour words work in English too.

---

## 1. Install (once)

You need **Python 3.9+** ([python.org](https://www.python.org/downloads/); on Windows tick "Add to PATH") and **ffmpeg** (videos only).

```bash
git clone <THIS-REPO-URL>
cd salvos-archive
pip install -r requirements.txt
```

ffmpeg: Windows `winget install ffmpeg` · Mac `brew install ffmpeg` · Linux `sudo apt install ffmpeg`.

> On Mac/Linux use `python3` instead of `python`.

## 2. Get your X bookmarks

1. Open **https://x.com/i/bookmarks** while logged in (Chrome/Edge/Firefox).
2. Press **F12** → **Console** tab.
3. Open [`x/console_snippet.js`](x/console_snippet.js), copy **all of it**, paste into the console and press Enter. (If the browser asks, type `allow pasting` first.)
4. It scrolls the page by itself and finally downloads `x_bookmarks_full_<date>.json`. To stop early, type `stopExport()`.
5. Then download everything:

```bash
python salvos.py x
```

The file is found automatically in `dados/entrada/` or your Downloads folder. Photos, videos and full texts go to `dados/x/`. Running again only fetches what's new.

## 3. Get an Instagram collection (optional)

1. On Instagram (logged in, in the browser) open **Saved → the collection** you want.
2. F12 → Console, paste [`instagram/console_snippet.js`](instagram/console_snippet.js) and Enter. It scrolls with pauses (on purpose, to be gentle) and downloads `ig_links_<collection>_<date>.json`.
3. Run:

```bash
python salvos.py ig
```

Public posts download **without login**. For restricted ones: `python salvos.py ig --navegador chrome` (close Chrome first) or `--cookies cookies.txt`. Do one collection at a time; the collection name becomes the "folder" in the dashboard. Slower: `--pausa 5`.

## 4. Open the dashboard

```bash
python salvos.py
```

Merges everything, analyzes images, suggests tags and opens **http://127.0.0.1:8765**. Stop with `Ctrl+C`.

### How to use

| I want to… | Do this |
|---|---|
| Search | Type in the search box. Supports `tag:`, `cat:`, `fonte:` (x/ig), `pasta:`, `autor:`, `cor:`, `tipo:` (video/foto/texto), `fav:1`, `-exclude` and `"exact phrase"` |
| Filter | **Filtros** button (source, folder, category, tag, colour, author, date). Click an active sidebar item again to clear it |
| Change view | Mosaico (masonry) · Grade (grid) · Lista (list) · Tempo (timeline) |
| Categorize | Click an item → category, tags, note. **Dashed** tags/categories are suggestions: click to accept |
| Bulk edit | **Selecionar** → tick items → add tag / category / favorite |

Your tags, categories, notes and favorites are stored in `dados/arquivo/library.json` and are **never overwritten** when you import new items.

### Tag and category suggestions

Simple rules (words and hashtags in the text + folder name), no AI, no internet. Teach it your own topics by editing the `VOCABULARIO` dictionary at the top of [`arquivo/sugerir_tags.py`](arquivo/sugerir_tags.py). Accept all suggestions at once (irreversible):

```bash
python arquivo/sugerir_tags.py --aceitar
```

## 5. Bonus: Obsidian

```bash
python salvos.py obsidian
```

Creates `dados/vault/` with one note per saved item (properties, `#cor/azul` / `#pasta/...` tags, embedded media). In Obsidian: *Open folder as vault*.

---

## Commands

| Command | What it does |
|---|---|
| `python salvos.py x` | download X bookmarks |
| `python salvos.py ig` | download an Instagram collection |
| `python salvos.py` | merge, analyze, suggest and open the dashboard (`--porta 9000` changes the port) |
| `python salvos.py atualizar` | same, without opening the dashboard |
| `python salvos.py obsidian` | export the Obsidian vault |

## Layout

```
salvos-archive/
├─ salvos.py            single entry point
├─ x/                   X snippet + downloader
├─ instagram/           Instagram snippet + downloader
├─ arquivo/             dashboard, search, tags, Obsidian
└─ dados/               YOUR data (git-ignored): entrada/, x/, instagram/, arquivo/, vault/
```

## Privacy

Nothing leaves your computer. The dashboard server only listens on `127.0.0.1`. The snippets only read the page you have open. The only outside connections download media from the posts themselves (X, Instagram and their public embed/syndication endpoints). `dados/` is in `.gitignore`, so your saves are never committed.

## Known limitations

- Very long X posts ("Show more") may come truncated; the tool tries to complete them, but some only show in full when logged in.
- The X snippet doesn't capture X bookmark *folders*: everything lands in "Bookmarks".
- Instagram carousels are completed via the public embed page; private posts may fail.
- X and Instagram change their sites now and then; if a snippet stops working, open an issue.
- Colours use 12 named buckets from simple image analysis (not perfect).
- Respect each platform's terms and copyright: this is for **your own** personal archive.

## Credits

The X snippet is derived from the QuantumMonkey exporter (MIT). Video downloads by [yt-dlp](https://github.com/yt-dlp/yt-dlp). License: MIT.
