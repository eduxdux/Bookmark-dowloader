"""
carrosseis.py - completa os carrosséis do Instagram: baixa as FOTOS que o yt-dlp pula e grava a
ordem certa dos slides (vídeo/foto misturados) em local.slides. Sem login, via página pública de embed.
O ig.py chama isto no fim; também pode rodar sozinho:

    python instagram/carrosseis.py            # só posts ainda não verificados
    python instagram/carrosseis.py --refazer

Completes Instagram carousels: downloads the photo slides yt-dlp skips and stores slide order.
"""
import html, json, os, re, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(AQUI), "dados", "instagram")
DATA = os.path.join(OUT, "data.json")
MEDIA = os.path.join(OUT, "media")
UA = {"User-Agent": "Mozilla/5.0"}


def pegar(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def filhos(post_id):
    """Lista [(is_video, url_imagem)] dos slides, ou None se não for carrossel."""
    pg = pegar(f"https://www.instagram.com/p/{post_id}/embed/captioned/").decode("utf-8", "replace")
    m = re.search(r'"contextJSON":"((?:[^"\\]|\\.)*)"', pg)
    if not m:
        return None
    ctx = json.loads(json.loads('"' + m.group(1) + '"'))
    sm = (ctx.get("gql_data") or {}).get("shortcode_media") or {}
    edges = (sm.get("edge_sidecar_to_children") or {}).get("edges")
    if not edges:
        return None
    return [(bool(e["node"].get("is_video")), e["node"].get("display_url")) for e in edges]


def num(p):
    m = re.search(r"(\d+)", os.path.basename(p))
    return int(m.group(1)) if m else 0


def main(pausa=1.5):
    if not os.path.exists(DATA):
        return
    with open(DATA, encoding="utf-8") as f:
        lib = json.load(f)
    refazer = "--refazer" in sys.argv
    alvo = [p for p in lib if refazer or "slides" not in (p.get("local") or {})]
    print(f"[carrosseis] {len(alvo)} post(s) a verificar")
    mudou = 0
    for n, p in enumerate(alvo, 1):
        loc = p.setdefault("local", {})
        try:
            ch = filhos(p["id"])
        except Exception as e:
            print(f"   [{n}/{len(alvo)}] x {p['id']}: {e}")
            time.sleep(pausa)
            continue
        if not ch:  # não é carrossel: só marca como verificado
            loc["slides"] = None
            time.sleep(pausa)
            continue
        videos = sorted(loc.get("videos", []), key=num)
        pasta = os.path.join(MEDIA, p["id"])
        os.makedirs(pasta, exist_ok=True)
        slides, vi, fotos = [], 0, []
        for j, (eh_video, url) in enumerate(ch, 1):
            if eh_video:
                if vi < len(videos):
                    slides.append({"t": "v", "src": videos[vi]})
                    vi += 1
                continue
            dest = os.path.join(pasta, f"foto{j}.jpg")
            try:
                if not os.path.exists(dest):
                    with open(dest, "wb") as f:
                        f.write(pegar(html.unescape(url)))
                rel = os.path.relpath(dest, OUT).replace(os.sep, "/")
                slides.append({"t": "i", "src": rel})
                fotos.append(rel)
            except Exception:
                continue
        if slides:
            loc["slides"] = slides
            loc["fotos"] = fotos
            mudou += 1
            print(f"   [{n}/{len(alvo)}] ok {p['id']}: {len(slides)} slides ({len(fotos)} fotos)")
        time.sleep(pausa)
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA)
    print(f"[carrosseis] {mudou} carrossel(is) atualizados")


if __name__ == "__main__":
    main()
