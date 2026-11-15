#!/usr/bin/env python3
"""Suíte de regressão da CHECKout.

Roda todos os casos de testes/casos/ num único comando, compara a saída com o
arquivo .esperado e verifica os critérios de aceite. Gera:

  testes/resultados.md   tabelas prontas para a seção de Avaliação do artigo
  testes/resultados.csv  resultado caso a caso (para planilha/gráfico)

Uso:  python testes/rodar_testes.py        (a partir da raiz do repositório)
Sai com código 0 se tudo passar, 1 caso contrário.
"""
import csv
import datetime
import json
import os
import platform
import re
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)

from checkout import executar, ler_arquivo           # noqa: E402
from checkout.lexico import analisar_lexico           # noqa: E402

CASOS = os.path.join(AQUI, "casos")
RE_DIAG = re.compile(r"^(Erro (léxico|sintático|semântico)|Aviso) no arquivo (\S+), linha (\d+), coluna (\d+): (.*)$")

GRUPOS = [
    ("V", "Válidos (controle)"),
    ("W", "Válido com aviso (controle)"),
    ("L", "Erro léxico"),
    ("P", "Erro sintático"),
    ("S", "Erro semântico"),
]


def grupo_de(id_):
    # V7 é um arquivo com erro léxico (\r\n + vírgula); fica no grupo léxico
    if id_ == "V7":
        return "L"
    return id_[0]


def classificar(texto):
    """Resume uma saída: (aceito?, fase do 1º erro, posição do 1º erro, nº de diagnósticos)."""
    linhas = [l for l in texto.splitlines() if l.strip()]
    diags = [RE_DIAG.match(l) for l in linhas]
    diags = [d for d in diags if d]
    erros = [d for d in diags if d.group(1).startswith("Erro")]
    aceito = any(l == "Programa válido." for l in linhas)
    fase = erros[0].group(2) if erros else None
    pos = f"{erros[0].group(4)}:{erros[0].group(5)}" if erros else None
    return aceito, fase, pos, len(diags)


def ordem(id_):
    return ("VWLPS".index(id_[0]), int(id_[1:]))


