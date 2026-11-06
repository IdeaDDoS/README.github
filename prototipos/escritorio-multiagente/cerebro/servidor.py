"""v3 — liga o cérebro ao corpo por WebSocket.

Uso (dentro de cerebro/):
    .venv\\Scripts\\python servidor.py
e abra http://localhost:8000 — a tela conecta sozinha.

- GET /   → serve o index.html (o corpo).
- WS  /ws → ao conectar, manda o seat.assign de cada cadeira (lido do elenco.json
            na hora: editou o elenco, recarregou a página, a plaquinha mudou).
            Recebe {"demanda": "..."} e devolve os eventos com pausa entre eles,
            no ritmo da animação.
"""

import asyncio
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from cerebro import PADRAO, apresentar, atender, carregar_elenco

CORPO = Path(__file__).parent.parent / "index.html"

# Segundos de espera DEPOIS de cada evento — o tempo que a tela leva para encenar.
PAUSA = {"seat.assign": 0, "task.assigned": 5.0, "message": 2.5, "task.done": 1.0}
PAUSA_PADRAO = 1.2

app = FastAPI(title="Escritório Multiagente — cérebro")


@app.get("/")
def corpo() -> FileResponse:
    return FileResponse(CORPO)


async def enviar(ws: WebSocket, eventos: list[dict]) -> None:
    for evt in eventos:
        await ws.send_json(evt)
        await asyncio.sleep(PAUSA.get(evt["t"], PAUSA_PADRAO))


@app.websocket("/ws")
async def canal(ws: WebSocket) -> None:
    await ws.accept()
    elenco = carregar_elenco(PADRAO)
    await enviar(ws, apresentar(elenco))
    try:
        while True:
            pedido = await ws.receive_json()
            demanda = str(pedido.get("demanda", "")).strip()
            if demanda:
                await enviar(ws, atender(demanda, elenco))
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
