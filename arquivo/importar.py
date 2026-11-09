"""
importar.py - junta X + Instagram numa biblioteca única (dados/arquivo/library.json).
Rodar de novo é seguro: atualiza os dados e PRESERVA tags, categoria, favorito e nota.
Itens que sumiram da origem continuam no arquivo.

Merges X + Instagram into one library. Safe to re-run: keeps your tags/category/favorite/notes.
"""
import json, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
RAIZ = os.path.join(RAIZ, "dados")  # tudo do usuário fica em dados/ (fora do git)
SAIDA = os.path.join(RAIZ, "arquivo", "library.json")
FONTES = {  # fonte -> pasta onde está o data.json e de onde partem os caminhos de mídia
    "x": os.path.join(RAIZ, "x"),
    "instagram": os.path.join(RAIZ, "instagram"),
}
CAMPOS_USUARIO = ("tags", "categoria", "favorito", "nota")


def caminho_raiz(base, p):
    """Caminho de mídia relativo à pasta de origem -> relativo à raiz do projeto (com /)."""
    return os.path.relpath(os.path.normpath(os.path.join(base, p)), RAIZ).replace(os.sep, "/")


def main():
    existente = {}
    if os.path.exists(SAIDA):
        with open(SAIDA, encoding="utf-8") as f:
            existente = {i["uid"]: i for i in json.load(f)}
    novos = 0
    for fonte, base in FONTES.items():
        arq = os.path.join(base, "data.json")
        if not os.path.exists(arq):
            print(f"[{fonte}] sem data.json em {base} (pulando)")
            continue
        with open(arq, encoding="utf-8") as f:
            itens = json.load(f)
        for t in itens:
            uid = f"{fonte}:{t['id']}"
            loc = t.get("local") or {}
            midia = {
                "fotos": [caminho_raiz(base, p) for p in loc.get("fotos", [])],
                "videos": [caminho_raiz(base, p) for p in loc.get("videos", [])],
                "poster": caminho_raiz(base, loc["poster"]) if loc.get("poster") else None,
                "avatar": caminho_raiz(base, loc["avatar"]) if loc.get("avatar") else None,
            }
            if loc.get("slides"):  # carrossel com a ordem real (vídeos e fotos misturados)
                midia["slides"] = [{"t": s["t"], "src": caminho_raiz(base, s["src"])} for s in loc["slides"]]
            item = {
                "uid": uid, "fonte": fonte, "id": t["id"], "url": t.get("url"),
                "colecao": t.get("colecao") or ("Bookmarks" if fonte == "x" else "Sem coleção"),
                "usuario": t.get("usuario"), "nome": t.get("nome"),
                "texto": t.get("texto") or "", "texto_cortado": bool(t.get("texto_cortado")),
                "data": t.get("data"), "midia": midia,
            }
            antigo = existente.get(uid)
            if antigo is None:
                novos += 1
                item.update(tags=[], categoria="", favorito=False, nota="")
            else:
                for k in CAMPOS_USUARIO:
                    item[k] = antigo.get(k, [] if k == "tags" else False if k == "favorito" else "")
                if "auto" in antigo:  # dados calculados (cores etc.) também são preservados
                    item["auto"] = antigo["auto"]
            existente[uid] = item
        print(f"[{fonte}] {len(itens)} itens")
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(list(existente.values()), f, indent=2, ensure_ascii=False)
    print(f"Total: {len(existente)} ({novos} novos) -> {SAIDA}")


if __name__ == "__main__":
    main()