def main():
    descricoes = {}
    with open(os.path.join(AQUI, "casos.csv"), encoding="utf-8") as f:
        for linha in csv.DictReader(f, delimiter=";"):
            descricoes[linha["id"]] = linha["descricao"]

    ids = sorted((n[:-9] for n in os.listdir(CASOS) if n.endswith(".checkout")), key=ordem)
    resultados = []
    t_total = 0.0

    for id_ in ids:
        fonte = ler_arquivo(os.path.join(CASOS, id_ + ".checkout"))
        with open(os.path.join(CASOS, id_ + ".esperado"), encoding="utf-8") as f:
            esperado = f.read().rstrip("\n")
        t0 = time.perf_counter()
        obtido, _ = executar(fonte, arquivo=id_ + ".checkout")
        dt = time.perf_counter() - t0
        t_total += dt

        e_aceito, e_fase, e_pos, e_n = classificar(esperado)
        o_aceito, o_fase, o_pos, o_n = classificar(obtido)
        deve_rejeitar = not e_aceito

        if obtido == esperado:
            status = "conforme"
        elif deve_rejeitar and o_aceito:
            status = "escape"              # erro proposital não detectado
        elif not deve_rejeitar and not o_aceito:
            status = "falso positivo"      # programa correto rejeitado
        else:
            status = "divergente"          # detectou, mas diagnóstico/posição diferente

        resultados.append({
            "id": id_, "grupo": grupo_de(id_), "descricao": descricoes.get(id_, ""),
            "deve_rejeitar": deve_rejeitar, "rejeitou": not o_aceito,
            "fase_esperada": e_fase or "-", "fase_obtida": o_fase or "-",
            "pos_esperada": e_pos or "-", "pos_obtida": o_pos or "-",
            "diag_esperados": e_n, "diag_obtidos": o_n,
            "status": status, "tempo_ms": dt * 1000,
            "esperado": esperado, "obtido": obtido,
        })

    # ---------------- critérios de aceite extras (Seção 6.3) ----------------
    criterios = []
    fonte_v1 = ler_arquivo(os.path.join(CASOS, "V1.checkout"))
    toks = analisar_lexico(fonte_v1)
    ultimo = toks[-1]
    ok = len(toks) == 48 and ultimo.categoria == "EOF" and (ultimo.linha, ultimo.coluna) == (19, 1)
    criterios.append(("Léxico: V1 produz 48 tokens, EOF em 19:1",
                      ok, f"{len(toks)} tokens, último {ultimo.categoria} em {ultimo.linha}:{ultimo.coluna}"))

    ast_txt, _ = executar(fonte_v1, "ast")
    with open(os.path.join(AQUI, "V1.ast.esperado.json"), encoding="utf-8") as f:
        ast_esp = json.load(f)
    try:
        ok = json.loads(ast_txt) == ast_esp
        detalhe = "idêntica à Seção 4.1" if ok else "difere da Seção 4.1"
    except json.JSONDecodeError:
        ok, detalhe = False, ast_txt
    criterios.append(("Sintático: checkout --ast de V1 igual à AST da Seção 4.1", ok, detalhe))

    # ---------------- impressão no terminal ----------------
    print(f"{'ID':<5}{'Status':<16}{'Fase esp.':<12}{'Fase obt.':<12}{'Pos esp.':<10}{'Pos obt.':<10}Descrição")
    print("-" * 100)
    for r in resultados:
        print(f"{r['id']:<5}{r['status']:<16}{r['fase_esperada']:<12}{r['fase_obtida']:<12}"
              f"{r['pos_esperada']:<10}{r['pos_obtida']:<10}{r['descricao']}")
    falhas = [r for r in resultados if r["status"] != "conforme"]
    for r in falhas:
        print(f"\n--- {r['id']} ({r['status']}) ---\nESPERADO:\n{r['esperado']}\nOBTIDO:\n{r['obtido']}")
    print()
    for nome, ok, detalhe in criterios:
        print(f"[{'OK' if ok else 'FALHOU'}] {nome} ({detalhe})")

    n = len(resultados)
    conformes = n - len(falhas)
    print(f"\n{conformes}/{n} casos conformes à matriz; "
          f"{sum(ok for _, ok, _ in criterios)}/{len(criterios)} critérios extras; "
          f"tempo total {t_total * 1000:.1f} ms")

    # ---------------- arquivos de resultado ----------------
    gravar_csv(resultados)
    gravar_md(resultados, criterios, t_total)
    print(f"\nResultados gravados em testes/resultados.md e testes/resultados.csv")
    return 0 if not falhas and all(ok for _, ok, _ in criterios) else 1


