"""Diagnósticos da CHECKout (Seção 5.5 do artigo).

Formato: Erro <fase> na linha L, coluna C: <descrição>
         Aviso na linha L, coluna C: <descrição>
"""


class Diagnostico:
    def __init__(self, tipo, fase, linha, coluna, mensagem):
        self.tipo = tipo          # "erro" ou "aviso"
        self.fase = fase          # "léxico", "sintático" ou "semântico"
        self.linha = linha
        self.coluna = coluna
        self.mensagem = mensagem

    def __str__(self):
        if self.tipo == "aviso":
            return f"Aviso na linha {self.linha}, coluna {self.coluna}: {self.mensagem}"
        return (f"Erro {self.fase} na linha {self.linha}, "
                f"coluna {self.coluna}: {self.mensagem}")


class ErroCompilacao(Exception):
    """Interrompe a análise léxica ou sintática no primeiro problema."""

    def __init__(self, diagnostico):
        super().__init__(str(diagnostico))
        self.diagnostico = diagnostico


def erro_lexico(linha, coluna, msg):
    return ErroCompilacao(Diagnostico("erro", "léxico", linha, coluna, msg))


def erro_sintatico(linha, coluna, msg):
    return ErroCompilacao(Diagnostico("erro", "sintático", linha, coluna, msg))
