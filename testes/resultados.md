# Resultados da suíte de testes da CHECKout

Execução: 2026-11-15 20:37 · Python 3.11.9 · Windows

## Tabela 1 — Resumo por grupo

| Grupo | Casos | Conformes | Rejeitados | Escapes | Falsos positivos | Fase correta | Posição correta |
|---|---:|---:|---:|---:|---:|---:|---:|
| Válidos (controle) | 10 | 10 | 0 | 0 | 0 | 10/10 | 10/10 |
| Válido com aviso (controle) | 1 | 1 | 0 | 0 | 0 | 1/1 | 1/1 |
| Erro léxico | 13 | 13 | 13 | 0 | 0 | 13/13 | 13/13 |
| Erro sintático | 11 | 11 | 11 | 0 | 0 | 11/11 | 11/11 |
| Erro semântico | 20 | 20 | 20 | 0 | 0 | 20/20 | 20/20 |
| **Total** | **55** | **55** | **44** | **0** | **0** | **55/55** | **55/55** |

## Tabela 2 — Métricas de detecção

| Métrica | Valor |
|---|---:|
| Programas com erro proposital | 44 |
| Programas de controle (válidos) | 11 |
| Taxa de detecção (erros rejeitados / com erro) | 44/44 (100.0%) |
| Diagnóstico e posição exatos | 44/44 (100.0%) |
| Escapes (erro aceito como válido) | 0 |
| Falsos positivos (controle rejeitado) | 0/11 |
| Tempo total da suíte | 44.2 ms |
| Tempo médio por caso | 0.80 ms |

## Tabela 3 — Regras semânticas exercitadas

| Regra | Casos que a disparam | Todos conformes? |
|---|---|---|
| R1 | S1, S2 | sim |
| R2 | S3 | sim |
| R3 | S9 | sim |
| R4 | S4, S9 | sim |
| R5 | S10, S11 | sim |
| R6 | S11 | sim |
| R7 | S7, S8 | sim |
| R8 | S5, S12, S19, S20 | sim |
| R9 | S6 | sim |
| R10 | W1, S4, S10 | sim |
| R11 | S13, S14, S15, S16 | sim |
| R12 | S17, S18 | sim |

## Critérios de aceite adicionais (Seção 6.3)

- ✔ Léxico: V1 produz 48 tokens, EOF em 19:1 — 48 tokens, último EOF em 19:1
- ✔ Sintático: checkout --ast de V1 igual à AST da Seção 4.1 — idêntica à Seção 4.1

## Tabela 4 — Resultado caso a caso

