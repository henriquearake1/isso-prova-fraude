"""
Isso prova fraude? #1 — a simulação de Monte Carlo do Tarcísio, refeita.

O que o governador fez (vídeo publicado no X em 25/10/2026, transcrição no guia):
  votos do Flávio no 2º turno = votos do Flávio no 1º turno de 2026
                                + votos dos outros candidatos no 1º turno de 2026
                                  × taxa de conversão de 2022 × fator aleatório (distribuição normal)
  taxa de conversão = (votos do candidato no 2º turno − no 1º turno) ÷ votos dos outros candidatos no 1º turno
  Resultado dele: 90% dos sorteios entre 51,8% e 53,6% para o Flávio; mediana 52,6% a 52,7%; ~63 mi × 57 mi.
  Ele fez por estado; aqui a conta é nacional, e chega ao mesmo resultado (52,5%).

Este script também roda os exemplos do vídeo: o pachinko (tábua de Galton) e a carteira de processos.
Uso: python tarcisio_monte_carlo.py   (precisa de numpy)
"""

from math import comb

import numpy as np

rng = np.random.default_rng(2026)
N = 100_000

# ------------------------------------------------------------------------------------------------
# Dados (TSE; anos anteriores conferidos na Wikipédia, tabelas de resultado de cada eleição)
# ------------------------------------------------------------------------------------------------
F1, L1, O1 = 56_104_503, 53_879_538, 9_316_747      # 2026, 1º turno: Flávio, Lula, outros candidatos
F2, L2 = 59_826_041, 64_256_232                     # 2026, 2º turno
ANOS = {  # candidato do PT (1º, 2º turno), adversário (1º, 2º turno), votos válidos no 1º turno
    2002: (39_455_233, 52_793_364, 19_705_445, 33_370_739, 84_952_512),
    2006: (46_662_365, 58_295_042, 39_968_369, 37_543_178, 96_022_502),
    2010: (47_651_434, 55_752_529, 33_132_283, 43_711_388, 101_590_153),
    2014: (43_267_668, 54_501_118, 34_897_211, 51_041_155, 104_023_543),
    2018: (31_342_051, 47_040_906, 49_276_990, 57_797_847, 107_050_749),
    2022: (57_259_504, 60_345_999, 51_072_345, 58_206_354, 118_229_719),
}


def flavio(taxa_pt, taxa_adv, fator_pt=1.0, fator_adv=1.0):
    lula = L1 + O1 * taxa_pt * fator_pt
    fla = F1 + O1 * taxa_adv * fator_adv
    return fla / (fla + lula), fla, lula


def main():
    print("== Pachinko (tábua de Galton), 11 fileiras de pinos ==")
    for p in (0.5, 0.6):
        direita = sum(comb(11, k) * p**k * (1 - p) ** (11 - k) for k in range(6, 12))
        sim = (rng.binomial(11, p, 10_000) >= 6).mean()
        print(f"  pinos com {p:.0%} para a direita: {direita:.1%} das bolinhas à direita (10 mil sorteadas: {sim:.1%})")

    print("\n== A regra de cada eleição (taxa de conversão do Tarcísio) aplicada ao 1º turno de 2026 ==")
    taxas = {}
    for ano, (p1, p2, a1, a2, v) in ANOS.items():
        outros = v - p1 - a1
        tp, ta = (p2 - p1) / outros, (a2 - a1) / outros
        taxas[ano] = (tp, ta)
        cresc_pt = (p2 - p1) / ((p2 - p1) + (a2 - a1))
        sh, fla, lula = flavio(tp, ta)
        print(f"  {ano}: taxa PT {tp:5.0%} | adversário {ta:5.0%} | PT ficou com {cresc_pt:4.0%} do crescimento"
              f" | Flávio teria {sh:.1%} ({fla / 1e6:.1f} mi × {lula / 1e6:.1f} mi)")
    tp26, ta26 = (L2 - L1) / O1, (F2 - F1) / O1
    print(f"  2026 real: taxa Lula {tp26:.0%} | Flávio {ta26:.0%} | Lula ficou com "
          f"{(L2 - L1) / ((L2 - L1) + (F2 - F1)):.0%} do crescimento | Flávio teve {F2 / (F2 + L2):.1%}")

    print("\n== O sorteio do Tarcísio: regra de 2022 fixa, fator aleatório normal (média 1) ==")
    tp, ta = taxas[2022]
    for s in (0.10, 0.15, 0.20, 0.30):
        sh, _, _ = flavio(tp, ta, rng.normal(1, s, N), rng.normal(1, s, N))
        q = np.percentile(sh, [5, 50, 95])
        print(f"  fator com desvio de {s:.0%}: 90% entre {q[0]:.1%} e {q[2]:.1%}, mediana {q[1]:.1%};"
              f" Lula vence em {(sh < 0.5).mean():.2%}")
    print(f"  Para chegar ao resultado real, o fator do Lula teria de valer {tp26 / tp:.1f} e o do Flávio {ta26 / ta:.2f}")

    print("\n== Monte Carlo com a premissa também sorteada (uma das seis eleições de 2002 a 2022) ==")
    arr = np.array([taxas[a] for a in ANOS])
    idx = rng.integers(0, len(arr), N)
    sh, _, _ = flavio(arr[idx, 0], arr[idx, 1], rng.normal(1, 0.10, N), rng.normal(1, 0.10, N))
    q = np.percentile(sh, [5, 50, 95])
    print(f"  90% entre {q[0]:.1%} e {q[2]:.1%}; Lula vence em {(sh < 0.5).mean():.0%} dos sorteios; resultado real: 48,2%")

    print("\n== Carteira de 1.000 processos de R$ 40 mil, 30% de chance de condenação cada ==")
    ind = rng.binomial(1000, 0.30, 10_000) * 40_000
    q = np.percentile(ind, [5, 95])
    print(f"  independentes: média R$ {ind.mean() / 1e6:.1f} mi; 9 em 10 cenários entre R$ {q[0] / 1e6:.1f} e {q[1] / 1e6:.1f} mi")
    cai = rng.random(10_000) < 0.30          # a tese comum cai em 30% dos cenários
    dep = rng.binomial(1000, np.where(cai, 0.95, 0.02)) * 40_000
    print(f"  uma tese comum (cai em 30%; aí 95% de condenação, senão 2%): média R$ {dep.mean() / 1e6:.1f} mi;"
          f" cenários entre R$ 10 e 14 mi: {((dep >= 10e6) & (dep <= 14e6)).mean():.1%};"
          f" perto de R$ 1 mi: {(dep < 3e6).mean():.0%}; perto de R$ 38 mi: {(dep > 30e6).mean():.0%}")


if __name__ == "__main__":
    main()
