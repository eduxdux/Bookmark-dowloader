"""
bookmarks.py - pipeline único: JSON do snippet -> textos completos, imagens,
vídeos (yt-dlp) e mural HTML.  /  one-shot pipeline: snippet JSON -> full texts,
images, videos (yt-dlp) and an HTML wall.

Uso / Usage (normalmente via "python salvos.py x"):
    python x/x.py                  # usa o x_bookmarks_full_*.json mais recente (dados/entrada ou Downloads)
    python x/x.py arquivo.json
    python x/x.py --sem-videos     # pula yt-dlp / skip yt-dlp
    python x/x.py --so-mural       # só regera o mural / only rebuild the wall

Saída / Output (dados/x/):
    data.json    biblioteca acumulada (rodar de novo só adiciona o novo)
    media/<id>/  imagens, poster e vídeos de cada tweet
    mural.html   abra com duplo clique / open by double-clicking
"""
import glob, json, os, re, shutil, subprocess, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(os.path.dirname(AQUI), "dados")
BIB = os.path.join(DADOS, "x")
MEDIA = os.path.join(BIB, "media")
DATA = os.path.join(BIB, "data.json")
VIDEOS_ANTIGOS = os.path.join(DADOS, "videos_antigos")  # opcional: mp4 já baixados, nomeados pelo ID da mídia
UA = {"User-Agent": "Mozilla/5.0"}


# ---------- utilidades ----------
def http_get(url, tentativas=3):
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read()
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(1.5 * (i + 1))


def baixar(url, destino):
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return True
    try:
        dados = http_get(url)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as f:
            f.write(dados)
        return True
    except Exception as e:
        print(f"   [!] {url[:80]}: {e}")
        return False


def rel(p):  # caminho relativo à pasta biblioteca, com /
    return os.path.relpath(p, BIB).replace(os.sep, "/")


def extensao(url, padrao="jpg"):
    m = re.search(r"format=(\w+)", url) or re.search(r"\.(jpg|jpeg|png|webp|gif)(?:\?|$)", url)
    return m.group(1) if m else padrao


def achar_json():
    pastas = [os.path.join(DADOS, "entrada"), os.path.join(os.path.expanduser("~"), "Downloads")]
    arqs = [a for p in pastas for a in glob.glob(os.path.join(p, "x_bookmarks_full_*.json")) if not a.endswith("_completo.json")]
    return max(arqs, key=os.path.getmtime) if arqs else None


def carregar_biblioteca():
    if os.path.exists(DATA):
        with open(DATA, encoding="utf-8") as f:
            return {t["id"]: t for t in json.load(f)}
    return {}


