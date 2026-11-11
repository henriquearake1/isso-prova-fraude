# Isso prova fraude?

Série de vídeos de [@henriquearake](https://www.instagram.com/henriquearake/) no Instagram: um método de investigação de fraude por episódio, o que ele prova e o que não prova.

Aqui ficam o código e os dados de cada episódio, para qualquer pessoa refazer as contas.

| Episódio | Pasta |
|---|---|
| #1 · A simulação de Monte Carlo do Tarcísio | [`01-monte-carlo-tarcisio`](01-monte-carlo-tarcisio) |
| #2 · A Lei de Benford nas notas do cotão | [`02-benford-cotao`](02-benford-cotao) |

## Como rodar

É preciso ter Python 3 e os pacotes `numpy`, `pandas` e `scipy`:

```
pip install numpy pandas scipy
python 01-monte-carlo-tarcisio/tarcisio_monte_carlo.py
python 02-benford-cotao/benford_cotao.py Ano-2026.csv.zip
```

O arquivo `Ano-2026.csv.zip` é o da Câmara dos Deputados (instruções em [`02-benford-cotao`](02-benford-cotao)).

Henrique Arake · doutor em análise econômica do direito
