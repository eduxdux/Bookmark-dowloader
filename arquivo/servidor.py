"""
servidor.py - dashboard local do seu arquivo de salvos.  /  local dashboard for your saved posts.

    python arquivo/servidor.py            # importa (se preciso) e abre http://127.0.0.1:8765
    python arquivo/servidor.py --porta 9000

Só escuta em 127.0.0.1 (só o seu computador). Edições (tags, categoria...) são gravadas
em dados/library.json. / Listens on localhost only; edits are saved to dados/library.json.
"""
import json, mimetypes, os, sys, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
RAIZ = os.path.join(RAIZ, "dados")
LIB = os.path.join(RAIZ, "arquivo", "library.json")
EXT_OK = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mov", ".mkv"}
trava = threading.Lock()


def ler():
    with open(LIB, encoding="utf-8") as f:
        return json.load(f)


def gravar(itens):
    tmp = LIB + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(itens, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LIB)


def limpar(campo, v):
    if campo == "tags":
        return sorted({str(t).strip().lower() for t in v if str(t).strip()})
    if campo == "favorito":
        return bool(v)
    return str(v).strip()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def enviar(self, codigo, corpo, tipo="application/json; charset=utf-8"):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        p = unquote(urlparse(self.path).path)
        if p in ("/", "/index.html"):
            with open(os.path.join(AQUI, "dashboard.html"), "rb") as f:
                return self.enviar(200, f.read(), "text/html; charset=utf-8")
        if p == "/api/itens":
            with trava:
                return self.enviar(200, json.dumps(ler(), ensure_ascii=False).encode("utf-8"))
        if p.startswith("/midia/"):
            raiz = os.path.realpath(RAIZ)
            alvo = os.path.realpath(os.path.join(raiz, p[len("/midia/"):]))
            if not alvo.startswith(raiz + os.sep) or os.path.splitext(alvo)[1].lower() not in EXT_OK \
                    or not os.path.isfile(alvo):
                return self.enviar(404, b"{}")
            return self.arquivo(alvo)
        self.enviar(404, b"{}")

    def arquivo(self, alvo):
        tam = os.path.getsize(alvo)
        tipo = mimetypes.guess_type(alvo)[0] or "application/octet-stream"
        ini, fim, codigo = 0, tam - 1, 200
        r = self.headers.get("Range")
        if r and r.startswith("bytes="):  # vídeo precisa de Range para buscar/pular
            a, _, b = r[6:].partition("-")
            ini = int(a) if a else 0
            fim = int(b) if b else tam - 1
            codigo = 206
        fim = min(fim, tam - 1)
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(fim - ini + 1))
        if codigo == 206:
            self.send_header("Content-Range", f"bytes {ini}-{fim}/{tam}")
        self.end_headers()
        try:
            with open(alvo, "rb") as f:
                f.seek(ini)
                resta = fim - ini + 1
                while resta > 0:
                    b = f.read(min(65536, resta))
                    if not b:
                        break
                    self.wfile.write(b)
                    resta -= len(b)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        p = unquote(urlparse(self.path).path)
        try:
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            return self.enviar(400, b"{}")
        with trava:
            itens = ler()
            por_uid = {i["uid"]: i for i in itens}
            if p == "/api/item":  # {uid, tags?, categoria?, favorito?, nota?}
                i = por_uid.get(corpo.get("uid"))
                if not i:
                    return self.enviar(404, b"{}")
                for k in ("tags", "categoria", "favorito", "nota"):
                    if k in corpo:
                        i[k] = limpar(k, corpo[k])
                gravar(itens)
                return self.enviar(200, json.dumps(i, ensure_ascii=False).encode("utf-8"))
            if p == "/api/lote":  # {uids, add_tags?, remover_tags?, categoria?, favorito?}
                for u in corpo.get("uids", []):
                    i = por_uid.get(u)
                    if not i:
                        continue
                    tags = set(i.get("tags", [])) | set(limpar("tags", corpo.get("add_tags", [])))
                    tags -= set(limpar("tags", corpo.get("remover_tags", [])))
                    i["tags"] = sorted(tags)
                    if "categoria" in corpo:
                        i["categoria"] = limpar("categoria", corpo["categoria"])
                    if "favorito" in corpo:
                        i["favorito"] = limpar("favorito", corpo["favorito"])
                gravar(itens)
                return self.enviar(200, b"{}")
        self.enviar(404, b"{}")


def main():
    if not os.path.exists(LIB):
        sys.path.insert(0, AQUI)
        import importar
        importar.main()
    if not os.path.exists(LIB):
        sys.exit("Nada para mostrar ainda. Rode antes: python salvos.py x  e/ou  python salvos.py ig")
    porta = int(sys.argv[sys.argv.index("--porta") + 1]) if "--porta" in sys.argv else 8765
    srv = ThreadingHTTPServer(("127.0.0.1", porta), H)
    url = f"http://127.0.0.1:{porta}"
    print(f"Dashboard em {url}  (Ctrl+C para sair)")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