def salvar_biblioteca(lib):
    os.makedirs(BIB, exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(list(lib.values()), f, indent=2, ensure_ascii=False)


# ---------- etapas ----------
def mesclar(lib, novos):
    """Adiciona tweets novos; em repetidos, mantém o texto mais completo."""
    add = 0
    for t in novos:
        antigo = lib.get(t["id"])
        if not antigo:
            lib[t["id"]] = t
            add += 1
        else:
            if len(t.get("texto", "")) > len(antigo.get("texto", "")):
                antigo["texto"], antigo["texto_cortado"] = t["texto"], t.get("texto_cortado", False)
            for k in ("metricas", "metricas_texto", "images", "avatar", "nome"):
                if t.get(k) and not antigo.get(k):
                    antigo[k] = t[k]
    return add


def completar_textos(lib):
    n = 0
    for t in lib.values():
        if not t.get("texto_cortado"):
            continue
        try:
            d = json.loads(http_get(f"https://cdn.syndication.twimg.com/tweet-result?id={t['id']}&token=a"))
            novo = d.get("text", "")
            fim = d.get("display_text_range", [0, 0])[1]
            novo = re.sub(r"\s*https://t\.co/\w+\s*$", "", novo[:fim] if fim else novo).strip()
            if len(novo) > len(t["texto"]):
                t["texto"], t["texto_cortado"] = novo, False
                n += 1
        except Exception:
            pass
        time.sleep(0.4)
    pend = sum(1 for t in lib.values() if t.get("texto_cortado"))
    print(f"[textos] {n} completados, {pend} ainda cortados (só aparecem inteiros logado)")


def separar_midias(t):
    fotos, thumbs = [], []
    for u in t.get("images", []):
        (thumbs if "video_thumb" in u else fotos).append(u)
    return fotos, thumbs


def baixar_imagens(lib):
    n = 0
    for t in lib.values():
        pasta = os.path.join(MEDIA, t["id"])
        fotos, thumbs = separar_midias(t)
        local = t.setdefault("local", {})
        local["fotos"] = []
        for i, u in enumerate(fotos, 1):
            dest = os.path.join(pasta, f"foto_{i}.{extensao(u)}")
            if baixar(u, dest):
                local["fotos"].append(rel(dest))
                n += 1
        if thumbs:
            dest = os.path.join(pasta, f"poster.{extensao(thumbs[0])}")
            if baixar(thumbs[0], dest):
                local["poster"] = rel(dest)
        if t.get("avatar"):
            dest = os.path.join(MEDIA, "_avatares", f"{t.get('usuario') or t['id']}.jpg")
            if baixar(t["avatar"], dest):
                local["avatar"] = rel(dest)
    print(f"[imagens] {n} fotos verificadas/baixadas")


def baixar_videos(lib):
    if shutil.which("ffmpeg") is None:
        print("[aviso] ffmpeg não encontrado; alguns vídeos podem falhar / ffmpeg not found")
    antigos = {f[:-4] for f in os.listdir(VIDEOS_ANTIGOS) if f.endswith(".mp4")} if os.path.isdir(VIDEOS_ANTIGOS) else set()
    novos = falhas = reuso = 0
    for t in lib.values():
        if not t.get("has_video"):
            continue
        local = t.setdefault("local", {})
        pasta = os.path.join(MEDIA, t["id"])
        # 1) já baixado antes (nome = ID da mídia presente na URL da thumbnail)
        _, thumbs = separar_midias(t)
        ids = [m.group(1) for u in thumbs if (m := re.search(r"video_thumb/(\d+)/", u))]
        achados = [os.path.join(VIDEOS_ANTIGOS, f"{i}.mp4") for i in ids if i in antigos]
        # 2) já baixado por esta ferramenta
        achados += sorted(glob.glob(os.path.join(pasta, "video_*.*")))
        if achados:
            local["videos"] = [rel(p) for p in achados]
            reuso += 1
            continue
        # 3) baixar com yt-dlp
        os.makedirs(pasta, exist_ok=True)
        r = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "-q", "--no-warnings", "-o",
             os.path.join(pasta, "video_%(playlist_index|1)s.%(ext)s"), t["url"]],
            capture_output=True, text=True)
        arqs = sorted(glob.glob(os.path.join(pasta, "video_*.*")))
        if arqs:
            local["videos"] = [rel(p) for p in arqs]
            novos += 1
            print(f"   [ok] vídeo {t['id']}")
        else:
            falhas += 1
            print(f"   [x] sem vídeo baixável {t['id']} ({(r.stderr or '').strip().splitlines()[-1:] or ''})")
    print(f"[vídeos] {reuso} já existiam, {novos} novos, {falhas} sem vídeo baixável")


def gerar_mural(lib):
    tpl = os.path.join(AQUI, "mural_template.html")
    with open(tpl, encoding="utf-8") as f:
        html = f.read()
    dados = json.dumps(list(lib.values()), ensure_ascii=False).replace("</", "<\\/")
    os.makedirs(BIB, exist_ok=True)
    with open(os.path.join(BIB, "mural.html"), "w", encoding="utf-8") as f:
        f.write(html.replace("/*__DATA__*/[]", dados))
    print(f"[mural] {os.path.join(BIB, 'mural.html')}")


# ---------- main ----------
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    lib = carregar_biblioteca()
    if "--so-mural" not in flags:
        caminho = args[0] if args else achar_json()
        if not caminho:
            sys.exit("Nenhum x_bookmarks_full_*.json em dados/entrada nem em Downloads. Rode x/console_snippet.js no x.com primeiro. / Run the console snippet first.")
        with open(caminho, encoding="utf-8") as f:
            novos = json.load(f)
        print(f"[json] {caminho}: {len(novos)} tweets, {mesclar(lib, novos)} novos")
        completar_textos(lib)
        baixar_imagens(lib)
        if "--sem-videos" not in flags:
            baixar_videos(lib)
        salvar_biblioteca(lib)
    gerar_mural(lib)


if __name__ == "__main__":
    main()
