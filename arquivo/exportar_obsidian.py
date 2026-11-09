"""
exportar_obsidian.py - gera um vault do Obsidian (um .md por salvo) em dados/vault/.
Abra a pasta "vault" no Obsidian (Open folder as vault). Grafo, backlinks e busca vêm de graça.

- Propriedades: fonte, pasta, autor, data, url, categoria, cores, tags
- Tags automáticas: #pasta/<nome>, #fonte/<x|instagram>, #cor/<azul>, #categoria/<nome> + as suas
- Mídia: hardlink (não ocupa espaço extra no mesmo disco; senão copia)
- Seguro para rodar de novo: sobrescreve só as notas geradas.

Generates an Obsidian vault. Open the "vault" folder in Obsidian.
"""
import json, os, re, shutil, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
RAIZ = os.path.join(RAIZ, "dados")
LIB = os.path.join(RAIZ, "arquivo", "library.json")
VAULT = os.path.join(RAIZ, "vault")


def slug(s):
    s = re.sub(r"[^\w\-]+", "-", str(s).strip().lower(), flags=re.UNICODE).strip("-")
    return s or "sem-nome"


def tag(s):
    return slug(s)


def yaml(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def midia(origem_rel, i):
    """Liga (hardlink) ou copia o arquivo para vault/media/<fonte>_<id>/ e devolve o caminho relativo."""
    src = os.path.join(RAIZ, origem_rel)
    pasta = os.path.join(VAULT, "media", f"{i['fonte']}_{i['id']}")
    os.makedirs(pasta, exist_ok=True)
    dest = os.path.join(pasta, os.path.basename(src))
    if not os.path.exists(dest):
        try:
            os.link(src, dest)
        except OSError:
            shutil.copy2(src, dest)
    return os.path.relpath(dest, VAULT).replace(os.sep, "/")


def main():
    with open(LIB, encoding="utf-8") as f:
        itens = json.load(f)
    for i in itens:
        autor = i.get("usuario") or i.get("nome") or "desconhecido"
        pasta_nota = os.path.join(VAULT, "Notas", "X" if i["fonte"] == "x" else "Instagram", slug(i["colecao"]))
        os.makedirs(pasta_nota, exist_ok=True)
        m = i["midia"]
        cores = (i.get("auto") or {}).get("cores", [])
        tags = [f"fonte/{i['fonte']}", f"pasta/{tag(i['colecao'])}"] + [f"cor/{c}" for c in cores] + [tag(t) for t in i["tags"]]
        if i.get("categoria"):
            tags.append(f"categoria/{tag(i['categoria'])}")
        linhas = ["---",
                  f"fonte: {i['fonte']}", f"pasta: {yaml(i['colecao'])}", f"autor: {yaml(autor)}",
                  f"data: {yaml((i.get('data') or '')[:10])}", f"url: {yaml(i.get('url') or '')}",
                  f"categoria: {yaml(i.get('categoria') or '')}", f"favorito: {str(bool(i.get('favorito'))).lower()}",
                  "cores: [" + ", ".join(cores) + "]",
                  "tags:", *[f"  - {t}" for t in tags], "---", ""]
        for v in m["videos"]:
            linhas.append(f"![[{midia(v, i)}]]")
        for p in m["fotos"] or ([m["poster"]] if m["poster"] and not m["videos"] else []):
            linhas.append(f"![[{midia(p, i)}]]")
        linhas += ["", i["texto"] or "_(sem texto)_", ""]
        if i.get("nota"):
            linhas += ["## Nota", i["nota"], ""]
        linhas.append(f"[Abrir original]({i['url']})" if i.get("url") else "")
        nome = f"{slug(autor)}-{i['id']}.md"
        with open(os.path.join(pasta_nota, nome), "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))
    print(f"{len(itens)} notas em {VAULT}")


if __name__ == "__main__":
    main()
