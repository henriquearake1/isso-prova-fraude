# #1 · A simulação de Monte Carlo do Tarcísio

No domingo da eleição (25/10/2026), o governador Tarcísio de Freitas publicou no X uma simulação de Monte Carlo feita com dados do TSE: 53% para o Flávio Bolsonaro, com "90% das ocorrências entre 51,8% e 53,6%". O Flávio teve 48,21%.

Este código refaz a conta e mostra onde ela errou.

## O que a conta do Tarcísio fazia

Nas palavras dele, no vídeo:

> votos do segundo turno do Flávio = votos do primeiro turno do Flávio + votos do primeiro turno dos outros candidatos × taxa de transferência × fator aleatório

A "taxa de transferência" é a de 2022: quanto cada finalista cresceu entre os turnos, dividido pelos votos dos outros candidatos no 1º turno. O fator aleatório segue uma distribuição normal.

## O que o código mostra

| | Flávio no 2º turno |
|---|---|
| Regra de 2022, sem sorteio (versão nacional) | 52,5% |
| Regra de 2022 com o sorteio, fator variando até 30% | 90% entre 51,0% e 53,9%; o Lula vence em 0,3% dos sorteios |
| Regra de cada eleição desde 2002 | 2002: 51,0% · 2006: 45,1% · 2010: 51,4% · 2014: 51,7% · 2018: 49,9% · 2022: 52,5% |
| Regra também sorteada entre as seis eleições | 90% entre 44,8% e 52,7%; o Lula vence em 28% dos sorteios |
| **Resultado real** | **48,2%** |

O sorteio só variava os números em volta da regra de 2022, que era a mais favorável ao Flávio entre os seis segundos turnos desde 2002. Em 2022, o Bolsonaro ficou com 70% do que os dois finalistas cresceram entre os turnos; em 2026, o Lula ficou com 74%. A simulação estava certa; a premissa, não.

O código também roda os dois exemplos do vídeo: o pachinko (tábua de Galton) e uma carteira hipotética de 1.000 processos, que mostra a diferença entre riscos independentes e riscos que dependem de uma mesma tese.

## Arquivos

- `tarcisio_monte_carlo.py`: o código (Python 3 + numpy; roda em segundos).
- `saida.txt`: o resultado de uma execução (semente 2026).

## Dados

- TSE, 1º e 2º turnos de 2026: Flávio 56.104.503 → 59.826.041; Lula 53.879.538 → 64.256.232; outros candidatos no 1º turno, 9.316.747.
- TSE, 1º e 2º turnos de 2002 a 2022 (votos dos dois finalistas e votos válidos do 1º turno), conferidos nas tabelas de resultado da Wikipédia.

## Fontes

- Tarcísio de Freitas, vídeo no X (25/10/2026), na versão do canal do Poder360 no YouTube.
- Poder360, "Tarcísio fez projeção errada do resultado da eleição; veja vídeo" (26/10/2026).
- TSE, resultados das eleições presidenciais de 2002 a 2026.
- Eurasia Group, via CNN Brasil (17/10/2026): chance de 25% para o Lula.
