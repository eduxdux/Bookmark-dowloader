"""
avatares.py - baixa a foto de perfil de quem postou (via página pública de embed, sem login)
e corrige o @ (o yt-dlp às vezes grava só um número). Incremental; o ig.py já chama isto no fim.

    python instagram/avatares.py            # só autores que ainda não têm foto
    python instagram/avatares.py --refazer

Downloads profile pictures of post authors (public embed page, no login) and fixes @handles.
"""
import html, json, os, re, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(AQUI), "dados", "instagram")
DATA = os.path.join(OUT, "data.json")
PASTA = os.path.join(OUT, "media", "_avatares")


def pagina(post_id):
    req = urllib.request.Request(f"https://www.instagram.com/p/{post_id}/embed/captioned/", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def main(pausa=1.5):
    if not os.path.exists(DATA):
        return
    with open(DATA, encoding="utf-8") as f:
        lib = json.load(f)
    refazer = "--refazer" in sys.argv
    grupos = {}
    for p in lib:
        grupos.setdefault(p.get("nome") or p.get("usuario") or p["id"], []).append(p)
    novos = {k: g for k, g in grupos.items()
             if refazer or not all((x.get("local") or {}).get("avatar") for x in g) or any(str(x.get("usuario") or "").isdigit() for x in g)}
    print(f"[avatares] {len(novos)} autor(es) a buscar")
    os.makedirs(PASTA, exist_ok=True)
    for n, (chave, g) in enumerate(novos.items(), 1):
        ok = False
        for p in g[:2]:  # tenta até 2 posts do mesmo autor
            try:
                pg = pagina(p["id"])
                user = re.search(r'class="UsernameText">([^<]+)', pg)
                img = re.search(r'<img src="([^"]*t51\.2885-19[^"]*)"', pg) or re.search(r'class="Avatar[^>]*>\s*<img[^>]*src="([^"]+)"', pg)
                if not user:
                    continue
                handle = html.unescape(user.group(1)).strip()
                rel = None
                if img:
                    dest = os.path.join(PASTA, re.sub(r"\W", "_", handle) + ".jpg")
                    req = urllib.request.Request(html.unescape(img.group(1)), headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
                        f.write(r.read())
                    rel = os.path.relpath(dest, OUT).replace(os.sep, "/")
                for x in g:
                    x["usuario"] = handle
                    x["nome"] = x.get("nome") or handle
                    x.setdefault("local", {})
                    if rel:
                        x["local"]["avatar"] = rel
                ok = True
                break
            except Exception:
                continue
            finally:
                time.sleep(pausa)
        print(f"   [{n}/{len(novos)}] {'ok' if ok else 'x '} {chave}")
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA)


if __name__ == "__main__":
    main()
