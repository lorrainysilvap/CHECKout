# CHECKout

DSL para roteiros de viagem com validação léxica, sintática e semântica.
Implementação de referência em Python 3 (somente biblioteca padrão, sem dependências).

## Requisitos

Python 3.8 ou superior.

## Como usar

```bash
python checkout.py exemplos/europa.checkout           # valida e imprime a saída ou os diagnósticos
python checkout.py --ast exemplos/europa.checkout     # imprime a AST em JSON
python checkout.py --tokens exemplos/europa.checkout  # imprime os tokens (léxico)
```

Código de saída: `0` programa válido, `1` erro léxico, sintático ou semântico, `2` erro de uso/arquivo.

Todo diagnóstico informa arquivo, linha e coluna:

```
Erro semântico no arquivo exemplos/rejeitado.checkout, linha 16, coluna 17: R8: moeda USD no custo difere da moeda da viagem (BRL)
```

## Exemplos

| Arquivo | O que mostra |
|---|---|
| `exemplos/europa.checkout` | roteiro mínimo válido (2 cidades, 1 trecho) |
| `exemplos/nordeste.checkout` | 3 cidades e 2 trechos, trechos intercalados com cidades |
| `exemplos/sul.checkout` | expressões com precedência e parênteses, e bloco `se`/`senao` |
| `exemplos/rejeitado.checkout` | programa sintaticamente correto e semanticamente inválido |

## A linguagem em resumo

```
viagem "Sul 2027" {
  moeda BRL;
  orcamento 2 * 400.00 BRL;
  cidade "Curitiba" { chegada 2027-07-01; saida 2027-07-04; }
  cidade "Florianopolis" { chegada 2027-07-04; saida 2027-07-08; }
  trecho "Curitiba" -> "Florianopolis" {
    transporte onibus;
    custo 2 * 110.00 BRL + 15.00 BRL;
    duracao 5h30;
  }
  se saldo < 200.00 BRL {
    imprimir "Sobrou pouco dinheiro";
  } senao {
    imprimir "Orcamento folgado";
  }
}
```

### Gramática (EBNF)

```
programa       = "viagem", texto, "{", moeda_decl, orcamento_decl,
                 cidade_decl, { declaracao }, "}" ;
declaracao     = cidade_decl | trecho_decl | se_decl ;
moeda_decl     = "moeda", identificador, ";" ;
orcamento_decl = "orcamento", expressao, ";" ;
cidade_decl    = "cidade", texto, "{", "chegada", data, ";", "saida", data, ";", "}" ;
trecho_decl    = "trecho", texto, "->", texto, "{",
                 "transporte", identificador, ";",
                 "custo", expressao, ";",
                 "duracao", duracao, ";", "}" ;

expressao      = termo, { "+", termo } ;               (* nível 1: soma *)
termo          = fator, { "*", fator } ;               (* nível 2: multiplicação *)
fator          = numero, [ identificador ]             (* 45.50 EUR = dinheiro; 2 = número *)
               | identificador                         (* saldo, subtotal *)
               | "(", expressao, ")" ;

se_decl        = "se", expressao, comparador, expressao, bloco, [ "senao", bloco ] ;
comparador     = "<" | ">" | "<=" | ">=" ;
bloco          = "{", { "imprimir", texto, ";" }, "}" ;
```

### Tokens

| Categoria | Exemplos |
|---|---|
| Palavra-chave | `viagem moeda orcamento cidade chegada saida trecho transporte custo duracao se senao imprimir` |
| Identificador | `EUR`, `trem`, `saldo` |
| Texto | `"Lisboa"` (aceita `\"` e `\\`) |
| Número | `2`, `45.50` (sem zero à esquerda; decimais com exatamente duas casas) |
| Data | `2027-06-10` |
| Duração | `2h45` |
| Símbolo | `{ } ; -> + * ( ) < > <= >=` |

### Regras semânticas

| Regra | Verifica |
|---|---|
| R1 | toda data existe no calendário |
| R2 | saída da cidade igual ou posterior à chegada |
| R3 | nomes de cidade não se repetem |
| R4 | trechos usam cidades declaradas, com origem diferente do destino |
| R5 | chegada ao destino igual ou posterior à saída da origem |
| R6 | permanências não se sobrepõem |
| R7 | minutos da duração entre 00 e 59, duração maior que zero |
| R8 | moeda com três letras maiúsculas; todo valor em dinheiro usa a moeda da viagem |
| R9 | soma dos custos não excede o orçamento |
| R10 | (aviso) cidades consecutivas no tempo ligadas por um trecho |
| R11 | tipos nas expressões: não se soma dinheiro com número, não se multiplica dinheiro por dinheiro, orçamento e custo resultam em dinheiro, comparação só entre valores do mesmo tipo |
| R12 | os nomes `saldo` e `subtotal` só existem dentro de `se`; outros nomes não são declarados |

## Como reproduzir os testes

```bash
python testes/rodar_testes.py
```

Roda os 55 casos de `testes/casos/` num único comando e 17 casos para expressões, `se`/`senao` e as regras R11 e R12, além dos critérios de aceite (48 tokens em V1 e AST).
Gera `testes/resultados.md` (tabelas para a seção de Avaliação) e
`testes/resultados.csv` (resultado caso a caso).

As saídas esperadas (`testes/casos/*.esperado`) foram escritas a partir da matriz
do artigo e da especificação das extensões, não copiadas da saída do programa.

## Estrutura

```
checkout.py              interface de linha de comando
checkout/
  lexico.py              analisador léxico 
  sintatico.py           analisador sintático descendente recursivo 
  ast.py                 nós da AST com posição
  semantico.py           regras R1 a R12 em duas passagens 
  compilador.py          junta as fases e formata a saída 
  erros.py               formato dos diagnósticos
exemplos/                quatro programas de demonstração (três válidos, um rejeitado)
testes/
  casos/                 55 pares .checkout / .esperado
  casos.csv              descrição de cada caso
  V1.ast.esperado.json   AST 
  rodar_testes.py        suíte de regressão
```