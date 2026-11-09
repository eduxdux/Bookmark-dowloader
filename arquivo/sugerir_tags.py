"""
sugerir_tags.py - sugere tags automaticamente (grátis, local, sem IA) e grava em item["auto"]["tags"].

Como funciona:
  1. VOCABULARIO abaixo: tag -> palavras/hashtags que a disparam (edite à vontade!).
  2. Hashtags que aparecem em 2+ salvos viram tags sozinhas (ex.: #fxhash -> fxhash).
  3. Pasta/coleção também pode sugerir tag (ex.: ceramic -> cerâmica).
Suas tags (campo "tags") nunca são alteradas. No dashboard as sugestões aparecem tracejadas;
clique para aceitar.

    python arquivo/sugerir_tags.py             # recalcula as sugestões
    python arquivo/sugerir_tags.py --aceitar   # promove TODAS as sugestões a tags reais (sem volta)

Free, local, rule-based tag suggestions. Edit VOCABULARIO to teach it your own topics.
"""
import json, os, re, sys, unicodedata
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(os.path.dirname(AQUI), "dados")
LIB = os.path.join(RAIZ, "arquivo", "library.json")

# tag canônica -> lista de termos (palavra inteira, sem acento/maiúscula; "#" opcional). Prefixo "~" = trecho.
VOCABULARIO = {
    "genart": ["generative art", "generativeart", "genart", "generative", "creative coding", "creativecoding", "fxhash",
               "fxhashxyz", "algorithmic art", "algoart", "processing", "p5js", "p5", "openframeworks", "touchdesigner",
               "shader", "glsl", "flow field", "particles", "particulas", "arte generativa", "codeart", "code art"],
    "animation": ["animation", "animated", "animacao", "animar", "animate", "2danimation", "3danimation", "framebyframe",
                  "frame by frame", "loop", "looping", "gif"],
    "motion": ["motion", "motiondesign", "motion design", "motiongraphics", "motion graphics", "motiondesigner", "mograph",
              "aftereffects", "after effects", "cavalry", "rive", "riveapp", "lottie", "kinetic", "kinetic type"],
    "3d": ["3d", "blender", "b3d", "c4d", "cinema4d", "cinema 4d", "redshift", "octane", "houdini", "zbrush", "maya",
           "render", "3dart", "modeling", "sculpt", "unreal", "unity"],
    "ilustracao": ["illustration", "ilustracao", "illustrator", "drawing", "desenho", "sketch", "procreate", "characterdesign",
                   "character design", "concept art", "conceptart", "painting", "pintura"],
    "design": ["graphic design", "graphicdesign", "design", "branding", "identity", "logo", "logotype", "packaging", "poster",
               "cartaz", "layout", "editorial"],
    "tipografia": ["typography", "tipografia", "typeface", "type design", "lettering", "font", "fonte tipografica", "kerning",
                   "typographic", "kinetic type"],
    "ui-ux": ["ui", "ux", "interface", "app design", "figma", "prototype", "prototipo", "interaction", "interactive",
              "interativo", "microinteraction", "web design", "webdesign", "website", "framer", "webflow"],
    "webgl": ["webgl", "three.js", "threejs", "three js", "r3f", "react three", "canvas"],
    "codigo": ["code", "codigo", "javascript", "typescript", "python", "scripting", "script", "github", "open source",
               "opensource", "tutorial", "plugin", "shader"],
    "som": ["sound", "sounddesign", "sound design", "music", "musica", "audio", "synth", "foley", "soundtrack"],
    "video": ["video", "videoart", "film", "filme", "cinema", "edit", "editz", "editing", "montage", "vfx", "reel"],
    "ceramica": ["ceramic", "ceramics", "ceramica", "pottery", "ceramista", "wheel", "kiln", "glaze", "esmalte", "stoneware",
                 "porcelain", "porcelana", "clay", "argila", "torno"],
    "arte": ["art", "artist", "arte", "artista", "artwork", "gallery", "galeria", "museum", "museu", "exhibition", "exposicao",
             "scultpure", "sculpture", "escultura"],
    "fotografia": ["photo", "photography", "fotografia", "foto", "photographer", "camera", "analog", "film photography"],
    "game": ["game", "gamedev", "indiegame", "jogo", "videogame", "godot", "pixel art", "pixelart", "sprite"],
    "ia": ["ai", "ia", "midjourney", "stable diffusion", "comfyui", "chatgpt", "llm", "machine learning", "neural",
           "runway", "sora", "veo", "generative ai"],
    "referencia": ["reference", "referencia", "inspiration", "inspiracao", "moodboard", "inspired"],
    "paleta": ["palette", "paleta", "color palette", "colour", "gradient", "gradiente"],
    "arquitetura": ["architecture", "arquitetura", "interior", "building", "urban"],
    "moda": ["fashion", "moda", "textile", "textil", "outfit"],
    "maternidade": ["parenting", "toddler", "baby", "kids", "criancas", "bebe", "screentime", "peacefulparenting", "mae", "mom"],
}
# nome de pasta/coleção -> tag sugerida
PASTAS = {}  # exemplo: {"ceramic": "ceramica"}  (trecho do nome da pasta -> tag)

