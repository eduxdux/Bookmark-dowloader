"""
salvos.py - comando único do projeto.  /  single entry point.

    python salvos.py x          # baixa seus bookmarks do X (precisa do JSON do snippet)
    python salvos.py ig         # baixa uma coleção do Instagram (precisa do JSON do snippet)
    python salvos.py            # junta tudo, analisa, sugere tags e ABRE o dashboard
    python salvos.py atualizar  # só junta/analisa/sugere (sem abrir o dashboard)
    python salvos.py obsidian   # exporta um vault do Obsidian em dados/vault/
    python salvos.py ajuda

Argumentos extras vão para o script de baixo, ex.:  python salvos.py ig --pausa 5   |   python salvos.py --porta 9000
Extra arguments are passed through to the underlying script.
"""
import os, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def rodar(script, *args, obrigatorio=True):
    r = subprocess.run([PY, os.path.join(AQUI, script), *args])
    if r.returncode and obrigatorio:
        sys.exit(r.returncode)
    return r.returncode


def atualizar():
    rodar("arquivo/importar.py")
    if rodar("arquivo/indexar.py", obrigatorio=False):
        print("[aviso] análise de cores pulada (pip install -r requirements.txt). O resto funciona.")
    rodar("arquivo/sugerir_tags.py")


def main():
    cmd, resto = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else ("abrir", sys.argv[1:])
    if cmd == "x":
        rodar("x/x.py", *resto)
    elif cmd in ("ig", "instagram"):
        rodar("instagram/ig.py", *resto)
    elif cmd == "atualizar":
        atualizar()
    elif cmd == "obsidian":
        rodar("arquivo/exportar_obsidian.py", *resto)
    elif cmd == "abrir":
        atualizar()
        rodar("arquivo/servidor.py", *resto)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
