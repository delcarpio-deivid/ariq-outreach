# ariq-outreach

Servidor MCP (FastMCP) para outreach B2B en Arequipa: genera auditorías express con Gemini, construye enlaces `wa.me` y procesa lotes desde CSV.

**Importante:** este proyecto **no envía mensajes** por WhatsApp ni usa la API de Meta. El operador humano abre cada enlace y confirma el envío manualmente.

## Requisitos

- Python 3.11+
- API key de [Google AI Studio](https://aistudio.google.com/) (`GEMINI_API_KEY`)

## Setup

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Editar .env con GEMINI_API_KEY y SENDER_NAME
```

Coloca el CSV de leads en `data/leads_arequipa.csv` (local, gitignored). Puedes copiar desde el consolidado del pipeline de leadgen:

```bash
cp leads_consolidado.csv data/leads_arequipa.csv
```

## MCP en Cursor

El archivo `.cursor/mcp.json` registra el servidor:

```json
{
  "mcpServers": {
    "ariq-outreach": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

En Windows, si el intérprete global no tiene las dependencias, usa la ruta del venv:

`venv/Scripts/python.exe -m mcp_server.server`

Reinicia Cursor tras configurar. Tools disponibles:

- `generar_auditoria_express` — auditoría + mensaje para un lead
- `crear_enlace_whatsapp` — normaliza teléfono y arma `wa.me`
- `procesar_lote` — recorre CSV, omite ya procesados, escribe `data/processed_leads.csv`

## Variación de mensaje vs fase

| Fase pipeline | Variación |
|---------------|-----------|
| 1 | A (WhatsApp/catálogo) |
| 2, 3 | B (SEO local / Maps) |
| 4 | `no_enviar` |

La variación C (follow-up / beca) queda para una herramienta futura.

## Tests

```bash
python -m pytest tests/ -v
```

Los tests usan fixtures ficticios y **mockean** `gemini_client`; no llaman a Gemini con datos reales.

## Seguridad (repo público)

Nunca commitear:

- `data/*.csv` con leads reales
- `leads_consolidado.csv`
- `.env`
- documentación interna con precios

## Depuración

```bash
python -m mcp_server.server
```
