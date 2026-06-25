import time
import json
import csv
import pickle
import os
import struct
import urllib.request
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Pokédex Persistência API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR    = os.path.join(os.path.dirname(__file__), "dados")
SPRITES_DIR = os.path.join(DATA_DIR, "sprites")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SPRITES_DIR, exist_ok=True)

JSON_PATH   = os.path.join(DATA_DIR, "pokemons.json")
PICKLE_PATH = os.path.join(DATA_DIR, "pokemons.pkl")
CSV_PATH    = os.path.join(DATA_DIR, "pokemons.csv")
BIN_PATH    = os.path.join(DATA_DIR, "pokemons.bin")

POKEAPI_URL = "https://pokeapi.co/api/v2/pokemon?limit=151"

STRUCT_FORMAT = "!H20sHHHH12s12s"
STRUCT_SIZE   = struct.calcsize(STRUCT_FORMAT)

HEADERS = {"User-Agent": "pokedex-persist/1.0 (trabalho escolar)"}


def _download_sprite(pokemon_id: int, url: str) -> str:
    """Baixa o sprite e salva em disco. Retorna o caminho local."""
    if not url:
        return ""
    dest = os.path.join(SPRITES_DIR, f"{pokemon_id}.png")
    if not os.path.exists(dest):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as r:
                with open(dest, "wb") as f:
                    f.write(r.read())
        except Exception:
            return ""
    return f"/sprites/{pokemon_id}.png"


def _fetch_from_api() -> list[dict]:
    """Baixa 151 pokémons da PokéAPI com detalhes básicos e salva sprites."""
    req = urllib.request.Request(POKEAPI_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        lista = json.loads(r.read())["results"]

    pokemons = []
    for entry in lista:
        req2 = urllib.request.Request(entry["url"], headers=HEADERS)
        with urllib.request.urlopen(req2, timeout=15) as r:
            d = json.loads(r.read())
        stats = {s["stat"]["name"]: s["base_stat"] for s in d["stats"]}
        tipos = [t["type"]["name"] for t in d["types"]]
        sprite_url = d["sprites"]["front_default"] or ""
        sprite_local = _download_sprite(d["id"], sprite_url)
        pokemons.append({
            "id":      d["id"],
            "name":    d["name"],
            "height":  d["height"],
            "weight":  d["weight"],
            "hp":      stats.get("hp", 0),
            "attack":  stats.get("attack", 0),
            "type1":   tipos[0] if len(tipos) > 0 else "",
            "type2":   tipos[1] if len(tipos) > 1 else "",
            "sprite":  sprite_local,
        })
    return pokemons


# ── helpers de texto ─────────────────────────────────────────────────────────

def _save_json(data: list[dict]) -> float:
    t0 = time.perf_counter()
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return time.perf_counter() - t0


def _load_json() -> tuple[list[dict], float]:
    t0 = time.perf_counter()
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data, time.perf_counter() - t0


def _save_csv(data: list[dict]) -> float:
    campos = ["id", "name", "height", "weight", "hp", "attack", "type1", "type2", "sprite"]
    t0 = time.perf_counter()
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(data)
    return time.perf_counter() - t0


def _load_csv() -> tuple[list[dict], float]:
    t0 = time.perf_counter()
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            row["id"]     = int(row["id"])
            row["height"] = int(row["height"])
            row["weight"] = int(row["weight"])
            row["hp"]     = int(row["hp"])
            row["attack"] = int(row["attack"])
            data.append(row)
    return data, time.perf_counter() - t0


# ── helpers binários ─────────────────────────────────────────────────────────

def _save_pickle(data: list[dict]) -> float:
    t0 = time.perf_counter()
    with open(PICKLE_PATH, "wb") as f:
        pickle.dump(data, f)
    return time.perf_counter() - t0


def _load_pickle() -> tuple[list[dict], float]:
    t0 = time.perf_counter()
    with open(PICKLE_PATH, "rb") as f:
        data = pickle.load(f)
    return data, time.perf_counter() - t0


def _save_struct(data: list[dict]) -> float:
    t0 = time.perf_counter()
    with open(BIN_PATH, "wb") as f:
        for p in data:
            packed = struct.pack(
                STRUCT_FORMAT,
                p["id"],
                p["name"].encode("utf-8")[:20].ljust(20, b"\x00"),
                p["height"],
                p["weight"],
                p["hp"],
                p["attack"],
                p["type1"].encode("utf-8")[:12].ljust(12, b"\x00"),
                p["type2"].encode("utf-8")[:12].ljust(12, b"\x00"),
            )
            f.write(packed)
    return time.perf_counter() - t0


def _load_struct() -> tuple[list[dict], float]:
    t0 = time.perf_counter()
    data = []
    with open(BIN_PATH, "rb") as f:
        while True:
            chunk = f.read(STRUCT_SIZE)
            if not chunk:
                break
            vals = struct.unpack(STRUCT_FORMAT, chunk)
            pid = vals[0]
            sprite_path = f"/sprites/{pid}.png" if os.path.exists(os.path.join(SPRITES_DIR, f"{pid}.png")) else ""
            data.append({
                "id":     pid,
                "name":   vals[1].rstrip(b"\x00").decode("utf-8"),
                "height": vals[2],
                "weight": vals[3],
                "hp":     vals[4],
                "attack": vals[5],
                "type1":  vals[6].rstrip(b"\x00").decode("utf-8"),
                "type2":  vals[7].rstrip(b"\x00").decode("utf-8"),
                "sprite": sprite_path,
            })
    return data, time.perf_counter() - t0


def _kb(path: str) -> float:
    try:
        return round(os.path.getsize(path) / 1024, 2)
    except FileNotFoundError:
        return 0.0


def _hexdump(path: str, n_bytes: int = 128) -> str:
    try:
        with open(path, "rb") as f:
            raw = f.read(n_bytes)
        lines = []
        for i in range(0, len(raw), 16):
            chunk = raw[i:i+16]
            hex_part  = " ".join(f"{b:02x}" for b in chunk)
            text_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"{i:04x}  {hex_part:<47}  {text_part}")
        return "\n".join(lines)
    except FileNotFoundError:
        return "(arquivo ainda não existe)"


