import datetime
import re

from . import ast
from .erros import Diagnostico

RE_MOEDA = re.compile(r"^[A-Z]{3}$")

DINHEIRO, NUMERO = "dinheiro", "número"
NOMES_DA_CONDICAO = ("saldo", "subtotal")   # nomes pré-definidos, visíveis só dentro de 'se'


def formatar_dinheiro(centavos):
    return f"{centavos // 100}.{centavos % 100:02d}"


def _data_valida(valor):
    try:
        datetime.date.fromisoformat(valor)
        return True
    except ValueError:
        return False


class Resultado:
    def __init__(self):
        self.diagnosticos = []
        self.subtotal = None   # centavos, quando calculado
        self.saldo = None
        self.orcamento = None  # valor calculado do orçamento
        self.impressoes = []   # textos produzidos pelos blocos 'se'/'senao'

    @property
    def erros(self):
        return [d for d in self.diagnosticos if d.tipo == "erro"]

    @property
    def avisos(self):
        return [d for d in self.diagnosticos if d.tipo == "aviso"]

    @property
    def valido(self):
        return not self.erros


class Semantico:
    def __init__(self, viagem):
        self.v = viagem
        self.res = Resultado()
        self.tabela = {}           # nome -> Cidade (primeira declaração)
        self.temporal_ok = set()   # ids das cidades com datas válidas e saída >= chegada
        self.erro_de_moeda = False
        self.erro_de_tipo = False  # R11/R12 em orçamento ou custo: valores não calculáveis

    def _erro(self, no_linha, no_coluna, msg):
        self.res.diagnosticos.append(Diagnostico("erro", "semântico", no_linha, no_coluna, msg))

    def _aviso(self, no_linha, no_coluna, msg):
        self.res.diagnosticos.append(Diagnostico("aviso", "semântico", no_linha, no_coluna, msg))

    # ------------------------------------------------------------------
    def analisar(self):
        self._primeira_passagem()
        self._segunda_passagem()
        self._calcular_saldo()
        self._avaliar_condicionais()
        self.res.diagnosticos.sort(key=lambda d: (d.tipo != "erro", d.linha, d.coluna))
        return self.res

    # ------------------------------------------------------------------
    def _primeira_passagem(self):
        v = self.v
        # R8 (forma): a moeda da viagem tem três letras maiúsculas
        if not RE_MOEDA.match(v.moeda):
            self._erro(v.linha_moeda, v.coluna_moeda,
                       "R8: código de moeda deve ter três letras maiúsculas")
            self.erro_de_moeda = True

        for c in v.cidades:
            # R1: toda data existe no calendário gregoriano
            datas_ok = True
            for d in (c.chegada, c.saida):
                if not _data_valida(d.valor):
                    self._erro(d.linha, d.coluna,
                               f"R1: data {d.valor} não existe no calendário")
                    datas_ok = False
            # R2: saída igual ou posterior à chegada
            if datas_ok:
                if c.saida.valor < c.chegada.valor:
                    self._erro(c.saida.linha, c.saida.coluna,
                               f'R2: saída anterior à chegada em "{c.nome}"')
                else:
                    self.temporal_ok.add(id(c))
            # R3: nenhum nome de cidade se repete
            if c.nome in self.tabela:
                anterior = self.tabela[c.nome]
                self._erro(c.linha, c.coluna,
                           f'R3: cidade "{c.nome}" já declarada na linha {anterior.linha}')
            else:
                self.tabela[c.nome] = c

    # ------------------------------------------------------------------
    def _segunda_passagem(self):
        v = self.v

        # R8 (consistência): todo valor em dinheiro usa a moeda da viagem
        if not self.erro_de_moeda:
            self._checar_moedas(v.orcamento, "no orçamento")
            for t in v.trechos:
                self._checar_moedas(t.custo, "no custo")
            for c in v.condicionais:
                self._checar_moedas(c.esq, "na condição")
                self._checar_moedas(c.dir, "na condição")

        # R11/R12: tipos e nomes nas expressões
        self._checar_valor(v.orcamento, "o orçamento")
        for t in v.trechos:
            self._checar_valor(t.custo, "o custo")
        for c in v.condicionais:
            te = self._tipo(c.esq, na_condicao=True)
            td = self._tipo(c.dir, na_condicao=True)
            if te is not None and td is not None and te != td:
                self._erro(c.linha_op, c.coluna_op,
                           f"R11: comparação entre {te} e {td}")

        for t in v.trechos:
            # R7: minutos entre 00 e 59 e duração maior que zero
            d = t.duracao
            if d.min_parte > 59:
                self._erro(d.linha, d.coluna, "R7: minutos devem estar entre 00 e 59")
            elif d.minutos == 0:
                self._erro(d.linha, d.coluna, "R7: duração deve ser maior que zero")

            # R4: origem e destino declarados e diferentes entre si
            for ref in (t.origem, t.destino):
                ref.cidade = self.tabela.get(ref.nome)
                if ref.cidade is None:
                    self._erro(ref.linha, ref.coluna,
                               f'R4: cidade "{ref.nome}" não foi declarada')
            o, de = t.origem.cidade, t.destino.cidade
            if o is not None and de is not None and o is de:
                self._erro(t.destino.linha, t.destino.coluna,
                           f'R4: origem e destino do trecho são a mesma cidade "{o.nome}"')
                continue

            # R5: chegada ao destino igual ou posterior à saída da origem
            if (o is not None and de is not None
                    and id(o) in self.temporal_ok and id(de) in self.temporal_ok
                    and de.chegada.valor < o.saida.valor):
                self._erro(t.destino.linha, t.destino.coluna,
                           f'R5: chegada a "{de.nome}" anterior à saída de "{o.nome}"')

        # Cidades em ordem de chegada (só as com datas coerentes)
        ordenadas = sorted((c for c in self.tabela.values() if id(c) in self.temporal_ok),
                           key=lambda c: c.chegada.valor)

        # R6: permanências não se sobrepõem
        mais_tardia = None  # cidade com a maior saída até aqui
        for c in ordenadas:
            if mais_tardia is not None and c.chegada.valor < mais_tardia.saida.valor:
                self._erro(c.chegada.linha, c.chegada.coluna,
                           f'R6: permanência em "{c.nome}" começa antes do fim da '
                           f'de "{mais_tardia.nome}"')
            if mais_tardia is None or c.saida.valor > mais_tardia.saida.valor:
                mais_tardia = c

        # R10 (aviso): cidades consecutivas no tempo ligadas por um trecho
        ligacoes = {(id(t.origem.cidade), id(t.destino.cidade)) for t in v.trechos
                    if t.origem.cidade is not None and t.destino.cidade is not None}
        for a, b in zip(ordenadas, ordenadas[1:]):
            if (id(a), id(b)) not in ligacoes:
                self._aviso(b.linha, b.coluna,
                            f'R10: não há trecho de "{a.nome}" para "{b.nome}"')

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Expressões
    # ------------------------------------------------------------------
    def _checar_moedas(self, expr, onde):
        for f in ast.folhas(expr):
            if isinstance(f, ast.Dinheiro) and f.moeda != self.v.moeda:
                self._erro(f.linha_moeda, f.coluna_moeda,
                           f"R8: moeda {f.moeda} {onde} difere da moeda da viagem ({self.v.moeda})")
                self.erro_de_moeda = True

    def _tipo(self, expr, na_condicao=False):
        """Devolve DINHEIRO, NUMERO ou None (quando já houve erro na subexpressão).

        Regras de tipo (R11):
          dinheiro + dinheiro = dinheiro      número + número = número
          número * dinheiro   = dinheiro      número * número = número
          dinheiro + número   -> erro         dinheiro * dinheiro -> erro
        """
        if isinstance(expr, ast.Dinheiro):
            return DINHEIRO
        if isinstance(expr, ast.Numero):
            return NUMERO
        if isinstance(expr, ast.Nome):
            # R12: só existem 'saldo' e 'subtotal', e só dentro de 'se'
            if not na_condicao:
                self._erro(expr.linha, expr.coluna,
                           f'R12: nome "{expr.nome}" só pode ser usado dentro de \'se\'')
                return None
            if expr.nome not in NOMES_DA_CONDICAO:
                self._erro(expr.linha, expr.coluna,
                           f'R12: nome "{expr.nome}" não declarado (use saldo ou subtotal)')
                return None
            return DINHEIRO
        te = self._tipo(expr.esq, na_condicao)
        td = self._tipo(expr.dir, na_condicao)
        if te is None or td is None:
            return None
        if expr.op == "+":
            if te != td:
                self._erro(expr.linha, expr.coluna, "R11: soma entre dinheiro e número")
                return None
            return te
        # '*'
        if te == DINHEIRO and td == DINHEIRO:
            self._erro(expr.linha, expr.coluna, "R11: multiplicação de dinheiro por dinheiro")
            return None
        return DINHEIRO if DINHEIRO in (te, td) else NUMERO

    def _checar_valor(self, expr, nome):
        """Orçamento e custo precisam resultar em dinheiro."""
        tipo = self._tipo(expr)
        if tipo is None:
            self.erro_de_tipo = True
        elif tipo != DINHEIRO:
            lin, col = ast.inicio(expr)
            self._erro(lin, col, f"R11: {nome} deve ser um valor em dinheiro (falta a moeda)")
            self.erro_de_tipo = True

    @staticmethod
    def _valor(expr, nomes=None):
        """Calcula o valor em centavos. Só é chamado depois que os tipos foram aceitos.
        Multiplicação: os dois lados estão em centésimos, então divide-se por 100
        com arredondamento meio-para-cima (2 * 45.50 = 200 * 4550 / 100 = 9100)."""
        if isinstance(expr, (ast.Dinheiro, ast.Numero)):
            return expr.centavos
        if isinstance(expr, ast.Nome):
            return nomes[expr.nome]
        a = Semantico._valor(expr.esq, nomes)
        b = Semantico._valor(expr.dir, nomes)
        if expr.op == "+":
            return a + b
        return (a * b + 50) // 100

    # ------------------------------------------------------------------
    def _calcular_saldo(self):
        v = self.v
        if self.erro_de_moeda or self.erro_de_tipo:
            return  # sem conversão ou com tipos inválidos: não há subtotal nem saldo
        orcamento = self._valor(v.orcamento)
        subtotal = sum(self._valor(t.custo) for t in v.trechos)
        # R9: soma dos custos não excede o orçamento
        if subtotal > orcamento:
            lin, col = ast.inicio(v.orcamento)
            self._erro(lin, col,
                       f"R9: orçamento excedido: {formatar_dinheiro(subtotal)} {v.moeda} "
                       f"acima de {formatar_dinheiro(orcamento)} {v.moeda}")
        self.res.orcamento = orcamento
        self.res.subtotal = subtotal
        self.res.saldo = orcamento - subtotal

    def _avaliar_condicionais(self):
        """Executa os blocos 'se'/'senao' na ordem em que aparecem no arquivo.
        Só roda se o programa não tem erros (todos os valores são conhecidos)."""
        if not self.res.valido or self.res.saldo is None:
            return
        nomes = {"saldo": self.res.saldo, "subtotal": self.res.subtotal}
        comparar = {"<": lambda a, b: a < b, ">": lambda a, b: a > b,
                    "<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b}
        for c in self.v.condicionais:
            verdade = comparar[c.op](self._valor(c.esq, nomes), self._valor(c.dir, nomes))
            for cmd in (c.entao if verdade else c.senao):
                self.res.impressoes.append(cmd.texto)


def analisar_semantico(viagem):
    return Semantico(viagem).analisar()