# categoria sugerida = primeira tag desta lista (ordem = prioridade, do mais específico ao mais geral)
CATEGORIAS = [("ceramica", "Cerâmica"), ("maternidade", "Maternidade"), ("genart", "Arte generativa"), ("3d", "3D"),
              ("tipografia", "Tipografia"), ("ilustracao", "Ilustração"), ("game", "Game"), ("fotografia", "Fotografia"),
              ("ui-ux", "UI/UX"), ("webgl", "Web / WebGL"), ("motion", "Motion"), ("animation", "Animação"),
              ("ia", "IA"), ("som", "Som"), ("video", "Vídeo"), ("codigo", "Código"), ("design", "Design"), ("arte", "Arte")]

IGNORAR_HASHTAGS ={"nft", "nftcommunity", "nftartists", "follow", "art", "artist", "fyp", "viral", "like", "reels",
                    "explore", "trending", "foryou", "new", "work", "free"}


def norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def compilar():
    out = {}
    for tag, termos in VOCABULARIO.items():
        partes = []
        for t in termos:
            t = norm(t)
            if t.startswith("~"):
                partes.append(re.escape(t[1:]))
            else:
                partes.append(r"(?<![\w])#?" + re.escape(t).replace(r"\ ", r"[\s_-]?") + r"(?![\w])")
        out[tag] = re.compile("|".join(partes))
    return out


def main():
    with open(LIB, encoding="utf-8") as f:
        itens = json.load(f)
    if "--aceitar" in sys.argv:
        n = 0
        for i in itens:
            novas = [t for t in (i.get("auto") or {}).get("tags", []) if t not in i["tags"]]
            i["tags"] = sorted(set(i["tags"]) | set(novas))
            n += len(novas)
            if not i.get("categoria") and (i.get("auto") or {}).get("categoria"):
                i["categoria"] = i["auto"]["categoria"]
        gravar(itens)
        return print(f"{n} sugestões aceitas como tags reais (e categorias sugeridas aplicadas).")

    rx = compilar()
    hashtags = Counter()
    textos = []
    for i in itens:
        t = norm(" ".join([i.get("texto") or "", i.get("nota") or ""]))
        textos.append(t)
        hashtags.update(set(re.findall(r"#(\w{3,})", t)))
    comuns = {h for h, n in hashtags.items() if n >= 2 and h not in IGNORAR_HASHTAGS}
    conhecidas = {norm(x).replace(" ", "") for ts in VOCABULARIO.values() for x in ts}

    total = 0
    for i, t in zip(itens, textos):
        sug = set()
        for tag, r in rx.items():
            if r.search(t):
                sug.add(tag)
        for h in re.findall(r"#(\w{3,})", t):
            if h in comuns and h not in conhecidas:
                sug.add(h)
        for chave, tag in PASTAS.items():
            if chave in norm(i.get("colecao") or ""):
                sug.add(tag)
        sug -= set(i["tags"])
        todas = sug | set(i["tags"])
        i.setdefault("auto", {})["tags"] = sorted(sug)
        i["auto"]["categoria"] = next((nome for tag, nome in CATEGORIAS if tag in todas), "")
        total += len(sug)
    gravar(itens)
    c = Counter(t for i in itens for t in i["auto"]["tags"])
    print(f"{total} sugestões em {len(itens)} itens ({sum(1 for i in itens if i['auto']['tags'])} com alguma).")
    print("Categorias:", dict(Counter(i["auto"]["categoria"] or "(nenhuma)" for i in itens)))
    print("Top:", ", ".join(f"{t}({n})" for t, n in c.most_common(25)))


def gravar(itens):
    tmp = LIB + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(itens, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LIB)


if __name__ == "__main__":
    main()
