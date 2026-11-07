#!/usr/bin/env python3
"""Interface de linha de comando da CHECKout.

Uso:
  python checkout.py roteiro.checkout           valida e imprime diagnósticos ou a saída
  python checkout.py --ast roteiro.checkout     imprime a AST em JSON
  python checkout.py --tokens roteiro.checkout  imprime a lista de tokens
"""
import sys

from checkout import executar, ler_arquivo


def main(argv):
    modo = "validar"
    args = list(argv)
    if args and args[0] in ("--ast", "--tokens"):
        modo = args.pop(0)[2:]
    if len(args) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        fonte = ler_arquivo(args[0])
    except OSError as e:
        print(f"Não foi possível abrir o arquivo: {e}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print("O arquivo não está em UTF-8.", file=sys.stderr)
        return 2
    texto, codigo = executar(fonte, modo)
    print(texto)
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))