# ── endpoints ────────────────────────────────────────────────────────────────

@app.get("/carregar")
def carregar():
    """Baixa da PokéAPI, salva sprites em disco e grava em todos os formatos."""
    try:
        data = _fetch_from_api()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao chamar a PokéAPI: {e}")

    _save_json(data)
    _save_csv(data)
    _save_pickle(data)
    _save_struct(data)

    return {"total": len(data), "pokemons": data}


@app.get("/offline")
def offline():
    """Lê do arquivo JSON salvo, sem acessar a internet."""
    if not os.path.exists(JSON_PATH):
        raise HTTPException(status_code=404, detail="Nenhum arquivo salvo. Chame /carregar primeiro.")
    data, _ = _load_json()
    return {"total": len(data), "fonte": "json (disco)", "pokemons": data}


@app.get("/offline/pickle")
def offline_pickle():
    """Lê do arquivo pickle salvo."""
    if not os.path.exists(PICKLE_PATH):
        raise HTTPException(status_code=404, detail="Arquivo pickle não encontrado. Chame /carregar primeiro.")
    data, _ = _load_pickle()
    return {"total": len(data), "fonte": "pickle (disco)", "pokemons": data}


@app.get("/comparar")
def comparar():
    resultado = {}

    if os.path.exists(JSON_PATH):
        t_save = _save_json(json.load(open(JSON_PATH, encoding="utf-8")))
        _, t_load = _load_json()
        resultado["json"] = {"kb": _kb(JSON_PATH), "save_ms": round(t_save*1000, 3), "load_ms": round(t_load*1000, 3)}
    else:
        resultado["json"] = {"kb": 0, "save_ms": None, "load_ms": None}

    if os.path.exists(CSV_PATH):
        data_csv, _ = _load_csv()
        t_save = _save_csv(data_csv)
        _, t_load = _load_csv()
        resultado["csv"] = {"kb": _kb(CSV_PATH), "save_ms": round(t_save*1000, 3), "load_ms": round(t_load*1000, 3)}
    else:
        resultado["csv"] = {"kb": 0, "save_ms": None, "load_ms": None}

    if os.path.exists(PICKLE_PATH):
        data_pkl, _ = _load_pickle()
        t_save = _save_pickle(data_pkl)
        _, t_load = _load_pickle()
        resultado["pickle"] = {"kb": _kb(PICKLE_PATH), "save_ms": round(t_save*1000, 3), "load_ms": round(t_load*1000, 3)}
    else:
        resultado["pickle"] = {"kb": 0, "save_ms": None, "load_ms": None}

    if os.path.exists(BIN_PATH):
        data_str, _ = _load_struct()
        t_save = _save_struct(data_str)
        _, t_load = _load_struct()
        resultado["struct"] = {"kb": _kb(BIN_PATH), "save_ms": round(t_save*1000, 3), "load_ms": round(t_load*1000, 3)}
    else:
        resultado["struct"] = {"kb": 0, "save_ms": None, "load_ms": None}

    return resultado


@app.get("/inspecionar")
def inspecionar():
    trecho_json = "(arquivo não encontrado)"
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            trecho_json = "".join([f.readline() for _ in range(20)])

    return {
        "texto_json": trecho_json,
        "hexdump_pickle": _hexdump(PICKLE_PATH),
        "hexdump_struct":  _hexdump(BIN_PATH),
    }


@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/carregar", "/offline", "/offline/pickle", "/comparar", "/inspecionar"]}

# Monta sprites APÓS definir todas as rotas
app.mount("/sprites", StaticFiles(directory=SPRITES_DIR), name="sprites")
