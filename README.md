# CHECKout

DSL para roteiros de viagem com validação léxica, sintática e semântica.
Implementação de referência em Python 3 (somente biblioteca padrão, sem dependências).

## Requisitos

Python 3.8 ou superior.

## Como usar

```bash
python checkout.py exemplos/europa.checkout           # valida e imprime a saída ou os diagnósticos
python checkout.py --ast exemplos/europa.checkout     # imprime a AST em JSON (Seção 4.1)
python checkout.py --tokens exemplos/europa.checkout  # imprime os tokens (léxico)
```

Código de saída: `0` programa válido, `1` erro léxico, sintático ou semântico, `2` erro de uso/arquivo.

## Como reproduzir os testes

```bash
python testes/rodar_testes.py
```

Roda os 38 casos da matriz da Seção 6.1 do artigo num único comando, além dos
critérios de aceite da Seção 6.3 (48 tokens em V1 e AST idêntica à da Seção 4.1).
Gera `testes/resultados.md` (tabelas para a seção de Avaliação) e
`testes/resultados.csv` (resultado caso a caso).

As saídas esperadas (`testes/casos/*.esperado`) foram escritas a partir da matriz
do artigo, não copiadas da saída do programa.

## Estrutura

```
checkout.py              interface de linha de comando
checkout/
  lexico.py              analisador léxico (Seção 3.1 e 5.1)
  sintatico.py           analisador sintático descendente recursivo (3.2 e 5.2)
  ast.py                 nós da AST com posição (4.1)
  semantico.py           regras R1 a R10 em duas passagens (3.4 e 5.3)
  compilador.py          junta as fases e formata a saída (4.2 e 5.5)
  erros.py               formato dos diagnósticos
exemplos/                três programas de demonstração (dois válidos, um rejeitado)
testes/
  casos/                 38 pares .checkout / .esperado
  casos.csv              descrição de cada caso
  V1.ast.esperado.json   AST da Seção 4.1
  rodar_testes.py        suíte de regressão
```

## Decisões de implementação não fixadas pelo artigo

- **Saída com avisos:** um programa com avisos e sem erros imprime os avisos e,
  em seguida, a saída normal (caso W1: subtotal 0.00, saldo igual ao orçamento).
- **Código das regras nas mensagens:** as mensagens semânticas começam com o código
  da regra (`R1:`, `R8:` ...), como na matriz de testes.
- **Cascata de erros:** cidades com data inexistente (R1) ou saída antes da chegada (R2)
  ficam fora de R5, R6 e R10; uma cidade com nome repetido (R3) não entra na tabela de
  símbolos. Se houver erro de moeda (R8), não se calcula subtotal, saldo nem R9.
- **Moeda malformada (R8):** só a moeda da viagem é checada pela forma; orçamento e
  custos são comparados com ela.
- **R6:** cada cidade é comparada com a de maior saída entre as anteriores (na ordem de
  chegada), o que também detecta sobreposição com cidades não adjacentes.
- **R10:** o trecho precisa ir da cidade anterior para a seguinte (direção importa).
- **V6:** as datas usadas foram Lisboa 2028-02-29 a 2028-03-02 e Madri 2028-03-02 a 2028-03-04.
