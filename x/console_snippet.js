/**
 * X (Twitter) Bookmarks Exporter COMPLETO - Snippet para o Console do navegador
 *
 * Baseado no console_snippet.js do repo QuantumMonkey (MIT), mas agora captura também:
 * nome do autor, @, data, texto, foto de perfil, links do texto, métricas e
 * se o texto está cortado ("Mostrar mais").
 *
 * Como usar:
 * 1. Entre no x.com e abra https://x.com/i/bookmarks
 * 2. F12 (ou Ctrl+Shift+J) -> aba Console
 * 3. Cole TUDO e aperte Enter (se o Chrome pedir, digite "allow pasting" antes)
 * 4. Para parar antes: digite stopExport() e Enter
 *
 * Ele baixa 2 arquivos:
 *   x_bookmarks_full_<data>.json  (dados completos, usado pelo x/x.py)
 *   x_bookmarks_<data>.txt        (só os links, lista de links)
 *
 * Nada sai do seu navegador: o script só lê a página e gera arquivos locais.
 */

(async function () {
    const estilo = "color: #1da1f2; font-weight: bold;";
    console.log("%c[Exporter completo] Iniciando...", estilo + " font-size: 14px;");

    const tweets = new Map();
    let lastHeight = document.body.scrollHeight;
    let noChangeCount = 0;
    let isRunning = true;

    window.stopExport = function () {
        console.log("%c[Exporter completo] Parando manualmente...", "color: #ffcc00; font-weight: bold;");
        isRunning = false;
    };

    // Texto do elemento mantendo emojis (o X usa <img alt="😀"> para emoji)
    function textoDe(node) {
        let out = "";
        node.childNodes.forEach(n => {
            if (n.nodeType === 3) {
                out += n.textContent;
            } else if (n.nodeType === 1) {
                if (n.tagName === "IMG") out += n.getAttribute("alt") || "";
                else if (n.tagName === "BR") out += "\n";
                else out += textoDe(n);
            }
        });
        return out;
    }

    function avatarGrande(src) {
        if (!src) return null;
        return src.replace(/_(normal|bigger|mini|x96|200x200|reasonably_small)(\.\w+)(\?.*)?$/, "_400x400$2");
    }

    function imagemOriginal(src) {
        let o = src.replace(/name=\w+/, "name=orig");
        if (!o.includes("name=")) o += o.includes("?") ? "&name=orig" : "?name=orig";
        return o;
    }

    // "1 resposta, 3 reposts, 27 curtidas, 914 visualizações" -> números
    function parseMetricas(s) {
        const m = { respostas: null, reposts: null, curtidas: null, salvos: null, visualizacoes: null };
        if (!s) return m;
        const pega = re => { const r = s.match(re); return r ? parseInt(r[1].replace(/[.,\s]/g, ""), 10) : null; };
        m.respostas = pega(/([\d.,]+)\s+(?:respostas?|repl(?:y|ies))/i);
        m.reposts = pega(/([\d.,]+)\s+reposts?/i);
        m.curtidas = pega(/([\d.,]+)\s+(?:curtidas?|likes?)/i);
        m.salvos = pega(/([\d.,]+)\s+(?:itens|items|bookmarks?)\s+salvos?|([\d.,]+)\s+bookmarks?/i);
        m.visualizacoes = pega(/([\d.,]+)\s+(?:visualiza\S*|views?)/i);
        return m;
    }

    function extrairTweet(article) {
        const timeEl = article.querySelector("time");
        const a = timeEl ? timeEl.closest("a") : null;
        const href = a ? a.getAttribute("href") : null;
        if (!href) return null;

        const cleanPath = href.split("?")[0];
        const fullUrl = cleanPath.startsWith("http") ? cleanPath : `https://x.com${cleanPath}`;
        const m = cleanPath.match(/^\/([^/]+)\/status\/(\d+)/);

        // Autor
        const userBlock = article.querySelector('[data-testid="User-Name"]');
        let nome = null;
        if (userBlock) {
            const linkNome = userBlock.querySelector("a");
            nome = linkNome ? textoDe(linkNome).trim() : null;
        }

        // Texto
        const textoEl = article.querySelector('[data-testid="tweetText"]');
        const texto = textoEl ? textoDe(textoEl).trim() : "";
        const links = [];
        if (textoEl) {
            textoEl.querySelectorAll("a[href]").forEach(l => {
                const h = l.getAttribute("href");
                if (h && !links.some(x => x.href === h)) {
                    links.push({ texto: textoDe(l).trim(), href: h.startsWith("/") ? `https://x.com${h}` : h });
                }
            });
        }

        // Foto de perfil
        const avImg = article.querySelector('[data-testid="Tweet-User-Avatar"] img');
        const avatar = avatarGrande(avImg ? avImg.getAttribute("src") : null);

        // Imagens (mesma lógica do snippet original)
        const imageUrls = [];
        article.querySelectorAll('div[data-testid="tweetPhoto"] img').forEach(img => {
            const src = img.getAttribute("src");
            if (src) imageUrls.push(imagemOriginal(src));
        });

        const hasVideo = article.querySelector("video") !== null ||
                         article.querySelector('[data-testid="videoPlayer"]') !== null;

        // Métricas (o X coloca um resumo no aria-label, no idioma da interface)
        const grupo = article.querySelector('[role="group"][aria-label]');

        return {
            url: fullUrl,
            id: m ? m[2] : cleanPath.split("/").pop(),
            usuario: m ? m[1] : null,
            nome: nome,
            data: timeEl.getAttribute("datetime") || null,
            texto: texto,
            idioma: textoEl ? textoEl.getAttribute("lang") : null,
            texto_cortado: article.querySelector('[data-testid="tweet-text-show-more-link"]') !== null,
            links: links,
            avatar: avatar,
            images: imageUrls,
            has_video: hasVideo,
            metricas: parseMetricas(grupo ? grupo.getAttribute("aria-label") : null),
            metricas_texto: grupo ? grupo.getAttribute("aria-label") : null
        };
    }

    // Quanto mais informação, maior a pontuação (usado para atualizar capturas parciais)
    function pontos(t) {
        return (t.texto ? t.texto.length : 0) + t.images.length * 100 +
               (t.avatar ? 50 : 0) + (t.nome ? 20 : 0) + (t.metricas_texto ? 10 : 0);
    }

    function coletar() {
        let novos = 0;
        document.querySelectorAll('article[data-testid="tweet"]').forEach(article => {
            let t;
            try { t = extrairTweet(article); } catch (e) { return; }
            if (!t) return;
            const antigo = tweets.get(t.url);
            if (!antigo) {
                tweets.set(t.url, t);
                novos++;
            } else if (pontos(t) > pontos(antigo)) {
                tweets.set(t.url, t); // captura melhor (imagem/avatar que carregou depois)
            }
        });
        return novos;
    }

    function baixarArquivo(conteudo, nome, tipo) {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([conteudo], { type: tipo }));
        a.download = nome;
        a.click();
        URL.revokeObjectURL(a.href);
    }

    function clicarRetry() {
        const textos = ["retry", "try again", "tentar novamente", "repetir"];
        for (const btn of document.querySelectorAll('button, [role="button"]')) {
            const txt = btn.textContent ? btn.textContent.trim().toLowerCase() : "";
            if (textos.some(t => txt === t || txt.includes(t))) {
                console.log("%c[Exporter completo] Erro/limite detectado. Clicando em 'Tentar novamente'...", "color: #e74c3c; font-weight: bold;");
                btn.click();
                return true;
            }
        }
        return false;
    }

    console.log("%cRolando e coletando. Não feche nem troque de aba.", estilo);
    console.log("Para parar a qualquer momento, digite stopExport() e Enter.");

    while (isRunning) {
        const novos = coletar();
        if (novos > 0) {
            console.log(`%cColetados ${novos} novos. Total: ${tweets.size}`, "color: #2ecc71;");
            noChangeCount = 0;
        }

        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 2000));

        const newHeight = document.body.scrollHeight;
        if (newHeight === lastHeight) {
            if (clicarRetry()) {
                await new Promise(r => setTimeout(r, 5000));
                noChangeCount = Math.max(0, noChangeCount - 2);
                continue;
            }
            noChangeCount++;
            console.log(`Nada novo carregou (tentativa ${noChangeCount}/30)...`);
            if (noChangeCount >= 30) {
                console.log("%cChegou ao fim dos bookmarks (ou limite do X).", estilo);
                break;
            }
        } else {
            lastHeight = newHeight;
            noChangeCount = 0;
        }
    }

    coletar(); // última passada
    console.log(`%cConcluído! Total de bookmarks: ${tweets.size}`, estilo + " font-size: 14px;");

    if (tweets.size > 0) {
        const lista = Array.from(tweets.values());
        const cortados = lista.filter(t => t.texto_cortado).length;
        if (cortados > 0) {
            console.log(`%c${cortados} tweet(s) longo(s) estão com o texto cortado ("Mostrar mais"). Veja o campo texto_cortado no JSON.`, "color: #ffcc00;");
        }
        const ts = new Date().toISOString().replace(/T/, "_").replace(/\..+/, "").replace(/:/g, "-");
        const nomeJson = `x_bookmarks_full_${ts}.json`;
        const nomeTxt = `x_bookmarks_${ts}.txt`;
        baixarArquivo(lista.map(t => t.url).join("\n"), nomeTxt, "text/plain");
        baixarArquivo(JSON.stringify(lista, null, 2), nomeJson, "application/json");
        console.log(`%cArquivos baixados:\n1. ${nomeTxt}\n2. ${nomeJson}`, "color: #2ecc71; font-weight: bold;");
    } else {
        console.log("%cNenhum bookmark encontrado. Confira se está logado e em https://x.com/i/bookmarks", "color: #e74c3c; font-weight: bold;");
    }
})();
