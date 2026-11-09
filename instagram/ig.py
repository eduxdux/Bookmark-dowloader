"""
ig.py - baixa os posts de uma coleção do Instagram (links do console_snippet.js)
e gera um mural HTML.  /  downloads Instagram collection posts and builds an HTML wall.

Requer / Requires:  pip install yt-dlp   (+ ffmpeg no PATH)

Uso / Usage:
    python instagram/ig.py                # usa o ig_links_*.json mais recente (dados/entrada ou Downloads)
    python instagram/ig.py ig_links_x.json --navegador chrome
    python instagram/ig.py --cookies cookies.txt   # alternativa ao navegador / alternative
    python instagram/ig.py --pausa 4      # segundos entre posts (padrão 3)
    python instagram/ig.py --so-mural

Posts públicos baixam sem login. Para privados/restritos, passe --navegador chrome (feche o
Chrome se der erro de cookies) ou --cookies cookies.txt. Rodar de novo só baixa o que falta.
Public posts need no login. For private/restricted ones use --navegador or --cookies.

Saída / Output: dados/instagram/data.json, media/<id>/, mural.html
"""
import glob, html, json, os, random, re, subprocess, sys, time, urllib.request
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(AQUI), "dados", "instagram")
ENTRADA = [os.path.join(os.path.dirname(AQUI), "dados", "entrada"), os.path.join(os.path.expanduser("~"), "Downloads")]
MEDIA = os.path.join(OUT, "media")
DATA = os.path.join(OUT, "data.json")
VID = {".mp4", ".webm", ".mov", ".mkv"}
IMG = {".jpg", ".jpeg", ".png", ".webp"}


def opcao(nome, padrao=None):
    a = sys.argv
    return a[a.index(nome) + 1] if nome in a and a.index(nome) + 1 < len(a) else padrao


def rel(p):
    return os.path.relpath(p, OUT).replace(os.sep, "/")


def carregar():
    if os.path.exists(DATA):
        with open(DATA, encoding="utf-8") as f:
            return {p["id"]: p for p in json.load(f)}
    return {}


