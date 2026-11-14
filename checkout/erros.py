"""Diagnósticos da CHECKout (Seção 5.5 do artigo).

Formato: Erro <fase> no arquivo <arquivo>, linha L, coluna C: <descrição>
         Aviso no arquivo <arquivo>, linha L, coluna C: <descrição>

Sem nome de arquivo (uso interno), cai no formato curto "na linha L, coluna C".
"""


class Diagnostico:
    def __init__(self, tipo, fase, linha, coluna, mensagem, arquivo=None):
        self.tipo = tipo          # "erro" ou "aviso"
        self.fase = fase          # "léxico", "sintático" ou "semântico"
        self.linha = linha
        self.coluna = coluna
        self.mensagem = mensagem
        self.arquivo = arquivo    # preenchido por compilador.executar

    def _onde(self):
        if self.arquivo:
            return f"no arquivo {self.arquivo}, linha {self.linha}, coluna {self.coluna}"
        return f"na linha {self.linha}, coluna {self.coluna}"

    def __str__(self):
        if self.tipo == "aviso":
            return f"Aviso {self._onde()}: {self.mensagem}"
        return f"Erro {self.fase} {self._onde()}: {self.mensagem}"


class ErroCompilacao(Exception):
    """Interrompe a análise léxica ou sintática no primeiro problema."""

    def __init__(self, diagnostico):
        super().__init__(str(diagnostico))
        self.diagnostico = diagnostico


def erro_lexico(linha, coluna, msg):
    return ErroCompilacao(Diagnostico("erro", "léxico", linha, coluna, msg))


def erro_sintatico(linha, coluna, msg):
    return ErroCompilacao(Diagnostico("erro", "sintático", linha, coluna, msg))
