/**
 * Instagram - exporta os links de UMA coleção de salvos / exports the links of ONE saved collection
 *
 * PT: 1) Entre no instagram.com, abra Salvos > sua coleção (URL com /saved/<nome>/<id>/)
 *     2) F12 > Console, cole tudo e Enter ("allow pasting" se o Chrome pedir)
 *     3) Para parar antes: stopExport()
 *     Baixa ig_links_<colecao>_<data>.json e .txt. Só lê a página, nada sai do navegador.
 * EN: open Saved > your collection, paste in the console, press Enter. stopExport() to stop early.
 *     Downloads ig_links_<collection>_<date>.json and .txt. Runs locally, reads the page only.
 */
(async function () {
    const PAUSA_MS = 2500;      // pausa entre rolagens / pause between scrolls
    const MAX_SEM_NOVOS = 8;    // rolagens seguidas sem novos = fim / idle scrolls before stopping
    const posts = new Map();
    let rodando = true;
    window.stopExport = () => { rodando = false; console.log("Parando..."); };

    function coletar() {
        let novos = 0;
        document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"], a[href*="/tv/"]').forEach(a => {
            const m = (a.getAttribute("href") || "").match(/\/(p|reel|tv)\/([\w-]+)/);
            if (!m || posts.has(m[2])) return;
            const img = a.querySelector("img");
            posts.set(m[2], {
                id: m[2],
                tipo: m[1] === "p" ? "post" : m[1],
                url: `https://www.instagram.com/${m[1]}/${m[2]}/`,
                miniatura: img ? img.getAttribute("src") : null,
                alt: img ? img.getAttribute("alt") : null
            });
            novos++;
        });
        return novos;
    }

    console.log("%c[IG] Coletando a coleção. Não troque de aba. stopExport() para parar.", "color:#e1306c;font-weight:bold");
    let semNovos = 0;
    while (rodando) {
        const novos = coletar();
        if (novos) { semNovos = 0; console.log(`+${novos} (total ${posts.size})`); } else semNovos++;
        if (semNovos >= MAX_SEM_NOVOS) break;
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, PAUSA_MS));
    }
    coletar();
    const colecao = (location.pathname.match(/\/saved\/([^/]+)/) || [, "colecao"])[1];
    const ts = new Date().toISOString().replace("T", "_").replace(/\..+/, "").replace(/:/g, "-");
    const lista = Array.from(posts.values()).map(p => ({ ...p, colecao }));
    const baixar = (c, n, t) => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([c], { type: t })); a.download = n; a.click(); };
    baixar(JSON.stringify(lista, null, 2), `ig_links_${colecao}_${ts}.json`, "application/json");
    baixar(lista.map(p => p.url).join("\n"), `ig_links_${colecao}_${ts}.txt`, "text/plain");
    console.log(`%c[IG] Pronto: ${lista.length} posts.`, "color:#2ecc71;font-weight:bold");
})();
