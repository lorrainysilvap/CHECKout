"""Analisador sintático descendente recursivo da CHECKout (Seções 3.2 e 5.2).

Uma função por não terminal da gramática EBNF. Cada função monta o nó da AST.
Para no primeiro erro, relatando o que esperava e o que encontrou.
"""
from . import ast
from .erros import erro_sintatico
from .lexico import (PALAVRA_CHAVE, IDENTIFICADOR, TEXTO, NUMERO, DATA, DURACAO,
                     SIMBOLO, EOF)

COMPARADORES = ("<", ">", "<=", ">=")


def descrever(tok):
    """Como o token encontrado aparece na mensagem de erro."""
    if tok.categoria == EOF:
        return "fim do arquivo"
    if tok.categoria == TEXTO:
        return "texto entre aspas"
    return f"'{tok.lexema}'"


class Sintatico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    # ---------- utilitários ----------
    @property
    def atual(self):
        return self.tokens[self.i]

    def _e(self, categoria, lexema=None):
        t = self.atual
        return t.categoria == categoria and (lexema is None or t.lexema == lexema)

    def _erro(self, esperado):
        t = self.atual
        return erro_sintatico(t.linha, t.coluna, f"esperado {esperado}, encontrado {descrever(t)}")

    def _consumir(self, categoria, lexema, esperado):
        if not self._e(categoria, lexema):
            raise self._erro(esperado)
        t = self.atual
        self.i += 1
        return t

    def _kw(self, palavra, esperado=None):
        return self._consumir(PALAVRA_CHAVE, palavra, esperado or f"'{palavra}'")

    def _sim(self, s, esperado=None):
        return self._consumir(SIMBOLO, s, esperado or f"'{s}'")

    def _ponto_e_virgula(self, apos):
        return self._sim(";", f"';' após a declaração de {apos}")

    # ---------- programa ----------
    # programa   = "viagem", texto, "{", moeda_decl, orcamento_decl,
    #              cidade_decl, { declaracao }, "}" ;
    # declaracao = cidade_decl | trecho_decl | se_decl ;
    def programa(self):
        kw = self._kw("viagem")
        nome = self._consumir(TEXTO, None, "nome da viagem entre aspas")
        self._sim("{")
        moeda_tok = self.moeda_decl()
        orcamento = self.orcamento_decl()
        cidades = [self.cidade_decl(obrigatoria=True)]
        trechos = []
        condicionais = []
        while True:
            if self._e(PALAVRA_CHAVE, "cidade"):
                cidades.append(self.cidade_decl())
            elif self._e(PALAVRA_CHAVE, "trecho"):
                trechos.append(self.trecho_decl())
            elif self._e(PALAVRA_CHAVE, "se"):
                condicionais.append(self.se_decl())
            elif self._e(SIMBOLO, "}"):
                self.i += 1
                break
            else:
                raise self._erro("'cidade', 'trecho', 'se' ou '}'")
        self._consumir(EOF, None, "fim do arquivo")
        return ast.Viagem(nome.valor, moeda_tok.valor, moeda_tok.linha, moeda_tok.coluna,
                          orcamento, cidades, trechos, kw.linha, kw.coluna, condicionais)

    # moeda_decl = "moeda", identificador, ";" ;
    def moeda_decl(self):
        self._kw("moeda", "declaração 'moeda'")
        codigo = self._consumir(IDENTIFICADOR, None, "código de moeda")
        self._ponto_e_virgula("moeda")
        return codigo

    # orcamento_decl = "orcamento", expressao, ";" ;
    def orcamento_decl(self):
        self._kw("orcamento", "declaração 'orcamento'")
        expr = self.expressao()
        self._ponto_e_virgula("orçamento")
        return expr

    # ---------- expressões (requisito 4: dois níveis de precedência) ----------
    # expressao = termo, { "+", termo } ;
    def expressao(self):
        esq = self.termo()
        while self._e(SIMBOLO, "+"):
            op = self.atual
            self.i += 1
            dir_ = self.termo()
            esq = ast.Binaria("+", esq, dir_, op.linha, op.coluna)
        return esq

    # termo = fator, { "*", fator } ;
    def termo(self):
        esq = self.fator()
        while self._e(SIMBOLO, "*"):
            op = self.atual
            self.i += 1
            dir_ = self.fator()
            esq = ast.Binaria("*", esq, dir_, op.linha, op.coluna)
        return esq

    # fator = numero, [ identificador ]      (com identificador: valor em dinheiro)
    #       | identificador                  (nome: saldo, subtotal)
    #       | "(", expressao, ")" ;
    def fator(self):
        t = self.atual
        if t.categoria == NUMERO:
            self.i += 1
            if self._e(IDENTIFICADOR):
                moeda = self.atual
                self.i += 1
                return ast.Dinheiro(t.valor, moeda.valor, t.linha, t.coluna,
                                    moeda.linha, moeda.coluna)
            return ast.Numero(t.valor, t.lexema, t.linha, t.coluna)
        if t.categoria == IDENTIFICADOR:
            self.i += 1
            return ast.Nome(t.valor, t.linha, t.coluna)
        if self._e(SIMBOLO, "("):
            self.i += 1
            expr = self.expressao()
            self._sim(")")
            return expr
        raise self._erro("valor numérico")

    # ---------- cidade ----------
    # cidade_decl = "cidade", texto, "{", chegada_decl, saida_decl, "}" ;
    def cidade_decl(self, obrigatoria=False):
        self._kw("cidade", "declaração 'cidade'" if obrigatoria else None)
        nome = self._consumir(TEXTO, None, "nome da cidade entre aspas")
        self._sim("{")
        self._kw("chegada")
        chegada = self._data()
        self._ponto_e_virgula("chegada")
        self._kw("saida")
        saida = self._data()
        self._ponto_e_virgula("saída")
        self._sim("}", "'}' ao fim da cidade")
        return ast.Cidade(nome.valor, chegada, saida, nome.linha, nome.coluna)

    def _data(self):
        t = self._consumir(DATA, None, "data")
        return ast.Data(t.valor, t.linha, t.coluna)

    # ---------- trecho ----------
    # trecho_decl = "trecho", texto, "->", texto, "{",
    #               transporte_decl, custo_decl, duracao_decl, "}" ;
    def trecho_decl(self):
        kw = self._kw("trecho")
        orig = self._consumir(TEXTO, None, "nome da cidade de origem entre aspas")
        self._sim("->")
        dest = self._consumir(TEXTO, None, "nome da cidade de destino entre aspas")
        self._sim("{")
        # transporte_decl = "transporte", identificador, ";" ;
        self._kw("transporte")
        transp = self._consumir(IDENTIFICADOR, None, "tipo de transporte")
        self._ponto_e_virgula("transporte")
        # custo_decl = "custo", expressao, ";" ;
        self._kw("custo")
        custo = self.expressao()
        self._ponto_e_virgula("custo")
        # duracao_decl = "duracao", duracao, ";" ;
        self._kw("duracao")
        d = self._consumir(DURACAO, None, "duração")
        self._ponto_e_virgula("duração")
        self._sim("}", "'}' ao fim do trecho")
        duracao = ast.Duracao(d.lexema, d.valor[0], d.valor[1], d.linha, d.coluna)
        return ast.Trecho(ast.Referencia(orig.valor, orig.linha, orig.coluna),
                          ast.Referencia(dest.valor, dest.linha, dest.coluna),
                          transp.valor, custo, duracao, kw.linha, kw.coluna)

    # ---------- estrutura de controle (requisito 5) ----------
    # se_decl     = "se", expressao, comparador, expressao, bloco, [ "senao", bloco ] ;
    # comparador  = "<" | ">" | "<=" | ">=" ;
    # bloco       = "{", { imprimir_decl }, "}" ;
    def se_decl(self):
        kw = self._kw("se")
        esq = self.expressao()
        if not (self.atual.categoria == SIMBOLO and self.atual.lexema in COMPARADORES):
            raise self._erro("comparador ('<', '>', '<=' ou '>=')")
        op = self.atual
        self.i += 1
        dir_ = self.expressao()
        entao = self._bloco()
        senao = []
        if self._e(PALAVRA_CHAVE, "senao"):
            self.i += 1
            senao = self._bloco()
        return ast.Condicional(esq, op.lexema, dir_, op.linha, op.coluna,
                               entao, senao, kw.linha, kw.coluna)

    def _bloco(self):
        self._sim("{")
        comandos = []
        while self._e(PALAVRA_CHAVE, "imprimir"):
            comandos.append(self.imprimir_decl())
        self._sim("}", "'imprimir' ou '}'")
        return comandos

    # imprimir_decl = "imprimir", texto, ";" ;
    def imprimir_decl(self):
        kw = self._kw("imprimir")
        texto = self._consumir(TEXTO, None, "texto entre aspas")
        self._ponto_e_virgula("imprimir")
        return ast.Imprimir(texto.valor, kw.linha, kw.coluna)


def analisar_sintatico(tokens):
    return Sintatico(tokens).programa()