def gravar_csv(resultados):
    campos = ["id", "grupo", "descricao", "deve_rejeitar", "rejeitou", "fase_esperada",
              "fase_obtida", "pos_esperada", "pos_obtida", "diag_esperados", "diag_obtidos",
              "status", "tempo_ms"]
    with open(os.path.join(AQUI, "resultados.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in resultados:
            linha = dict(r)
            linha["tempo_ms"] = f"{r['tempo_ms']:.3f}"
            w.writerow(linha)


def gravar_md(resultados, criterios, t_total):
    out = []
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    out.append("# Resultados da suíte de testes da CHECKout\n")
    out.append(f"Execução: {agora} · Python {platform.python_version()} · {platform.system()}\n")

    # Tabela 1: resumo por grupo (métricas do eixo B)
    out.append("## Tabela 1 — Resumo por grupo\n")
    out.append("| Grupo | Casos | Conformes | Rejeitados | Escapes | Falsos positivos | Fase correta | Posição correta |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    tot = dict(n=0, conf=0, rej=0, esc=0, fp=0, fase=0, pos=0)
    for g, nome in GRUPOS:
        rs = [r for r in resultados if r["grupo"] == g]
        if not rs:
            continue
        n = len(rs)
        conf = sum(r["status"] == "conforme" for r in rs)
        rej = sum(r["rejeitou"] for r in rs)
        esc = sum(r["status"] == "escape" for r in rs)
        fp = sum(r["status"] == "falso positivo" for r in rs)
        fase = sum(r["fase_esperada"] == r["fase_obtida"] for r in rs)
        pos = sum(r["pos_esperada"] == r["pos_obtida"] for r in rs)
        out.append(f"| {nome} | {n} | {conf} | {rej} | {esc} | {fp} | {fase}/{n} | {pos}/{n} |")
        for k, v in zip(tot, (n, conf, rej, esc, fp, fase, pos)):
            tot[k] += v
    out.append(f"| **Total** | **{tot['n']}** | **{tot['conf']}** | **{tot['rej']}** | "
               f"**{tot['esc']}** | **{tot['fp']}** | **{tot['fase']}/{tot['n']}** | "
               f"**{tot['pos']}/{tot['n']}** |\n")

    com_erro = [r for r in resultados if r["deve_rejeitar"]]
    controles = [r for r in resultados if not r["deve_rejeitar"]]
    detectados = sum(r["rejeitou"] for r in com_erro)
    exatos = sum(r["status"] == "conforme" for r in com_erro)
    fps = sum(r["rejeitou"] for r in controles)
    out.append("## Tabela 2 — Métricas de detecção\n")
    out.append("| Métrica | Valor |")
    out.append("|---|---:|")
    out.append(f"| Programas com erro proposital | {len(com_erro)} |")
    out.append(f"| Programas de controle (válidos) | {len(controles)} |")
    out.append(f"| Taxa de detecção (erros rejeitados / com erro) | {detectados}/{len(com_erro)} ({100 * detectados / len(com_erro):.1f}%) |")
    out.append(f"| Diagnóstico e posição exatos | {exatos}/{len(com_erro)} ({100 * exatos / len(com_erro):.1f}%) |")
    out.append(f"| Escapes (erro aceito como válido) | {len(com_erro) - detectados} |")
    out.append(f"| Falsos positivos (controle rejeitado) | {fps}/{len(controles)} |")
    out.append(f"| Tempo total da suíte | {t_total * 1000:.1f} ms |")
    out.append(f"| Tempo médio por caso | {t_total * 1000 / len(resultados):.2f} ms |\n")

    # Tabela 3: cobertura das regras semânticas
    out.append("## Tabela 3 — Regras semânticas exercitadas\n")
    out.append("| Regra | Casos que a disparam | Todos conformes? |")
    out.append("|---|---|---|")
    for regra in [f"R{i}" for i in range(1, 13)]:
        rs = [r for r in resultados if re.search(rf"\b{regra}:", r["esperado"])]
        ids = ", ".join(r["id"] for r in rs) or "—"
        todos = "sim" if rs and all(r["status"] == "conforme" for r in rs) else ("—" if not rs else "não")
        out.append(f"| {regra} | {ids} | {todos} |")
    out.append("")

    out.append("## Critérios de aceite adicionais (Seção 6.3)\n")
    for nome, ok, detalhe in criterios:
        out.append(f"- {'✔' if ok else '✘'} {nome} — {detalhe}")
    out.append("")

    out.append("## Tabela 4 — Resultado caso a caso\n")
    out.append("| ID | Alteração | Fase esperada | Fase obtida | Posição esperada | Posição obtida | Resultado |")
    out.append("|---|---|---|---|---|---|---|")
    for r in resultados:
        desc = r["descricao"].replace("|", "\\|")
        out.append(f"| {r['id']} | {desc} | {r['fase_esperada']} | {r['fase_obtida']} | "
                   f"{r['pos_esperada']} | {r['pos_obtida']} | {r['status']} |")
    out.append("")

    falhas = [r for r in resultados if r["status"] != "conforme"]
    if falhas:
        out.append("## Divergências\n")
        for r in falhas:
            out.append(f"### {r['id']} ({r['status']})\n")
            out.append("Esperado:\n```\n" + r["esperado"] + "\n```\nObtido:\n```\n" + r["obtido"] + "\n```\n")

    with open(os.path.join(AQUI, "resultados.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))


if __name__ == "__main__":
    sys.exit(main())
