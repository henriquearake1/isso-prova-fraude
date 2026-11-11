"""
Isso prova fraude? #1 — Monte Carlo contra a Lei de Benford nas urnas.

Pergunta: se uma eleição fosse 100% limpa, quantas vezes o teste de Benford do 1º dígito,
aplicado aos votos por seção, "acusaria" fraude?

Método (Monte Carlo):
  1. Tamanhos de seção REAIS do 2º turno de 2026: os votos válidos (Lula + Flávio) de cada uma das
     499.205 seções dos boletins de urna do TSE.
  2. Em cada seção, cada eleitor vota no Lula com a chance que o Lula teve no MUNICÍPIO da seção
     (e no Flávio, com o resto). Nada é manipulado: a eleição é limpa por construção.
  3. Sorteia-se a eleição inteira 10.000 vezes. Em cada uma, aplica-se o teste de Benford do
     1º dígito aos votos do Lula por seção (qui-quadrado, 8 graus de liberdade, 5% de significância)
     e conta-se em quantas o teste "acusaria" fraude. O mesmo vale para os votos do Flávio.
  Controles: (A) moeda de 50% em todas as seções; (C) município + variação entre seções do mesmo
  município (beta-binomial); critério alternativo de Nigrini (MAD > 0,015).

Uso:
  python benford_monte_carlo.py                       # usa secoes_2t_2026_resumo.txt (resumo dos BU)
  python benford_monte_carlo.py --bu pasta_com_zips   # lê os bweb_2t_*.zip do TSE direto (dados por seção exatos)
  python benford_monte_carlo.py --n 1000              # menos simulações, mais rápido

Os boletins de urna (bweb_2t_<UF>_261020260742.zip, 144 MB no total) ficam em
https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

BENFORD = np.log10(1 + 1 / np.arange(1, 10))  # 30,1% · 17,6% · 12,5% · 9,7% · 7,9% · 6,7% · 5,8% · 5,1% · 4,6%
ALFA = 0.05
MAD_NIGRINI = 0.015  # acima disso, "não conformidade" no 1º dígito (Nigrini, 2012)


# ----------------------------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------------------------
def carregar_resumo(caminho: Path, rng: np.random.Generator):
    """Reconstrói as 499.205 seções a partir do resumo: tamanho exato de cada seção e a % do Lula
    no município (em faixas de 2 pontos). Devolve (votos_validos, p_municipio, extras)."""
    d = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.startswith("#"):
            continue
        chave, resto = linha.split(" ", 1)
        d[chave] = resto.split()
    nh = {int(a): int(b) for a, b in (x.split(":") for x in d["NH"])}
    jm = {tuple(map(int, a.split("."))): int(b) for a, b in (x.split(":") for x in d["JM"])}

    # Para cada faixa de 10 votos, junta os tamanhos exatos (NH) com as faixas de % municipal (JM)
    tamanhos_por_faixa = defaultdict(list)
    for v, c in nh.items():
        tamanhos_por_faixa[v // 10] += [v] * c
    pfaixa_por_faixa = defaultdict(list)
    for (vb, pb), c in jm.items():
        pfaixa_por_faixa[vb] += [pb] * c
    V, P = [], []
    for vb in sorted(tamanhos_por_faixa):
        t = np.array(tamanhos_por_faixa[vb])
        pb = np.array(pfaixa_por_faixa[vb])
        assert len(t) == len(pb), vb
        rng.shuffle(pb)
        V.append(t)
        P.append((pb + rng.random(len(pb))) / 50)  # faixa de 2 pontos -> valor dentro da faixa
    V = np.concatenate(V)
    P = np.clip(np.concatenate(P), 0.001, 0.999)
    extras = {k: list(map(int, d[k])) for k in ("D1_SECAO_L", "D1_SECAO_F", "D1_MUN_L", "D1_MUN_F")}
    return V, P, extras


def carregar_bu(pasta: Path):
    """Lê os zips do TSE (bweb_2t_*.zip) e devolve, por seção: votos válidos e % do Lula no município."""
    secoes = {}
    for zp in sorted(pasta.glob("bweb_2t_*.zip")):
        with zipfile.ZipFile(zp) as z:
            nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            with z.open(nome) as f:
                leitor = csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")
                for r in leitor:
                    if r["CD_CARGO_PERGUNTA"] != "1" or r["CD_TIPO_VOTAVEL"] != "1":
                        continue
                    k = (r["SG_UF"], r["CD_MUNICIPIO"], r["NR_ZONA"], r["NR_SECAO"])
                    s = secoes.setdefault(k, [0, 0])
                    s[0 if r["NR_VOTAVEL"] == "13" else 1] += int(r["QT_VOTOS"])
        print(f"  {zp.name}: {len(secoes):,} seções acumuladas", file=sys.stderr)
    mun = defaultdict(lambda: [0, 0])
    for (uf, m, _, _), (l, f) in secoes.items():
        mun[(uf, m)][0] += l
        mun[(uf, m)][1] += l + f
    V = np.array([l + f for l, f in secoes.values()])
    P = np.array([mun[(k[0], k[1])][0] / mun[(k[0], k[1])][1] for k in secoes])
    L = np.array([l for l, _ in secoes.values()])
    F = V - L
    extras = {"D1_SECAO_L": list(primeiro_digito_contagem(L)), "D1_SECAO_F": list(primeiro_digito_contagem(F))}
    return V, np.clip(P, 0.001, 0.999), extras


# ----------------------------------------------------------------------------------------------
# Teste de Benford
# ----------------------------------------------------------------------------------------------
def primeiro_digito_contagem(x: np.ndarray) -> np.ndarray:
    x = x[x > 0]
    d = (x // 10 ** np.floor(np.log10(x)).astype(np.int64)).astype(np.int64)
    return np.bincount(d, minlength=10)[1:10]


def teste_benford(cont: np.ndarray) -> dict:
    n = cont.sum()
    esperado = BENFORD * n
    chi2 = float(((cont - esperado) ** 2 / esperado).sum())
    p = float(stats.chi2.sf(chi2, df=8))
    mad = float(np.abs(cont / n - BENFORD).mean())
    return {"n": int(n), "chi2": chi2, "p": p, "mad": mad, "pct_digito_1": float(cont[0] / n),
            "acusa_chi2": p < ALFA, "acusa_mad": mad > MAD_NIGRINI}


# ----------------------------------------------------------------------------------------------
# Monte Carlo
# ----------------------------------------------------------------------------------------------
def simular(V, P, n_sim, rng, modelo="municipio", phi=100.0, fraude=None):
    """Sorteia n_sim eleições limpas. modelo: 'moeda' (p = 50%), 'municipio' (p = % do município),
    'municipio+variacao' (p de cada seção sorteado de uma beta em torno do município, concentração phi)."""
    res = []
    for _ in range(n_sim):
        if modelo == "moeda":
            p = np.full(V.shape, 0.5)
        elif modelo == "municipio":
            p = P
        else:
            p = rng.beta(P * phi, (1 - P) * phi)
        L = rng.binomial(V, p)
        if fraude is not None:  # controle: tira uma fração dos votos do Flávio numa fração das seções
            frac_secoes, frac_votos = fraude
            alvo = rng.random(len(V)) < frac_secoes
            mov = np.floor((V - L) * frac_votos).astype(np.int64) * alvo
            L = L + mov
        F = V - L
        tl, tf = teste_benford(primeiro_digito_contagem(L)), teste_benford(primeiro_digito_contagem(F))
        res.append({"L": tl, "F": tf})
    return res


def resumir(res):
    def frac(c, k):
        return sum(r[c][k] for r in res)
    n = len(res)
    out = {"n_sim": n}
    for c in ("L", "F"):
        chi = np.array([r[c]["chi2"] for r in res])
        mad = np.array([r[c]["mad"] for r in res])
        d1 = np.array([r[c]["pct_digito_1"] for r in res])
        out[c] = {
            "acusa_chi2": frac(c, "acusa_chi2"), "acusa_mad": frac(c, "acusa_mad"),
            "chi2_min": float(chi.min()), "chi2_mediana": float(np.median(chi)), "p_max": max(r[c]["p"] for r in res),
            "mad_min": float(mad.min()), "mad_mediana": float(np.median(mad)),
            "pct_digito_1_min": float(d1.min()), "pct_digito_1_mediana": float(np.median(d1)), "pct_digito_1_max": float(d1.max()),
        }
    out["acusa_algum"] = sum(r["L"]["acusa_chi2"] or r["F"]["acusa_chi2"] for r in res)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", default=Path(__file__).with_name("secoes_2t_2026_resumo.txt"), type=Path)
    ap.add_argument("--bu", type=Path, help="pasta com os bweb_2t_*.zip do TSE")
    ap.add_argument("--n", type=int, default=10_000, help="simulações do modelo principal")
    ap.add_argument("--n-controle", type=int, default=1_000, help="simulações de cada controle")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--saida", type=Path, default=Path("resultado_monte_carlo.json"))
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)

    V, P, extras = carregar_bu(a.bu) if a.bu else carregar_resumo(a.resumo, rng)
    print(f"Seções: {len(V):,} | votos válidos: {V.sum():,} | mediana por seção: {int(np.median(V))} "
          f"| 5% a 95%: {int(np.percentile(V, 5))} a {int(np.percentile(V, 95))}")

    real = {"secoes_L": teste_benford(np.array(extras["D1_SECAO_L"])),
            "secoes_F": teste_benford(np.array(extras["D1_SECAO_F"]))}
    if "D1_MUN_L" in extras:
        real["municipios_L"] = teste_benford(np.array(extras["D1_MUN_L"]))
        real["municipios_F"] = teste_benford(np.array(extras["D1_MUN_F"]))
    for k, t in real.items():
        print(f"REAL {k:13s}: 1º dígito = 1 em {t['pct_digito_1']:.1%} | chi2 {t['chi2']:,.0f} | p {t['p']:.2g} | MAD {t['mad']:.4f}")

    resultado = {"dados": {"secoes": int(len(V)), "votos_validos": int(V.sum()),
                           "mediana": float(np.median(V)), "p5": float(np.percentile(V, 5)), "p95": float(np.percentile(V, 95))},
                 "real": real, "simulacoes": {}}
    t0 = time.time()
    for nome, kw, n in [("municipio", {"modelo": "municipio"}, a.n),
                        ("moeda", {"modelo": "moeda"}, a.n_controle),
                        ("municipio+variacao", {"modelo": "municipio+variacao"}, a.n_controle),
                        ("com_fraude_1pct_secoes_20pct_votos", {"modelo": "municipio", "fraude": (0.01, 0.20)}, a.n_controle)]:
        r = resumir(simular(V, P, n, rng, **kw))
        resultado["simulacoes"][nome] = r
        print(f"{nome:36s}: {r['L']['acusa_chi2']:,} de {n:,} acusadas (Lula, qui-quadrado) | "
              f"{r['F']['acusa_chi2']:,} (Flávio) | MAD>0,015: {r['L']['acusa_mad']:,} | "
              f"maior p: {r['L']['p_max']:.1e} | 1º dígito = 1 entre {r['L']['pct_digito_1_min']:.1%} e {r['L']['pct_digito_1_max']:.1%} "
              f"[{time.time() - t0:.0f}s]")
    a.saida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f"\nResultado salvo em {a.saida}")


if __name__ == "__main__":
    main()
