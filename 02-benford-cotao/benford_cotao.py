"""
Isso prova fraude? #2 — A Lei de Newcomb-Benford nas notas da cota parlamentar (CEAP) de 2026.

Pergunta: as notas fiscais reembolsadas pela Câmara em 2026 seguem a lei do primeiro dígito?
Onde não seguem, o que explica o desvio?

Dados: arquivo oficial da Câmara dos Deputados, uma linha por documento reembolsado.
  https://www.camara.leg.br/cotas/Ano-2026.csv.zip   (dicionário: dadosabertos.camara.leg.br)

Uso:
  python benford_cotao.py Ano-2026.csv.zip              # gera resultado_cotao.json e imprime o resumo
  python benford_cotao.py Ano-2026.csv.zip --sim 2000   # simulações por deputado (padrão 2000)

Regras do teste:
  - Valor: vlrDocumento (o valor da nota). Ficam de fora valores abaixo de R$ 10 (Nigrini, 2012,
    recomenda descartar valores pequenos) e devoluções (valores negativos).
  - Medidas: qui-quadrado (8 graus de liberdade) e desvio absoluto médio (MAD) de Nigrini.
    Faixas de Nigrini (2012) para o 1º dígito: até 0,006 conformidade próxima; 0,006 a 0,012
    aceitável; 0,012 a 0,015 marginal; acima de 0,015 não conformidade.
  - Com dezenas de milhares de notas, o qui-quadrado reprova qualquer desvio mínimo; por isso
    a referência é o MAD, como recomenda Nigrini.
  - Por deputado: como cada um tem poucas centenas de notas, o MAD de um deputado é comparado
    com o MAD que amostras do mesmo tamanho, sorteadas da própria Lei de Benford, teriam por acaso
    (Monte Carlo, percentil 99).
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import math

import numpy as np
import pandas as pd

BENFORD = np.log10(1 + 1 / np.arange(1, 10))  # 30,1 · 17,6 · 12,5 · 9,7 · 7,9 · 6,7 · 5,8 · 5,1 · 4,6 (%)
COMBUSTIVEL = "COMBUSTÍVEIS E LUBRIFICANTES."
DIVULGACAO = "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR."


def chi2_sf_8gl(x: float) -> float:
    """P(qui-quadrado com 8 graus de liberdade > x), fórmula fechada para graus pares (sem scipy)."""
    h = x / 2
    return math.exp(-h) * sum(h ** k / math.factorial(k) for k in range(4))


def nigrini(mad: float) -> str:
    if mad <= 0.006:
        return "conformidade próxima"
    if mad <= 0.012:
        return "conformidade aceitável"
    if mad <= 0.015:
        return "conformidade marginal"
    return "não conformidade"


def primeiro_digito(v: np.ndarray) -> np.ndarray:
    v = np.abs(v[v > 0])
    return (v / 10 ** np.floor(np.log10(v))).astype(int).clip(1, 9)


def teste(v: np.ndarray) -> dict:
    d = primeiro_digito(np.asarray(v, dtype=float))
    cont = np.bincount(d, minlength=10)[1:10]
    n = int(cont.sum())
    esp = BENFORD * n
    chi2 = float(((cont - esp) ** 2 / esp).sum())
    mad = float(np.abs(cont / n - BENFORD).mean())
    return {"n": n, "contagem": cont.tolist(), "pct": [round(float(100 * c / n), 1) for c in cont],
            "chi2": round(chi2, 1), "p": chi2_sf_8gl(chi2), "mad": round(mad, 4),
            "nigrini": nigrini(mad)}


def carregar(caminho: Path) -> pd.DataFrame:
    with zipfile.ZipFile(caminho) as z:
        nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        bruto = z.read(nome)
    df = pd.read_csv(io.BytesIO(bruto), sep=";", dtype=str, encoding="utf-8", keep_default_na=False)
    for c in ("vlrDocumento", "vlrLiquido", "vlrGlosa"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["numMes"] = pd.to_numeric(df["numMes"], errors="coerce")
    return df


def mad_aleatorio(n: int, sims: int, rng: np.random.Generator) -> np.ndarray:
    """MAD de `sims` amostras de tamanho n sorteadas da própria Lei de Benford."""
    amostras = rng.multinomial(n, BENFORD, size=sims) / n
    return np.abs(amostras - BENFORD).mean(axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zip", type=Path)
    ap.add_argument("--sim", type=int, default=2000)
    ap.add_argument("--min-notas", type=int, default=200)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--saida", type=Path, default=Path("resultado_cotao.json"))
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)

    df = carregar(a.zip)
    total_linhas = len(df)
    validas = df[df["vlrDocumento"] >= 10].copy()
    res = {
        "arquivo": a.zip.name,
        "linhas": total_linhas,
        "meses": sorted(int(m) for m in df["numMes"].dropna().unique()),
        "linhas_por_mes": {int(k): int(v) for k, v in df["numMes"].value_counts().sort_index().items()},
        "soma_vlrDocumento": round(float(df["vlrDocumento"].sum()), 2),
        "soma_vlrLiquido": round(float(df["vlrLiquido"].sum()), 2),
        "fora_do_teste": {"abaixo_de_10": int(((df["vlrDocumento"] > 0) & (df["vlrDocumento"] < 10)).sum()),
                          "zero_ou_negativo": int((df["vlrDocumento"] <= 0).sum())},
        "deputados": int(df["nuDeputadoId"].nunique()),
        "benford_pct": [round(float(100 * b), 1) for b in BENFORD],
    }

    # 1. Base inteira
    res["base_inteira"] = teste(validas["vlrDocumento"].values)

    # 2. Por categoria
    cats = []
    for cat, g in validas.groupby("txtDescricao"):
        t = teste(g["vlrDocumento"].values)
        t.update({"categoria": cat, "soma": round(float(g["vlrDocumento"].sum()), 2)})
        cats.append(t)
    res["por_categoria"] = sorted(cats, key=lambda t: -t["n"])

    # 3. Combustível: por que o 2 domina?
    comb = validas[validas["txtDescricao"] == COMBUSTIVEL]["vlrDocumento"]
    res["combustivel"] = {
        "n": int(len(comb)),
        "pct_comeca_com_2": round(100 * float((primeiro_digito(comb.values) == 2).mean()), 1),
        "pct_entre_200_e_299_99": round(100 * float(((comb >= 200) & (comb < 300)).mean()), 1),
        "pct_entre_100_e_499_99": round(100 * float(((comb >= 100) & (comb < 500)).mean()), 1),
        "mediana": round(float(comb.median()), 2),
        "p10": round(float(comb.quantile(0.10)), 2),
        "p90": round(float(comb.quantile(0.90)), 2),
        "pct_valores_redondos_10": round(100 * float((comb % 10 == 0).mean()), 1),
    }

    # 4. Sem combustível
    sem = validas[validas["txtDescricao"] != COMBUSTIVEL]
    res["sem_combustivel"] = teste(sem["vlrDocumento"].values)
    res["sem_combustivel"]["mad_99_aleatorio_mesmo_n"] = round(
        float(np.percentile(mad_aleatorio(res["sem_combustivel"]["n"], a.sim, rng), 99)), 4)

    # 5. Divulgação: valores redondos
    div = validas[validas["txtDescricao"] == DIVULGACAO]["vlrDocumento"]
    res["divulgacao"] = {
        "n": int(len(div)), "soma": round(float(div.sum()), 2),
        "pct_multiplo_de_1000": round(100 * float(((div >= 1000) & (div % 1000 == 0)).mean()), 1),
        "pct_multiplo_de_100": round(100 * float((div % 100 == 0).mean()), 1),
        "valores_mais_comuns": [[float(k), int(v)] for k, v in div.value_counts().head(10).items()],
    }

    # 6. Por deputado (sem combustível), contra o acaso
    deps = []
    cache = {}
    for (did, nome, pt, uf), g in sem.groupby(["nuDeputadoId", "txNomeParlamentar", "sgPartido", "sgUF"]):
        n = len(g)
        if n < a.min_notas or not did:
            continue
        t = teste(g["vlrDocumento"].values)
        if n not in cache:
            cache[n] = float(np.percentile(mad_aleatorio(n, a.sim, rng), 99))
        dig = int(np.argmax(np.array(t["pct"]) / 100 - BENFORD)) + 1
        sel = g[primeiro_digito(g["vlrDocumento"].values) == dig]
        top = (sel["txtDescricao"].str.slice(0, 40) + " | " + sel["txtFornecedor"].str.slice(0, 40)).value_counts().head(3)
        deps.append({"id": did, "nome": nome, "partido": pt, "uf": uf, "n": n, "mad": t["mad"],
                     "mad_99_acaso": round(cache[n], 4), "acima_do_acaso": t["mad"] > cache[n],
                     "digito_em_excesso": dig, "pct_digito": t["pct"][dig - 1],
                     "esperado_digito": round(100 * BENFORD[dig - 1], 1),
                     "onde_estao": [[k, int(v)] for k, v in top.items()]})
    deps.sort(key=lambda d: -d["mad"])
    res["por_deputado"] = {"min_notas": a.min_notas, "avaliados": len(deps),
                           "acima_do_acaso": sum(d["acima_do_acaso"] for d in deps),
                           "top10": deps[:10]}

    # 7. As notas de outubro dos casos do noticiário
    casos = {}
    for rotulo, padrao in (("Lêda Borges", r"L[êe]da Borges"), ("Antônia Lúcia", r"Ant[ôo]nia L[úu]cia")):
        g = df[df["txNomeParlamentar"].str.contains(padrao, case=False, regex=True)]
        out = g[(g["numMes"] == 10) & (g["txtDescricao"] == DIVULGACAO)]
        casos[rotulo] = {
            "notas_2026": int(len(g)),
            "notas_2026_sem_combustivel_ge10": int(((g["txtDescricao"] != COMBUSTIVEL) & (g["vlrDocumento"] >= 10)).sum()),
            "divulgacao_outubro": round(float(out["vlrDocumento"].sum()), 2),
            "notas_divulgacao_outubro": [
                {"valor": float(r.vlrDocumento), "fornecedor": r.txtFornecedor, "cnpj": r.txtCNPJCPF,
                 "emissao": r.datEmissao[:10], "url": r.urlDocumento} for r in out.itertuples()],
            "divulgacao_jan_mai_media_mensal": round(float(
                g[(g["numMes"].between(1, 5)) & (g["txtDescricao"] == DIVULGACAO)]["vlrDocumento"].sum() / 5), 2),
        }
    res["casos"] = casos

    a.saida.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    # Resumo
    b, s = res["base_inteira"], res["sem_combustivel"]
    print(f"Arquivo {res['arquivo']}: {total_linhas:,} notas, meses {res['meses']}, {res['deputados']} parlamentares/lideranças")
    print(f"Benford esperado (%):      {res['benford_pct']}")
    print(f"Base inteira  n={b['n']:,}: {b['pct']} | MAD {b['mad']} ({b['nigrini']})")
    c = res["combustivel"]
    print(f"Combustível   n={c['n']:,}: começa com 2 em {c['pct_comeca_com_2']}% | entre R$ 200 e 299 em "
          f"{c['pct_entre_200_e_299_99']}% | mediana R$ {c['mediana']}")
    print(f"Sem combustível n={s['n']:,}: {s['pct']} | MAD {s['mad']} ({s['nigrini']}) | acaso p99 {s['mad_99_aleatorio_mesmo_n']}")
    for t in res["por_categoria"][:10]:
        print(f"  {t['categoria'][:45]:45s} n={t['n']:6,} MAD {t['mad']:.4f} {t['nigrini']}")
    pd_ = res["por_deputado"]
    print(f"Deputados com {pd_['min_notas']}+ notas sem combustível: {pd_['avaliados']}; acima do acaso: {pd_['acima_do_acaso']}")
    for d in pd_["top10"][:5]:
        print(f"  {d['nome']} ({d['partido']}-{d['uf']}) n={d['n']} MAD {d['mad']} (acaso {d['mad_99_acaso']}) "
              f"dígito {d['digito_em_excesso']}: {d['pct_digito']}% vs {d['esperado_digito']}% -> {d['onde_estao'][0]}")
    for k, v in casos.items():
        print(f"{k}: divulgação em outubro R$ {v['divulgacao_outubro']:,.2f}; notas no ano {v['notas_2026']}")
    print(f"\nResultado salvo em {a.saida}")


if __name__ == "__main__":
    main()