| ID | Alteração | Fase esperada | Fase obtida | Posição esperada | Posição obtida | Resultado |
|---|---|---|---|---|---|---|
| V1 | nenhuma alteração | - | - | - | - | conforme |
| V2 | nome "Europa // 2027" | - | - | - | - | conforme |
| V3 | nome "Férias \"Europa\"" | - | - | - | - | conforme |
| V4 | // fim após o último }, sem quebra de linha final | - | - | - | - | conforme |
| V5 | trecho movido para entre as duas cidades | - | - | - | - | conforme |
| V6 | datas trocadas para 2028-02-29 a 2028-03-04 (ano bissexto) | - | - | - | - | conforme |
| V7 | quebras de linha \r\n e custo 45,50 na linha 15 | léxico | léxico | 15:13 | 15:13 | conforme |
| V8 | custo 2 * 45.50 EUR + 3.00 EUR e orçamento 2 * 1000.00 EUR + 500.00 EUR (precedência) | - | - | - | - | conforme |
| V9 | custo 2 * (45.50 EUR + 3.00 EUR) (parênteses) | - | - | - | - | conforme |
| V10 | dois blocos se/senao: um verdadeiro e um falso | - | - | - | - | conforme |
| V11 | se subtotal >= 1.50 * 30.00 EUR + 0.50 EUR (precedência na condição) e se sem senao falso | - | - | - | - | conforme |
| W1 | trecho removido | - | - | - | - | conforme |
| L1 | cidade "Lisboa {  (aspas não fechadas) | léxico | léxico | 5:10 | 5:10 | conforme |
| L2 | arquivo contendo só viagem "Europa | léxico | léxico | 1:8 | 1:8 | conforme |
| L3 | custo 45,50 | léxico | léxico | 15:13 | 15:13 | conforme |
| L4 | chegada 2027-6-10 | léxico | léxico | 6:13 | 6:13 | conforme |
| L5 | orcamento 2500.0 | léxico | léxico | 4:13 | 4:13 | conforme |
| L6 | custo .50 | léxico | léxico | 15:11 | 15:11 | conforme |
| L7 | custo 045.50 | léxico | léxico | 15:11 | 15:11 | conforme |
| L8 | custo -45.50 | léxico | léxico | 15:11 | 15:11 | conforme |
| L9 | custo 45.234 | léxico | léxico | 15:11 | 15:11 | conforme |
| L10 | duracao 2h5 | léxico | léxico | 16:13 | 16:13 | conforme |
| L11 | nome "Europa\n2027" | léxico | léxico | 2:15 | 2:15 | conforme |
| L12 | custo 45.50 EUR - 5.00 EUR (subtração não existe) | léxico | léxico | 15:21 | 15:21 | conforme |
| P1 | sem ; após moeda EUR | sintático | sintático | 4:3 | 4:3 | conforme |
| P2 | sem o } final | sintático | sintático | 18:1 | 18:1 | conforme |
| P3 | programa com moeda e orçamento, sem cidade | sintático | sintático | 4:1 | 4:1 | conforme |
| P4 | orcamento declarado antes de moeda | sintático | sintático | 2:3 | 2:3 | conforme |
| P5 | transporte trecho; | sintático | sintático | 14:16 | 14:16 | conforme |
| P6 | duracao "2h45"; (forma antiga) | sintático | sintático | 16:13 | 16:13 | conforme |
| P7 | em Lisboa, saida antes de chegada | sintático | sintático | 6:5 | 6:5 | conforme |
| P8 | custo 2 *  | sintático | sintático | 15:15 | 15:15 | conforme |
| P9 | se sem { antes de imprimir | sintático | sintático | 18:25 | 18:25 | conforme |
| P10 | se sem comparador | sintático | sintático | 18:12 | 18:12 | conforme |
| P11 | custo (45.50 EUR + 3.00 EUR | sintático | sintático | 15:32 | 15:32 | conforme |
| S1 | chegada 2027-02-30 | semântico | semântico | 6:13 | 6:13 | conforme |
| S2 | chegada 2027-02-29 (2027 não é bissexto) | semântico | semântico | 6:13 | 6:13 | conforme |
| S3 | saída de Lisboa 2027-06-09 | semântico | semântico | 7:11 | 7:11 | conforme |
| S4 | trecho para "Porto" | semântico | semântico | 13:22 | 13:22 | conforme |
| S5 | custo em USD | semântico | semântico | 15:17 | 15:17 | conforme |
| S6 | orçamento 40.00 EUR | semântico | semântico | 4:13 | 4:13 | conforme |
| S7 | duração 2h75 | semântico | semântico | 16:13 | 16:13 | conforme |
| S8 | duração 0h00 | semântico | semântico | 16:13 | 16:13 | conforme |
| S9 | segunda cidade renomeada para "Lisboa" | semântico | semântico | 9:10 | 9:10 | conforme |
| S10 | trecho invertido para "Madri" -> "Lisboa" | semântico | semântico | 13:21 | 13:21 | conforme |
| S11 | chegada a Madri 2027-06-12 | semântico | semântico | 10:13 | 10:13 | conforme |
| S12 | moeda Eur em todo o arquivo | semântico | semântico | 3:9 | 3:9 | conforme |
| S13 | custo 45.50 EUR * 2.00 EUR | semântico | semântico | 15:21 | 15:21 | conforme |
| S14 | custo 45.50 EUR + 2 | semântico | semântico | 15:21 | 15:21 | conforme |
| S15 | orcamento 2500.00 (sem moeda) | semântico | semântico | 4:13 | 4:13 | conforme |
| S16 | se saldo < 100 (dinheiro com número) | semântico | semântico | 18:12 | 18:12 | conforme |
| S17 | se total < 100.00 EUR (nome não declarado) | semântico | semântico | 18:6 | 18:6 | conforme |
| S18 | custo saldo (nome fora do se) | semântico | semântico | 15:11 | 15:11 | conforme |
| S19 | se saldo < 100.00 USD | semântico | semântico | 18:21 | 18:21 | conforme |
| S20 | custo 2 * 45.50 EUR + 3.00 USD | semântico | semântico | 15:32 | 15:32 | conforme |
