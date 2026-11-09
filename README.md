# Salvos Archive

🇧🇷 Português · [🇬🇧 English](README.en.md)

Transforma seus **bookmarks do X (Twitter)** e uma **coleção salva do Instagram** em um arquivo pessoal, **local e offline**: você pesquisa, filtra, categoriza e organiza tudo num dashboard, com fotos e vídeos baixados no seu computador.

- 🔒 Tudo roda na sua máquina. Sem conta, sem servidor, sem enviar nada para ninguém.
- 🆓 Só ferramentas gratuitas, sem IA paga.
- 🔎 Busca estilo Obsidian: `tag:genart -logo cor:azul fonte:ig "frase exata"`. Buscar **azul** também acha o que é visualmente azul.
- 🏷️ Sugere **tags e categorias** sozinho (genart, animation, motion, 3d, cerâmica…) e você aceita com um clique.
- 🖼️ 4 modos de ver: mosaico, grade, lista, linha do tempo. Cada item mostra de qual pasta/coleção veio.
- 📓 Bônus: exporta um *vault* do Obsidian.

---

## 1. Instalar (uma vez)

Você precisa de **Python 3.9+** ([python.org](https://www.python.org/downloads/); no Windows marque "Add to PATH") e do **ffmpeg** (só para vídeos).

```bash
git clone <URL-DESTE-REPOSITORIO>
cd salvos-archive
pip install -r requirements.txt
```

ffmpeg: Windows `winget install ffmpeg` · Mac `brew install ffmpeg` · Linux `sudo apt install ffmpeg`.

> No Mac/Linux use `python3` no lugar de `python`.

## 2. Pegar seus salvos do X

1. Abra **https://x.com/i/bookmarks** logado no Chrome (ou Edge/Firefox).
2. Aperte **F12** → aba **Console**.
3. Abra o arquivo [`x/console_snippet.js`](x/console_snippet.js), copie **tudo**, cole no console e aperte Enter. (Se o navegador pedir, digite `allow pasting` antes de colar.)
4. Ele rola a página sozinho e, no fim, baixa um arquivo `x_bookmarks_full_<data>.json`. Para parar antes: digite `stopExport()`.
5. Baixe tudo:

```bash
python salvos.py x
```

O arquivo é achado sozinho em `dados/entrada/` ou na sua pasta Downloads. Fotos, vídeos e textos completos vão para `dados/x/`. Rodar de novo só baixa o que é novo.

## 3. Pegar uma coleção do Instagram (opcional)

1. No Instagram (logado, no navegador), abra **Salvos → a coleção** que você quer.
2. F12 → Console, cole o conteúdo de [`instagram/console_snippet.js`](instagram/console_snippet.js) e Enter. Ele rola com pausas (de propósito, para não incomodar o Instagram) e baixa `ig_links_<colecao>_<data>.json`.
3. Rode:

```bash
python salvos.py ig
```

Posts públicos baixam **sem login**. Se algum for restrito: `python salvos.py ig --navegador chrome` (feche o Chrome antes) ou `--cookies cookies.txt`. Faça uma coleção por vez, o nome da coleção vira a "pasta" no dashboard. Para ir mais devagar: `--pausa 5`.

## 4. Abrir o dashboard

```bash
python salvos.py
```

Junta tudo, analisa as imagens, sugere tags e abre **http://127.0.0.1:8765** no navegador. Para parar, `Ctrl+C` no terminal.

### Como usar

| Quero… | Faça |
|---|---|
| Procurar | Digite na busca. Aceita `tag:`, `cat:`, `fonte:` (x/ig), `pasta:`, `autor:`, `cor:`, `tipo:` (video/foto/texto), `fav:1`, `-excluir` e `"frase exata"` |
| Filtrar | Botão **Filtros** (fonte, pasta, categoria, tag, cor, autor, data). Clicar de novo num item da barra lateral desmarca |
| Mudar a vista | Mosaico · Grade · Lista · Tempo |
| Categorizar | Clique no item → categoria, tags e nota. Tags/categorias **tracejadas** são sugestões: clique para aceitar |
| Vários de uma vez | **Selecionar** → marque os itens → adicionar tag / categoria / favoritar |

Suas tags, categorias, notas e favoritos ficam salvos em `dados/arquivo/library.json` e **nunca são apagados** quando você importa coisas novas.

### Sugestões de tags e categorias

São regras simples (palavras e hashtags do texto + nome da pasta), sem IA e sem internet. Para ensinar seus próprios assuntos, edite o dicionário `VOCABULARIO` no topo de [`arquivo/sugerir_tags.py`](arquivo/sugerir_tags.py). Para aceitar todas as sugestões de uma vez (sem volta):

```bash
python arquivo/sugerir_tags.py --aceitar
```

## 5. Bônus: Obsidian

```bash
python salvos.py obsidian
```

Gera `dados/vault/` com uma nota por salvo (com propriedades, tags `#cor/azul`, `#pasta/...`, mídia embutida). No Obsidian: *Open folder as vault*.

---

## Comandos

| Comando | O que faz |
|---|---|
| `python salvos.py x` | baixa os bookmarks do X |
| `python salvos.py ig` | baixa uma coleção do Instagram |
| `python salvos.py` | junta, analisa, sugere e abre o dashboard (`--porta 9000` muda a porta) |
| `python salvos.py atualizar` | igual, mas sem abrir o dashboard |
| `python salvos.py obsidian` | exporta o vault do Obsidian |

## Onde ficam as coisas

```
salvos-archive/
├─ salvos.py            comando único
├─ x/                   snippet + baixador do X
├─ instagram/           snippet + baixador do Instagram
├─ arquivo/             dashboard, busca, tags, Obsidian
└─ dados/               SEUS dados (fora do git): entrada/, x/, instagram/, arquivo/, vault/
```

## Privacidade

Nada sai do seu computador. O servidor do dashboard só escuta em `127.0.0.1` (ninguém na sua rede acessa). Os snippets só leem a página aberta no navegador. As únicas conexões externas são para baixar as mídias dos próprios posts (X, Instagram e a API pública de embed/syndication deles). A pasta `dados/` está no `.gitignore`: se você fizer um fork, seus salvos não sobem.

## Limitações conhecidas

- Textos muito longos do X (com "Mostrar mais") podem vir cortados; o programa tenta completar, mas alguns só aparecem inteiros logado.
- O snippet do X não captura as *pastas* de bookmarks do X: tudo entra como "Bookmarks".
- Posts do Instagram em carrossel são completados pela página pública de embed; pode falhar em posts privados.
- Instagram e X mudam o site de vez em quando; se um snippet parar de funcionar, abra uma issue.
- Cores: classificadas em 12 nomes por análise simples da imagem (não é perfeito).
- Respeite os termos de uso das plataformas e os direitos autorais: use para o **seu** arquivo pessoal.

## Créditos

O snippet do X parte do exportador do projeto QuantumMonkey (MIT). Downloads de vídeo por [yt-dlp](https://github.com/yt-dlp/yt-dlp). Licença: MIT.
