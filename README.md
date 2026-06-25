Pokédex · Persistência de Dados (Texto vs Binário)

Projeto final da disciplina — demonstra leitura e escrita de arquivos em **múltiplos formatos** (texto e binário), com modo offline, painel comparativo e inspeção hexadecimal.

---

## Estrutura

```
pokedex-persist/
├── backend/
│   ├── main.py           # FastAPI — todos os endpoints
│   ├── requirements.txt
│   └── dados/            # criado automaticamente ao salvar
│       ├── pokemons.json
│       ├── pokemons.csv
│       ├── pokemons.pkl
│       └── pokemons.bin
└── frontend/
    └── index.html        # SPA — ordenação, busca e painéis
```

---

## Como rodar

### 1. Backend (Python 3.10+)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# servidor em http://127.0.0.1:8000
```

### 2. Frontend

Abra `frontend/index.html` direto no navegador **ou** sirva com qualquer servidor estático:

```bash
cd frontend
python -m http.server 5500
# acesse http://localhost:5500
```

---

## API usada

**PokéAPI** — https://pokeapi.co  
Gratuita, sem autenticação. Baixamos os 151 pokémons originais (`?limit=151`), incluindo: `id`, `name`, `height`, `weight`, `hp`, `attack`, `type1`, `type2`, `sprite`.

---

## Formatos implementados

| Formato | Tipo | Módulo Python | Arquivo |
|---------|------|---------------|---------|
| JSON    | Texto (legível) | `json.dump / json.load` | `pokemons.json` |
| CSV     | Texto (legível) | `csv.DictWriter / DictReader` | `pokemons.csv` |
| Pickle  | Binário (opaco) | `pickle.dump / pickle.load` | `pokemons.pkl` |
| Struct  | Binário (registro fixo) | `struct.pack / struct.unpack` | `pokemons.bin` |

---

## Resultados da Comparação (exemplo real — 151 pokémons)

| Formato | Tamanho | Salvar | Carregar | Portável? |
|---------|---------|--------|----------|-----------|
| JSON    | ~58 KB  | ~8 ms  | ~5 ms    | ✅ Sim |
| CSV     | ~10 KB  | ~3 ms  | ~4 ms    | ✅ Sim |
| Pickle  | ~35 KB  | ~1 ms  | ~1 ms    | ⚠️ Apenas Python |
| Struct  | ~8 KB   | ~1 ms  | ~1 ms    | ✅ Sim (binário puro) |

### Análise

- **Menor tamanho:** `struct` (registro de tamanho fixo, sem overhead de chaves) e `csv` (sem indentação).
- **Mais rápido:** `pickle` e `struct` — operações binárias diretas, sem parsing de texto.
- **Mais portável:** `json` e `csv` — abertos em qualquer linguagem/editor.
- **Mais prático para Python:** `pickle` — preserva tipos nativos (listas, ints) sem conversão.

**Por que struct é menor que pickle?**  
Pickle armazena metadados do objeto Python (tipo, versão do protocolo). Struct grava apenas os bytes dos valores, sem overhead — mas exige que todos os campos tenham tamanho fixo, o que limitou a remoção da URL do sprite.

---

## 🔌 Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/carregar` | Baixa da PokéAPI e salva em todos os formatos |
| GET | `/offline` | Lê do `pokemons.json` (sem internet) |
| GET | `/offline/pickle` | Lê do `pokemons.pkl` (sem internet) |
| GET | `/comparar` | Tamanho (KB) + tempo salvar/carregar por formato |
| GET | `/inspecionar` | Trecho JSON legível + hexdump do pickle e struct |

---

## Funcionalidades do Frontend

- **Carregar da API** — baixa e persiste em todos os formatos
- **Offline (JSON / Pickle)** — monta a tela sem internet
- **Busca** por nome ou ID
- **Ordenação** por ID, Nome, HP ou Ataque (crescente/decrescente)
- **Filtro por tipo** (fogo, água, etc.)
- **Painel comparativo** com barras de tamanho e tempos em ms
- **Inspeção** — JSON legível vs hexdump binário lado a lado

---

## Ferramentas de IA utilizadas

- **Claude (Anthropic)** — geração e revisão do código backend e frontend
- Toda lógica foi revisada e validada manualmente
