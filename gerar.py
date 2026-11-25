"""Desenha assets/atividade.svg com os números públicos do GitHub. Sem dependências."""
import json
import math
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USUARIO = "takkedaz"
SAIDA = Path(__file__).parent / "assets" / "atividade.svg"
CORES = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6", "CSS": "#a371f7", "HTML": "#e34c26",
         "Python": "#4b8bbe", "Java": "#b07219", "Shell": "#89e051"}
TEAL, BRANCO, CINZA, FUNDO = "#2dd4bf", "#e6edf3", "#8b949e", "#0b0e14"
FONTE = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def api(caminho):
    pedido = urllib.request.Request("https://api.github.com" + caminho,
                                    headers={"Accept": "application/vnd.github+json", "User-Agent": "perfil-svg"})
    if os.environ.get("GITHUB_TOKEN"):
        pedido.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    with urllib.request.urlopen(pedido, timeout=30) as r:
        return json.load(r)


def dados():
    repos = [r for r in api(f"/users/{USUARIO}/repos?per_page=100") if not r["fork"]]
    desde = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    linguagens, commits = {}, 0
    for r in repos:
        for nome, tamanho in api(f"/repos/{USUARIO}/{r['name']}/languages").items():
            linguagens[nome] = linguagens.get(nome, 0) + tamanho
        pagina = 1
        while True:
            # sem filtrar por autor: commit com e-mail não cadastrado na conta sumiria; só os do robô saem
            lote = api(f"/repos/{USUARIO}/{r['name']}/commits?since={desde}&per_page=100&page={pagina}")
            commits += sum(1 for c in lote if not c["commit"]["author"]["name"].endswith("[bot]"))
            if len(lote) < 100:
                break
            pagina += 1
    total = sum(linguagens.values()) or 1
    ordem = sorted(((n, t / total) for n, t in linguagens.items()), key=lambda x: -x[1])[:5]
    return ordem, [("Repositórios", len(repos)), ("Commits no último ano", commits),
                   ("Demos no ar", sum(1 for r in repos if r["has_pages"])), ("Linguagens", len(linguagens))]


def texto(x, y, conteudo, tam=14, cor=BRANCO, peso=400, ancora="start"):
    return (f'<text x="{x}" y="{y}" font-size="{tam}" fill="{cor}" font-weight="{peso}" '
            f'text-anchor="{ancora}">{conteudo}</text>')


def cartao(x, y, w, h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{FUNDO}" stroke="{BRANCO}" stroke-width="1.5"/>'


def radar(linguagens):
    eixos = linguagens + [("", 0)] * max(0, 3 - len(linguagens))
    cx, cy, raio, n = 210, 188, 100, len(eixos)
    maior = eixos[0][1] or 1

    def ponto(i, r):
        a = -math.pi / 2 + 2 * math.pi * i / n
        return cx + r * math.cos(a), cy + r * math.sin(a)

    def poligono(raios, **atr):
        pts = " ".join("%.1f,%.1f" % ponto(i, r) for i, r in enumerate(raios))
        return f'<polygon points="{pts}" ' + " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in atr.items()) + "/>"

    s = [poligono([raio * k / 4] * n, fill="none", stroke="#30363d") for k in range(1, 5)]
    for i, (nome, _) in enumerate(eixos):
        x, y = ponto(i, raio)
        s.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#30363d"/>')
        lx, ly = ponto(i, raio + 18)
        ancora = "middle" if abs(lx - cx) < 5 else ("start" if lx > cx else "end")
        s.append(texto(round(lx), round(ly + 4), nome, 13, ancora=ancora))
    raios = [raio * math.sqrt(p / maior) for _, p in eixos]
    s.append(poligono(raios, fill=TEAL, fill_opacity=".28", stroke=TEAL, stroke_width="2.5"))
    s += ['<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (*ponto(i, r), TEAL) for i, r in enumerate(raios)]
    return "".join(s)


def desenhar(linguagens, numeros, data):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="854" height="448" viewBox="0 0 854 448" '
         f'font-family="{FONTE}">', cartao(1, 1, 420, 338), cartao(433, 1, 420, 338), cartao(1, 351, 852, 96)]
    s.append(texto(22, 36, "Radar de linguagens", 16, TEAL, 600))
    s.append(radar(linguagens))
    s.append(texto(22, 322, "Proporção de código por linguagem, escala raiz quadrada", 12, CINZA))

    s.append(texto(454, 36, "Principais linguagens", 16, TEAL, 600))
    s.append('<clipPath id="barra"><rect x="454" y="56" width="378" height="9" rx="4.5"/></clipPath>'
             '<g clip-path="url(#barra)">')
    x = 454.0
    for nome, p in linguagens:
        s.append(f'<rect x="{x:.1f}" y="56" width="{378 * p + 0.5:.1f}" height="9" fill="{CORES.get(nome, CINZA)}"/>')
        x += 378 * p
    s.append("</g>")
    for i, (nome, p) in enumerate(linguagens):
        y, cor = 98 + i * 44, CORES.get(nome, CINZA)
        pct = f"{p * 100:.1f}".replace(".", ",") + "%"
        s.append(f'<circle cx="460" cy="{y - 5}" r="6" fill="{cor}"/>' + texto(476, y, nome, 14)
                 + texto(832, y, pct, 14, TEAL, ancora="end")
                 + f'<rect x="454" y="{y + 11}" width="378" height="4" rx="2" fill="#21262d"/>'
                 + f'<rect x="454" y="{y + 11}" width="{max(4, 378 * p):.1f}" height="4" rx="2" fill="{cor}"/>')
    s.append(texto(454, 322, f"atualizado em {data}", 12, CINZA))

    for i, (rotulo, valor) in enumerate(numeros):
        x = 22 + i * 213
        if i:
            s.append(f'<line x1="{x - 18}" y1="368" x2="{x - 18}" y2="430" stroke="#30363d"/>')
        s.append(texto(x, 383, rotulo, 13, CINZA) + texto(x, 424, valor, 28, TEAL, 600))
    return "".join(s) + "</svg>\n"


if __name__ == "__main__":
    linguagens, numeros = dados()
    hoje = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    novo = desenhar(linguagens, numeros, hoje)
    sem_data = lambda t: re.sub(r"atualizado em [\d/]+", "", t)
    # só regrava quando algum número muda, para o robô não criar um commit por dia à toa
    if not SAIDA.exists() or sem_data(SAIDA.read_text(encoding="utf-8")) != sem_data(novo):
        SAIDA.parent.mkdir(exist_ok=True)
        SAIDA.write_text(novo, encoding="utf-8", newline="\n")
    print(linguagens, numeros)
