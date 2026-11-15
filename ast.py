"""Nós da AST da CHECKout.

Todo nó guarda a posição (linha, coluna) do token que o originou.
"""


def pos_dict(linha, coluna):
    return {"linha": linha, "coluna": coluna}


class Data:
    def __init__(self, valor, linha, coluna):
        self.valor, self.linha, self.coluna = valor, linha, coluna

    def para_dict(self):
        return {"tipo": "Data", "valor": self.valor, "pos": pos_dict(self.linha, self.coluna)}


# ---------------------------------------------------------------------------
# Expressões (requisito 4): folhas Dinheiro, Numero e Nome; nó interno Binaria.
# Precedência: '*' (termo) liga mais forte que '+' (expressão); '(' ')' agrupa.
# ---------------------------------------------------------------------------

class Dinheiro:
    """Literal monetário: número seguido de código de moeda (45.50 EUR)."""

    def __init__(self, centavos, moeda, linha, coluna, linha_moeda, coluna_moeda):
        self.centavos, self.moeda = centavos, moeda
        self.linha, self.coluna = linha, coluna
        self.linha_moeda, self.coluna_moeda = linha_moeda, coluna_moeda

    def para_dict(self):
        return {"tipo": "Dinheiro", "centavos": self.centavos, "moeda": self.moeda,
                "pos": pos_dict(self.linha, self.coluna),
                "posMoeda": pos_dict(self.linha_moeda, self.coluna_moeda)}


class Numero:
    """Número puro, sem moeda (quantidade ou fator: 2, 1.50)."""

    def __init__(self, centavos, texto, linha, coluna):
        self.centavos, self.texto = centavos, texto   # 1.50 -> 150 (escala de centésimos)
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        return {"tipo": "Numero", "valor": self.texto, "pos": pos_dict(self.linha, self.coluna)}


class Nome:
    """Uso de um nome pré-definido (saldo, subtotal) dentro de uma condição."""

    def __init__(self, nome, linha, coluna):
        self.nome, self.linha, self.coluna = nome, linha, coluna

    def para_dict(self):
        return {"tipo": "Nome", "nome": self.nome, "pos": pos_dict(self.linha, self.coluna)}


class Binaria:
    """Operação esq <op> dir. A posição é a do operador."""

    def __init__(self, op, esq, dir_, linha, coluna):
        self.op, self.esq, self.dir = op, esq, dir_
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        return {"tipo": "Binaria", "op": self.op, "pos": pos_dict(self.linha, self.coluna),
                "esq": self.esq.para_dict(), "dir": self.dir.para_dict()}


def inicio(expr):
    """Posição do primeiro token de uma expressão (a folha mais à esquerda)."""
    while isinstance(expr, Binaria):
        expr = expr.esq
    return expr.linha, expr.coluna


def folhas(expr):
    """Todas as folhas de uma expressão, da esquerda para a direita."""
    if isinstance(expr, Binaria):
        return folhas(expr.esq) + folhas(expr.dir)
    return [expr]


# ---------------------------------------------------------------------------

class Duracao:
    def __init__(self, texto, horas, minutos, linha, coluna):
        self.texto = texto
        self.horas, self.min_parte = horas, minutos   # min_parte = os dois dígitos após h
        self.minutos = horas * 60 + minutos            # total em minutos
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        return {"tipo": "Duracao", "texto": self.texto, "minutos": self.minutos,
                "pos": pos_dict(self.linha, self.coluna)}


class Referencia:
    def __init__(self, nome, linha, coluna):
        self.nome, self.linha, self.coluna = nome, linha, coluna
        self.cidade = None  # preenchido pela análise semântica

    def para_dict(self):
        return {"nome": self.nome, "pos": pos_dict(self.linha, self.coluna)}


class Cidade:
    def __init__(self, nome, chegada, saida, linha, coluna):
        self.nome, self.chegada, self.saida = nome, chegada, saida
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        return {"tipo": "Cidade", "nome": self.nome, "pos": pos_dict(self.linha, self.coluna),
                "chegada": self.chegada.para_dict(), "saida": self.saida.para_dict()}


class Trecho:
    def __init__(self, origem, destino, transporte, custo, duracao, linha, coluna):
        self.origem, self.destino = origem, destino
        self.transporte, self.custo, self.duracao = transporte, custo, duracao  # custo: expressão
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        return {"tipo": "Trecho", "pos": pos_dict(self.linha, self.coluna),
                "origem": self.origem.para_dict(), "destino": self.destino.para_dict(),
                "transporte": self.transporte, "custo": self.custo.para_dict(),
                "duracao": self.duracao.para_dict()}


# ---------------------------------------------------------------------------
# Estrutura de controle (requisito 5) e saída (requisito 7)
# ---------------------------------------------------------------------------

class Imprimir:
    def __init__(self, texto, linha, coluna):
        self.texto, self.linha, self.coluna = texto, linha, coluna

    def para_dict(self):
        return {"tipo": "Imprimir", "texto": self.texto, "pos": pos_dict(self.linha, self.coluna)}


class Condicional:
    """se <expr> <comparador> <expr> { imprimir ... } [senao { imprimir ... }]"""

    def __init__(self, esq, op, dir_, linha_op, coluna_op, entao, senao, linha, coluna):
        self.esq, self.op, self.dir = esq, op, dir_
        self.linha_op, self.coluna_op = linha_op, coluna_op
        self.entao, self.senao = entao, senao
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        return {"tipo": "Se", "pos": pos_dict(self.linha, self.coluna),
                "condicao": {"op": self.op, "pos": pos_dict(self.linha_op, self.coluna_op),
                             "esq": self.esq.para_dict(), "dir": self.dir.para_dict()},
                "entao": [i.para_dict() for i in self.entao],
                "senao": [i.para_dict() for i in self.senao]}


class Viagem:
    def __init__(self, nome, moeda, linha_moeda, coluna_moeda, orcamento,
                 cidades, trechos, linha, coluna, condicionais=None):
        self.nome = nome
        self.moeda, self.linha_moeda, self.coluna_moeda = moeda, linha_moeda, coluna_moeda
        self.orcamento = orcamento   # expressão
        self.cidades, self.trechos = cidades, trechos
        self.condicionais = condicionais or []
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        d = {"tipo": "Viagem", "nome": self.nome, "pos": pos_dict(self.linha, self.coluna),
             "moeda": {"codigo": self.moeda,
                       "pos": pos_dict(self.linha_moeda, self.coluna_moeda)},
             "orcamento": self.orcamento.para_dict(),
             "cidades": [c.para_dict() for c in self.cidades],
             "trechos": [t.para_dict() for t in self.trechos]}
        if self.condicionais:   # só aparece quando há 'se' (mantém a AST da Seção 4.1)
            d["condicionais"] = [c.para_dict() for c in self.condicionais]
        return d
