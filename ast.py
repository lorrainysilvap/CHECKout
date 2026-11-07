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


class Dinheiro:
    def __init__(self, centavos, moeda, linha, coluna, linha_moeda, coluna_moeda):
        self.centavos, self.moeda = centavos, moeda
        self.linha, self.coluna = linha, coluna
        self.linha_moeda, self.coluna_moeda = linha_moeda, coluna_moeda

    def para_dict(self):
        return {"tipo": "Dinheiro", "centavos": self.centavos, "moeda": self.moeda,
                "pos": pos_dict(self.linha, self.coluna),
                "posMoeda": pos_dict(self.linha_moeda, self.coluna_moeda)}


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
        self.transporte, self.custo, self.duracao = transporte, custo, duracao
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        return {"tipo": "Trecho", "pos": pos_dict(self.linha, self.coluna),
                "origem": self.origem.para_dict(), "destino": self.destino.para_dict(),
                "transporte": self.transporte, "custo": self.custo.para_dict(),
                "duracao": self.duracao.para_dict()}


class Viagem:
    def __init__(self, nome, moeda, linha_moeda, coluna_moeda, orcamento,
                 cidades, trechos, linha, coluna):
        self.nome = nome
        self.moeda, self.linha_moeda, self.coluna_moeda = moeda, linha_moeda, coluna_moeda
        self.orcamento = orcamento
        self.cidades, self.trechos = cidades, trechos
        self.linha, self.coluna = linha, coluna

    def para_dict(self):
        return {"tipo": "Viagem", "nome": self.nome, "pos": pos_dict(self.linha, self.coluna),
                "moeda": {"codigo": self.moeda,
                          "pos": pos_dict(self.linha_moeda, self.coluna_moeda)},
                "orcamento": self.orcamento.para_dict(),
                "cidades": [c.para_dict() for c in self.cidades],
                "trechos": [t.para_dict() for t in self.trechos]}
