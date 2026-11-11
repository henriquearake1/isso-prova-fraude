# #2 · A Lei de Benford nas notas do cotão

Em 09/11/2026, o Metrópoles noticiou que uma deputada que perdeu a eleição gastou R$ 137 mil da cota parlamentar (o "cotão") em outubro, com divulgação. Este código baixa as notas que a Câmara reembolsou em 2026 e aplica a elas o teste do primeiro dígito, a Lei de Newcomb-Benford, um dos testes que auditores usam para escolher onde procurar fraude.

## A lei

Em valores e contagens que surgem naturalmente, sem teto, piso ou preço tabelado, e que se espalham por várias ordens de grandeza (das dezenas aos milhares), uns 30% começam com 1 e menos de 5% com 9. A chance de cada primeiro dígito *d* é log10(1 + 1/*d*): 30,1% · 17,6% · 12,5% · 9,7% · 7,9% · 6,7% · 5,8% · 5,1% · 4,6%.

Uma forma de ver o porquê: uma aplicação de R$ 100 rendendo 10% ao ano leva 24 anos para chegar a R$ 1.000. Para ir de 100 a 200 ela precisa dobrar, e passa 7,3 anos começando com 1; para ir de 900 a 1.000 basta crescer 11%, e ela passa 1,1 ano começando com 9. São 30,1% e 4,6% do tempo.

## Como rodar

1. Baixe o arquivo oficial da Câmara: <https://www.camara.leg.br/cotas/Ano-2026.csv.zip>
2. `python benford_cotao.py Ano-2026.csv.zip`

Precisa de Python 3 com `numpy` e `pandas`. Roda em segundos e grava `resultado_cotao.json`.

Arquivo usado no vídeo: atualizado pela Câmara em 10/11/2026, às 3h35 (Brasília), com 123.573 notas de janeiro a 10 de novembro (SHA-256 `628e852cd6b61a7e3cba57eb7526efff049251c642a9e69f072762a717ab97af`). A Câmara atualiza o arquivo todo dia e os deputados têm até 90 dias para pedir reembolso, então setembro, outubro e novembro ainda vão crescer e os números mudam um pouco a cada download.

## Regras do teste

- Valor da nota (`vlrDocumento`); ficam de fora as notas abaixo de R$ 10 (1.712) e as devoluções (10).
- Medidas: qui-quadrado e desvio absoluto médio (MAD). Com dezenas de milhares de notas, o qui-quadrado reprova qualquer diferença mínima; a referência é o MAD, com as faixas de Nigrini (2012) para o 1º dígito: até 0,006 conformidade próxima; até 0,012 aceitável; até 0,015 marginal; acima, não conformidade.
- Por deputado: cada um tem poucas centenas de notas, e o MAD de amostras pequenas é alto por acaso. O MAD de cada deputado é comparado com o percentil 99 de 2.000 amostras do mesmo tamanho sorteadas da própria Lei de Benford.

## O que o código mostra

| Conjunto | Notas | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | MAD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Lei de Benford (%) | | 30,1 | 17,6 | 12,5 | 9,7 | 7,9 | 6,7 | 5,8 | 5,1 | 4,6 | |
| Base inteira | 121.851 | 28,0 | **28,5** | 15,6 | 8,7 | 6,7 | 4,2 | 2,9 | 3,1 | 2,5 | 0,0309 |
| Combustíveis | 58.375 | 26,1 | **41,0** | 17,8 | 7,5 | 4,0 | 1,0 | 0,8 | 0,8 | 0,9 | 0,0638 |
| Sem combustíveis | 63.476 | 29,7 | 16,9 | 13,5 | 9,7 | 9,1 | 7,2 | 4,7 | 5,1 | 4,1 | 0,0060 |

- **Combustível:** 40,6% das notas ficam entre R$ 200 e R$ 299,99 (mediana R$ 246,13). Com a gasolina perto de R$ 6,50 o litro (ANP), é o preço de um tanque. Número com tamanho típico não segue Benford.
- **Sem combustível:** as 63.476 notas restantes ficam no limite entre a conformidade próxima e a aceitável de Nigrini. Cada categoria, sozinha, foge da lei (táxi, hospedagem, aluguel de carro têm preços típicos); é a mistura de categorias que se aproxima dela.
- **Divulgação da atividade parlamentar:** 48,6% das 8.961 notas são múltiplos exatos de R$ 1.000 (contratos mensais de valor fechado).
- **Por deputado (84 com 200 notas ou mais, sem combustível):** 78 ficam acima do que o acaso explicaria. Os primeiros da lista repetem a mesma despesa: no primeiro, 69% das 239 notas começam com 9 porque 161 delas são corridas de táxi de R$ 88 a R$ 99; nos dois seguintes, pedágios de rodovia com tarifa entre R$ 10 e R$ 19. O teste aponta onde olhar; quem diz se a despesa existiu é o comprovante.
- **Os casos do noticiário:** Lêda Borges teve R$ 137.450 de divulgação reembolsados em outubro (R$ 120.450 de 55.000 revistas a R$ 2,19; R$ 12.000; R$ 5.000), contra R$ 20.500 por mês de janeiro a maio. Antônia Lúcia, R$ 103.000 em outubro, numa nota só. O teste não julga uma nota isolada.

## Quando o teste engana: as urnas

A pasta [`urnas`](urnas) tem a simulação citada no vídeo. Uma seção eleitoral tem perto de 255 votos válidos, e um candidato com metade deles fica entre 100 e 199 na maioria das seções; por isso 60,8% das seções do Lula no 2º turno de 2026 começam com 1. O código sorteia 10.000 eleições sem nenhuma fraude, com o tamanho real de cada uma das 499.205 seções (boletins de urna do TSE) e a votação de cada município, e aplica o teste a cada uma: ele acusa fraude em todas, para os dois candidatos. Acusa também mil eleições fraudadas de propósito, com o mesmo resultado: o teste não separa uma da outra.

`python urnas/benford_monte_carlo.py` (precisa de `numpy` e `scipy`; uns 10 minutos). Com `--n 1000`, roda em um minuto.

## Arquivos

| Arquivo | O que é |
|---|---|
| `benford_cotao.py` | O teste nas notas da cota parlamentar |
| `resultado_cotao.json` | Resultado completo: por categoria, por deputado (os dez primeiros) e as notas dos casos do noticiário |
| `saida.txt` | O resumo que o código imprime |
| `urnas/benford_monte_carlo.py` | A simulação das 10.000 eleições |
| `urnas/secoes_2t_2026_resumo.txt` | Tamanho de cada seção do 2º turno de 2026 e votação dos municípios, resumidos dos boletins de urna do TSE |
| `urnas/resultado_monte_carlo.json`, `urnas/saida.txt` | Resultado da simulação |

## Fontes

- Câmara dos Deputados, dados abertos da cota parlamentar (Ano-2026.csv.zip)
- Metrópoles, coluna Tacio Lorran, "Após perder eleição, deputada gasta R$ 137 mil do 'cotão' com autopromoção" (09/11/2026)
- TSE, boletins de urna do 2º turno de 2026
- S. Newcomb, "Note on the Frequency of Use of the Different Digits in Natural Numbers", American Journal of Mathematics 4 (1881)
- F. Benford, "The Law of Anomalous Numbers", Proceedings of the American Philosophical Society 78 (1938)
- M. Nigrini, Benford's Law: Applications for Forensic Accounting, Auditing, and Fraud Detection, Wiley (2012); "I've Got Your Number", Journal of Accountancy (maio de 1999)
- ANP, Síntese Semanal de Preços 43/2026
