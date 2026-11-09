"""
indexar.py - analisa as imagens e grava cores dominantes em cada item (campo "auto").
Grátis e 100% local (Pillow + numpy). Incremental: só processa itens ainda sem cores.

    python arquivo/indexar.py            # só itens novos
    python arquivo/indexar.py --refazer  # recalcula tudo

Free and fully local. Run after importar.py.
"""
import json, os, sys

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("Faltam Pillow e numpy: pip install -r requirements.txt  (a busca por cor fica desligada sem isso)")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
RAIZ = os.path.join(RAIZ, "dados")
LIB = os.path.join(RAIZ, "arquivo", "library.json")
CORES = ["preto", "branco", "cinza", "vermelho", "laranja", "marrom", "amarelo", "verde", "ciano", "azul", "roxo", "rosa"]
NEUTRAS = {"preto", "branco", "cinza"}


def classificar(img):
    """Fração de pixels por cor nomeada (imagem reduzida, via HSV)."""
    img = img.convert("RGB")
    img.thumbnail((80, 80))
    hsv = np.asarray(img.convert("HSV")).reshape(-1, 3).astype(np.int32)
    h, s, v = hsv[:, 0] * 360 / 255, hsv[:, 1], hsv[:, 2]
    nome = np.empty(len(hsv), dtype=object)
    cromatico = (s >= 45) & (v >= 50)
    nome[:] = "cinza"
    nome[v < 50] = "preto"
    nome[(s < 45) & (v >= 200)] = "branco"
    faixas = [("vermelho", (h < 15) | (h >= 345)), ("laranja", (h >= 15) & (h < 40)), ("amarelo", (h >= 40) & (h < 70)),
              ("verde", (h >= 70) & (h < 165)), ("ciano", (h >= 165) & (h < 200)), ("azul", (h >= 200) & (h < 255)),
              ("roxo", (h >= 255) & (h < 290)), ("rosa", (h >= 290) & (h < 345))]
    for n, m in faixas:
        nome[cromatico & m] = n
    nome[cromatico & (h >= 15) & (h < 45) & (v < 140)] = "marrom"
    total = len(nome)
    return {c: float((nome == c).sum()) / total for c in CORES}


def cores_do_item(i):
    caminhos = (i["midia"]["fotos"][:4]) or ([i["midia"]["poster"]] if i["midia"]["poster"] else [])
    soma, n = {c: 0.0 for c in CORES}, 0
    for p in caminhos:
        try:
            with Image.open(os.path.join(RAIZ, p)) as im:
                for c, f in classificar(im).items():
                    soma[c] += f
                n += 1
        except Exception:
            continue
    if not n:
        return None
    frac = {c: f / n for c, f in soma.items()}
    escolhidas = [c for c in CORES if frac[c] >= (0.30 if c in NEUTRAS else 0.08)]
    escolhidas.sort(key=lambda c: -frac[c])
    return escolhidas, {c: round(f, 3) for c, f in frac.items() if f >= 0.03}


def main():
    with open(LIB, encoding="utf-8") as f:
        itens = json.load(f)
    refazer = "--refazer" in sys.argv
    feitos = 0
    for i in itens:
        auto = i.setdefault("auto", {})
        if "cores" in auto and not refazer:
            continue
        r = cores_do_item(i)
        auto["cores"], auto["cores_pct"] = (r if r else ([], {}))
        feitos += 1
    tmp = LIB + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(itens, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LIB)
    print(f"{feitos} itens analisados, {sum(1 for i in itens if i['auto'].get('cores'))} com cores")


if __name__ == "__main__":
    main()
