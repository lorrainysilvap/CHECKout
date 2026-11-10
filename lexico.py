"""Analisador léxico da CHECKout (Seções 3.1 e 5.1 do artigo).

Recebe o texto do arquivo e devolve uma lista de tokens terminada por EOF.
Para no primeiro erro léxico.
"""
from .erros import erro_lexico

PALAVRAS_CHAVE = {
    "viagem", "moeda", "orcamento", "cidade", "chegada", "saida",
    "trecho", "transporte", "custo", "duracao",
}

# Categorias de token
PALAVRA_CHAVE = "PALAVRA_CHAVE"
IDENTIFICADOR = "IDENTIFICADOR"
TEXTO = "TEXTO"
NUMERO = "NUMERO"
DATA = "DATA"
DURACAO = "DURACAO"
SIMBOLO = "SIMBOLO"
EOF = "EOF"


class Token:
    def __init__(self, categoria, lexema, linha, coluna, valor=None):
        self.categoria = categoria
        self.lexema = lexema      # texto como aparece no arquivo
        self.linha = linha
        self.coluna = coluna
        self.valor = valor        # valor interpretado (texto sem aspas, centavos, minutos...)

    def __repr__(self):
        return f"{self.linha}:{self.coluna}\t{self.categoria}\t{self.lexema}"


def _letra_ascii(c):
    return ("A" <= c <= "Z") or ("a" <= c <= "z")


def _digito(c):
    return "0" <= c <= "9"


class Lexico:
    def __init__(self, fonte):
        if fonte.startswith("﻿"):          # BOM do UTF-8
            fonte = fonte[1:]
        self.fonte = fonte
        self.i = 0
        self.linha = 1
        self.coluna = 1

    # ---------- utilitários de leitura ----------
    def _atual(self, desloc=0):
        j = self.i + desloc
        return self.fonte[j] if j < len(self.fonte) else ""

    def _avancar(self):
        """Consome um caractere e atualiza linha/coluna.
        \\r\\n conta como uma única quebra; coluna conta caracteres."""
        c = self.fonte[self.i]
        self.i += 1
        if c == "\r":
            if self._atual() == "\n":
                self.i += 1
            self.linha += 1
            self.coluna = 1
        elif c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    # ---------- análise ----------
    def tokens(self):
        lista = []
        while True:
            self._pular_espacos_e_comentarios()
            if self.i >= len(self.fonte):
                lista.append(Token(EOF, "", self.linha, self.coluna))
                return lista
            lista.append(self._proximo())

    def _pular_espacos_e_comentarios(self):
        while self.i < len(self.fonte):
            c = self._atual()
            if c in " \t\r\n":
                self._avancar()
            elif c == "/" and self._atual(1) == "/":
                while self.i < len(self.fonte) and self._atual() not in "\r\n":
                    self._avancar()
            else:
                return

    def _proximo(self):
        lin, col = self.linha, self.coluna
        c = self._atual()

        if c == '"':
            return self._texto(lin, col)
        if _letra_ascii(c):
            return self._palavra(lin, col)
        if _digito(c):
            return self._numerico(lin, col)
        if c in "{};":
            self._avancar()
            return Token(SIMBOLO, c, lin, col)
        if c == "-" and self._atual(1) == ">":
            self._avancar()
            self._avancar()
            return Token(SIMBOLO, "->", lin, col)
        raise erro_lexico(lin, col, f"caractere inesperado '{c}'")

    def _texto(self, lin, col):
        ini = self.i
        self._avancar()  # aspas de abertura
        conteudo = []
        while True:
            c = self._atual()
            if c == "" or c in "\r\n":
                raise erro_lexico(lin, col, "texto iniciado aqui não foi fechado com aspas")
            if c == '"':
                self._avancar()
                break
            if c == "\\":
                lin_esc, col_esc = self.linha, self.coluna
                prox = self._atual(1)
                if prox == "" or prox in "\r\n":
                    raise erro_lexico(lin, col, "texto iniciado aqui não foi fechado com aspas")
                if prox not in '"\\':
                    raise erro_lexico(lin_esc, col_esc, "sequência de escape inválida")
                self._avancar()
                conteudo.append(self._avancar())
                continue
            conteudo.append(self._avancar())
        lexema = self.fonte[ini:self.i]
        return Token(TEXTO, lexema, lin, col, "".join(conteudo))

    def _palavra(self, lin, col):
        ini = self.i
        while _letra_ascii(self._atual()) or _digito(self._atual()) or self._atual() == "_":
            self._avancar()
        lexema = self.fonte[ini:self.i]
        if lexema in PALAVRAS_CHAVE:
            return Token(PALAVRA_CHAVE, lexema, lin, col)
        return Token(IDENTIFICADOR, lexema, lin, col, lexema)

    def _ler_digitos(self):
        ini = self.i
        while _digito(self._atual()):
            self._avancar()
        return self.fonte[ini:self.i]

    def _numerico(self, lin, col):
        """Números, datas e durações começam com dígito.
        Lê todos os dígitos e decide pelo caractere seguinte (Seção 3.1)."""
        ini = self.i
        digitos = self._ler_digitos()
        seguinte = self._atual()

        if seguinte == "-":                      # data AAAA-MM-DD
            ok = len(digitos) == 4
            if ok:
                self._avancar()
                mes = self._ler_digitos()
                ok = len(mes) == 2 and self._atual() == "-"
            if ok:
                self._avancar()
                dia = self._ler_digitos()
                ok = len(dia) == 2
            if not ok:
                raise erro_lexico(lin, col, "data malformada; use o formato AAAA-MM-DD")
            lexema = self.fonte[ini:self.i]
            return Token(DATA, lexema, lin, col, lexema)

        if seguinte == "h":                      # duração HhMM
            self._avancar()
            minutos = self._ler_digitos()
            if len(minutos) != 2 or _letra_ascii(self._atual()) or self._atual() == "_":
                raise erro_lexico(lin, col, "duração malformada")
            lexema = self.fonte[ini:self.i]
            return Token(DURACAO, lexema, lin, col, (int(digitos), int(minutos)))

        # número: inteiro sem zero à esquerda, com ou sem exatamente duas casas
        if len(digitos) > 1 and digitos[0] == "0":
            raise erro_lexico(lin, col, "número com zero à esquerda")
        centavos = int(digitos) * 100
        if seguinte == ".":
            self._avancar()
            casas = self._ler_digitos()
            if len(casas) != 2:
                raise erro_lexico(lin, col, "número decimal deve ter exatamente duas casas")
            centavos += int(casas)
        lexema = self.fonte[ini:self.i]
        return Token(NUMERO, lexema, lin, col, centavos)


def analisar_lexico(fonte):
    return Lexico(fonte).tokens()