def salvar(lib):
    os.makedirs(OUT, exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(list(lib.values()), f, indent=2, ensure_ascii=False)


def arquivos(pasta):
    vids = sorted(f for f in glob.glob(os.path.join(pasta, "*")) if os.path.splitext(f)[1].lower() in VID)
    imgs = sorted(f for f in glob.glob(os.path.join(pasta, "*")) if os.path.splitext(f)[1].lower() in IMG)
    return vids, imgs


def baixar_via_embed(p):
    """Plano B para posts só de foto (o yt-dlp não suporta): usa a página pública de embed.
    Fallback for photo-only posts: public embed page (first image only for carousels)."""
    req = urllib.request.Request(f"https://www.instagram.com/p/{p['id']}/embed/captioned/",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        pg = r.read().decode("utf-8", "replace")
    img = re.search(r'<img class="EmbeddedMediaImage"[^>]*?\ssrc="([^"]+)"', pg)
    if not img:
        return False
    pasta = os.path.join(MEDIA, p["id"])
    dest = os.path.join(pasta, "1.jpg")
    req = urllib.request.Request(html.unescape(img.group(1)), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        f.write(r.read())
    user = re.search(r'class="UsernameText">([^<]+)', pg)
    cap = re.search(r'class="Caption">.*?</a>(.*?)<div class="CaptionComments"', pg, re.S)
    texto = html.unescape(re.sub(r"<[^>]+>", "\n", cap.group(1))).strip() if cap else (p.get("alt") or "")
    p.update({"usuario": user.group(1) if user else None, "nome": user.group(1) if user else None,
              "texto": re.sub(r"\n{3,}", "\n\n", texto), "data": None, "texto_cortado": False,
              "local": {"fotos": [rel(dest)]}})
    return True


def baixar_post(p, auth):
    pasta = os.path.join(MEDIA, p["id"])
    os.makedirs(pasta, exist_ok=True)
    base = [sys.executable, "-m", "yt_dlp", "--no-warnings", "-q", "--write-info-json", "--write-thumbnail",
            "-o", os.path.join(pasta, "%(playlist_index|1)s.%(ext)s")]
    # 1) sem login (posts públicos funcionam assim); 2) com cookies só se falhar
    r = subprocess.run(base + [p["url"]], capture_output=True, text=True)
    if not glob.glob(os.path.join(pasta, "*.info.json")) and auth:
        r = subprocess.run(base + auth + [p["url"]], capture_output=True, text=True)
    infos = sorted(glob.glob(os.path.join(pasta, "*.info.json")))
    vids, imgs = arquivos(pasta)
    if not infos and not vids and not imgs:
        try:
            if baixar_via_embed(p):
                return True, None
        except Exception:
            pass
        return False, (r.stderr or "").strip().splitlines()[-1:] or ["erro desconhecido"]
    meta = {}
    if infos:
        with open(infos[0], encoding="utf-8") as f:
            meta = json.load(f)
    ts = meta.get("timestamp")
    p.update({
        "usuario": meta.get("uploader_id") or meta.get("channel") or meta.get("uploader"),
        "nome": meta.get("uploader") or meta.get("channel"),
        "texto": (meta.get("description") or meta.get("title") or "").strip(),
        "data": datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None,
        "texto_cortado": False,
        "local": {},
    })
    if vids:
        p["local"]["videos"] = [rel(v) for v in vids]
        if imgs:
            p["local"]["poster"] = rel(imgs[0])
    else:
        p["local"]["fotos"] = [rel(i) for i in imgs]
    return True, None


def mural(lib):
    with open(os.path.join(AQUI, "mural_template.html"), encoding="utf-8") as f:
        html = f.read()
    dados = json.dumps(list(lib.values()), ensure_ascii=False).replace("</", "<\\/")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "mural.html"), "w", encoding="utf-8") as f:
        f.write(html.replace("/*__DATA__*/[]", dados))
    print(f"[mural] {os.path.join(OUT, 'mural.html')}")


def main():
    lib = carregar()
    if "--so-mural" not in sys.argv:
        valores = {opcao(o) for o in ("--navegador", "--cookies", "--pausa") if opcao(o)}
        args = [a for a in sys.argv[1:] if not a.startswith("--") and a not in valores]
        caminho = args[0] if args else None
        if not caminho:
            arqs = [a for p in ENTRADA for a in glob.glob(os.path.join(p, "ig_links_*.json"))]
            caminho = max(arqs, key=os.path.getmtime) if arqs else None
        if not caminho:
            sys.exit("Nenhum ig_links_*.json em dados/entrada nem em Downloads. Rode instagram/console_snippet.js primeiro. / Run the snippet first.")
        with open(caminho, encoding="utf-8") as f:
            links = json.load(f)
        auth = ["--cookies", opcao("--cookies")] if opcao("--cookies") else (["--cookies-from-browser", opcao("--navegador")] if opcao("--navegador") else [])
        pausa = float(opcao("--pausa", 3))
        novos = [p for p in links if p["id"] not in lib or "local" not in lib[p["id"]]]
        print(f"[ig] {len(links)} links, {len(novos)} a baixar (pausa {pausa}s)")
        for n, p in enumerate(novos, 1):
            p["fonte"] = "instagram"
            ok, erro = baixar_post(p, auth)
            if ok:
                lib[p["id"]] = p
                print(f"   [{n}/{len(novos)}] ok {p['id']}")
                salvar(lib)
            else:
                print(f"   [{n}/{len(novos)}] x  {p['id']}: {erro[0]}")
            time.sleep(pausa + random.uniform(0, 1.5))
        import avatares  # foto de perfil + @ correto de cada autor
        avatares.main()
        import carrosseis  # fotos dos slides que o yt-dlp pula
        carrosseis.main()
        lib = carregar()
    mural(lib)


if __name__ == "__main__":
    main()
