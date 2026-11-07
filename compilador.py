"""Junta as três fases e produz a saída do programa (Seções 4.2 e 5.4)."""
import json

from .erros import ErroCompilacao
from .lexico import analisar_lexico
from .semantico import analisar_semantico, formatar_dinheiro
from .sintatico import analisar_sintatico


def ler_arquivo(caminho):
    # newline="" preserva \r\n para o léxico contar uma quebra só
    with open(caminho, encoding="utf-8", newline="") as f:
        return f.read()


def executar(fonte, modo="validar"):
    """Executa a análise e devolve (texto_de_saida, codigo_de_saida).

    modo: "validar" (padrão), "ast" (imprime a AST em JSON) ou "tokens".
    Código de saída: 0 = válido, 1 = erro.
    """
    try:
        tokens = analisar_lexico(fonte)
        if modo == "tokens":
            linhas = [f"{t.linha}:{t.coluna}\t{t.categoria}\t{t.lexema}" for t in tokens]
            linhas.append(f"Total: {len(tokens)} tokens")
            return "\n".join(linhas), 0
        viagem = analisar_sintatico(tokens)
    except ErroCompilacao as e:
        return str(e.diagnostico), 1

    if modo == "ast":
        return json.dumps(viagem.para_dict(), ensure_ascii=False, indent=2), 0

    res = analisar_semantico(viagem)
    saida = [str(d) for d in res.diagnosticos]
    if not res.valido:
        return "\n".join(saida), 1

    m = viagem.moeda
    saida += [
        "Programa válido.",
        f"Orçamento: {formatar_dinheiro(viagem.orcamento.centavos)} {m}",
        f"Subtotal de deslocamentos: {formatar_dinheiro(res.subtotal)} {m}",
        f"Saldo: {formatar_dinheiro(res.saldo)} {m}",
    ]
    return "\n".join(saida), 0
