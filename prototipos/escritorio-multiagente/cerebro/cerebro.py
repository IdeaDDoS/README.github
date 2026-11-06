"""v2 — cérebro burro: o Gerente roteia por palavra-chave e o agente devolve resposta pronta.

Sem LLM, sem rede. Só prova o contrato: recebe uma demanda e imprime eventos JSON,
um por linha — os mesmos que o corpo (index.html) já sabe desenhar.

Uso:
    python cerebro.py "corrige o bug do login"
    python cerebro.py "query de vendas por mês" --elenco outro_elenco.json
"""

import argparse
import json
import sys
from pathlib import Path

PADRAO = Path(__file__).with_name("elenco.json")


def carregar_elenco(caminho: Path) -> list[dict]:
    return json.loads(caminho.read_text(encoding="utf-8"))["cadeiras"]


def apresentar(elenco: list[dict]) -> list[dict]:
    """Diz ao corpo quem está sentado em cada cadeira (a plaquinha)."""
    return [
        {"t": "seat.assign", "seat": c["cadeira"], "nome": c["agente"]["placa"],
         "agente": c["agente"]["nome"], "fonte": c["agente"].get("fonte", "")}
        for c in elenco
    ]


def rotear(demanda: str, elenco: list[dict]) -> dict | None:
    """Primeira cadeira cuja palavra aparece na demanda. Sem LLM: regra fixa."""
    texto = demanda.lower()
    for c in elenco[1:]:  # elenco[0] é sempre o gerente
        regras = c.get("regras")
        if regras and any(p in texto for p in regras["palavras"]):
            return c
    return None


def atender(demanda: str, elenco: list[dict]) -> list[dict]:
    gerente = elenco[0]["cadeira"]
    eventos = [{"t": "agent.state", "agent": gerente, "state": "thinking"}]

    alvo = rotear(demanda, elenco)
    if alvo is None:
        return eventos + [{"t": "error", "agent": gerente, "msg": "Ninguém aqui faz isso"}]

    quem, regras = alvo["cadeira"], alvo["regras"]
    return eventos + [
        {"t": "agent.state", "agent": gerente, "state": "idle"},
        {"t": "task.assigned", "from": gerente, "to": quem, "msg": demanda},
        {"t": "agent.state", "agent": quem, "state": "working"},
        {"t": "message", "from": quem, "to": gerente, "msg": regras["responde"]},
        {"t": "agent.state", "agent": quem, "state": "idle"},
        {"t": "task.done", "agent": quem, "output": regras["entrega"]},
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("demanda")
    ap.add_argument("--elenco", type=Path, default=PADRAO)
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    elenco = carregar_elenco(args.elenco)
    for evt in apresentar(elenco) + atender(args.demanda, elenco):
        print(json.dumps(evt, ensure_ascii=False))


if __name__ == "__main__":
    main()
