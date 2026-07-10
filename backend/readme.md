# AI Meeting Assistant — Backend

A FastAPI backend that turns a meeting recording (YouTube link or uploaded audio/video file) into a searchable, queryable meeting record: transcript, title, summary, action items, key decisions, open questions, and a RAG-powered Q&A chat over the transcript.

---

## 1. What it does

Given either a **YouTube URL** or an **uploaded audio/video file**, the backend:

1. Downloads/converts the source into a normalized 16kHz mono WAV file and splits it into 2-minute chunks.
2. Transcribes every chunk with **Groq's hosted Whisper** and stitches the chunks into one transcript.
3. Runs five LLM tasks **in parallel** (via `ThreadPoolExecutor`) against the transcript using **Mistral**:
   - Title generation
   - Map-reduce summary (chunked → per-chunk summary → combined bullet-point summary)
   - Action item extraction
   - Key decision extraction
   - Open/unresolved question extraction
4. **Simultaneously**, builds a per-meeting **Chroma vector store** from the transcript (chunked + embedded with a local HuggingFace sentence-transformer) so it can be queried later.
5. Persists everything to a SQLite database (transcript, summary, analysis fields, audio metadata, timestamps).
6. Exposes a **chat endpoint** that answers free-form questions about a specific meeting using **Retrieval-Augmented Generation** over that meeting's vector store.
7. Exposes CRUD-style endpoints to list, fetch, and delete meetings (deleting a meeting also cleans up its vector store, audio file, and leftover chunk files on disk).

---

## 2. Tech stack

| Concern | Library / Service |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Config | pydantic-settings (`.env` file) |
| LLM orchestration | LangChain (LCEL runnables) |
| LLM (reasoning/generation) | Mistral, via `langchain-mistralai` (`mistral-small-latest` by default) |
| Speech-to-text | Groq-hosted Whisper (`whisper-large-v3-turbo` by default) |
| Embeddings | HuggingFace `sentence-transformers` (`all-MiniLM-L6-v2`, CPU) |
| Vector store | ChromaDB (one persisted collection per meeting) |
| Relational storage | SQLite via SQLAlchemy ORM |
| Audio handling | `yt-dlp` (YouTube download), `pydub` + `ffmpeg` (conversion/chunking) |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` |

---

## 3. Project structure

```
backend/
├── main.py                      # FastAPI app entrypoint; creates DB tables, mounts router
├── requirements.txt
├── app/
│   ├── config.py                 # Settings loaded from .env (API keys, model names, dirs)
│   ├── api/
│   │   ├── router.py              # Aggregates health/meetings/chat routers
│   │   └── routes/
│   │       ├── health.py          # GET / , GET /health
│   │       ├── meetings.py        # POST/GET/GET-by-id/DELETE /meetings
│   │       └── chat.py            # POST /chat
│   ├── core/                     # LLM / AI pipeline building blocks
│   │   ├── llm.py                 # Factory for the Mistral chat model
│   │   ├── transcriber.py         # Groq Whisper transcription
│   │   ├── summarize.py           # Map-reduce summary + title generation
│   │   ├── extractor.py           # Action items / decisions / open questions chains
│   │   ├── vector_store.py        # Chroma build/load/retriever helpers (per-meeting)
│   │   └── rag_engine.py          # Standalone RAG chain builder (see note below)
│   ├── services/
│   │   ├── meeting_service.py     # Orchestrates the full pipeline end-to-end
│   │   ├── chat_service.py        # RAG chain used by the /chat endpoint
│   │   └── storage_service.py     # Cleans up vector store/audio/chunks on delete
│   ├── repositories/
│   │   └── meeting_repository.py  # SQLAlchemy CRUD for the Meeting table
│   ├── db/
│   │   ├── database.py            # Engine, session factory, declarative Base (SQLite)
│   │   ├── models.py              # Meeting ORM model
│   │   └── dependencies.py        # get_db() FastAPI dependency
│   ├── schemas/                  # Pydantic request/response models
│   │   ├── meeting.py, meeting_list.py, meeting_detail.py
│   │   ├── analysis.py, audio.py, chat.py, response.py
│   └── utils/
│       └── audio_processor.py     # YouTube download, WAV conversion, chunking
```

---

## 4. Architecture / data flow

### 4.1 Ingest pipeline (`POST /meetings`)

```
Client
  │  youtube_url  OR  file
  ▼
MeetingService.process(source)
  │
  ├─ 1. _prepare_audio(source)          → app/utils/audio_processor.py
  │       - YouTube URL → yt-dlp download → ffmpeg extract → WAV
  │       - Uploaded file → pydub convert → mono, 16kHz WAV
  │       - Split into 2-minute chunks
  │
  ├─ 2. _transcribe(chunks)             → app/core/transcriber.py
  │       - Each chunk sent to Groq Whisper, sequentially
  │       - Chunks joined into one transcript string
  │
  ├─ 3. Parallel (ThreadPoolExecutor, 2 workers):
  │       ├─ _analyze(transcript)       → app/core/summarize.py, extractor.py
  │       │     - title, summary, action_items, key_decisions, open_questions
  │       │     - (internally also parallelized, 5 workers)
  │       └─ _build_vector_store(meeting_id, transcript) → app/core/vector_store.py
  │             - chunk transcript (500 chars / 50 overlap)
  │             - embed with all-MiniLM-L6-v2
  │             - persist Chroma collection at vector_db/{meeting_id}
  │
  ├─ 4. _save_meeting(...)              → SQLite via MeetingRepository
  │
  └─ 5. Return MeetingResponse (meeting_id, title, transcript, summary,
         action_items, key_decisions, open_questions)
```

### 4.2 Chat / Q&A pipeline (`POST /chat`)

```
Client → { meeting_id, question }
  │
  ▼
ChatService.ask(meeting_id, question)
  │
  ├─ load_vector_store(meeting_id)   → reopen the persisted Chroma collection
  ├─ retriever (k=4 similarity search)
  ├─ RAG prompt: "answer ONLY from meeting context, else say you can't find it"
  ├─ get_llm() (Mistral) | StrOutputParser()
  └─ return ChatResponse(answer)
```

Note: `ChatService` explicitly deletes the loaded vector store object and runs `gc.collect()` in a `finally` block after each request — this looks like a deliberate workaround for Chroma/SQLite file-handle or memory issues on repeated loads.

### 4.3 Delete pipeline (`DELETE /meetings/{id}`)

```
StorageService.delete_meeting_assets(meeting)
  ├─ delete_vector_store(meeting_id)   → rmtree vector_db/{meeting_id}
  ├─ delete_audio(audio_path)          → remove the WAV file
  └─ delete_chunks(audio_path)         → remove {audio}_chunk_*.wav files
```

---

## 5. API reference

Base URL: `http://localhost:8000`

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/` | Root ping — returns a static welcome message |
| GET | `/health` | Returns `{"status": "healthy"}` |

### Meetings

| Method | Path | Description |
|---|---|---|
| POST | `/meetings` | Ingest a meeting from a YouTube URL **or** an uploaded file (multipart form). Runs the full pipeline synchronously and returns the result. |
| GET | `/meetings` | List all meetings (id, title, status, created_at) |
| GET | `/meetings/{meeting_id}` | Full meeting detail (transcript, summary, analysis fields, timestamps) |
| DELETE | `/meetings/{meeting_id}` | Deletes the meeting row plus its vector store, audio file, and chunk files |

**`POST /meetings` request** — exactly one of these two form fields:
- `youtube_url` (form field, string)
- `file` (form file, audio/video upload)

Sending both, or neither, returns `400`.

**`POST /meetings` response** (`MeetingResponse`):
```json
{
  "meeting_id": "uuid-string",
  "title": "string",
  "transcript": "string",
  "summary": "string",
  "action_items": "string",
  "key_decisions": "string",
  "open_questions": "string"
}
```

**`GET /meetings` response** (`MeetingListResponse[]`):
```json
[
  { "id": "uuid", "title": "string", "status": "completed", "created_at": "2026-07-10T12:00:00" }
]
```

**`GET /meetings/{id}` response** (`MeetingDetailResponse`): same as above list item, plus `transcript`, `summary`, `action_items`, `key_decisions`, `open_questions`, `youtube_url`, `filename`, `duration`, `updated_at`.

**`DELETE /meetings/{id}` response:**
```json
{ "message": "Meeting deleted successfully." }
```
Returns `404` if the meeting doesn't exist.

### Chat

| Method | Path | Description |
|---|---|---|
| POST | `/chat` | Ask a question about a specific meeting's transcript (RAG) |

**Request** (`ChatRequest`):
```json
{ "meeting_id": "uuid-string", "question": "What did we decide about the launch date?" }
```

**Response** (`ChatResponse`):
```json
{ "answer": "string" }
```

---

## 6. Data model

`Meeting` (SQLite table `meetings`):

| Column | Type | Notes |
|---|---|---|
| id | String (PK) | UUID4, generated per meeting |
| title | Text | LLM-generated |
| transcript | Text | Full stitched transcript |
| summary | Text | Map-reduce bullet summary |
| action_items | Text | Numbered list, LLM-generated |
| key_decisions | Text | Numbered list, LLM-generated |
| open_questions | Text | Numbered list, LLM-generated |
| youtube_url | Text, nullable | Set only if source was a URL |
| filename | Text, nullable | Basename of the processed WAV |
| audio_path | Text, nullable | Full path to the WAV file on disk |
| duration | String, nullable | `"MM:SS"` |
| status | String | `"completed"` (no other states currently set) |
| created_at | DateTime | UTC, auto |
| updated_at | DateTime | UTC, auto-updates on row update |

---

## 7. Setup & running locally

### Prerequisites
- Python 3.10+
- `ffmpeg` installed and on PATH (required by `pydub` / `yt-dlp` audio extraction)
- A Groq API key (for Whisper transcription)
- A Mistral API key (for all LLM tasks)

### Install

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in `backend/` (this is read by `app/config.py`):

```env
GROQ_API_KEY=your_groq_key_here
MISTRAL_API_KEY=your_mistral_key_here

# Optional overrides (defaults shown)
GROQ_WHISPER_MODEL=whisper-large-v3-turbo
MISTRAL_MODEL=mistral-small-latest
EMBEDDING_MODEL=all-MiniLM-L6-v2
UPLOAD_DIR=uploads
VECTOR_DB_DIR=vector_db
CHROMA_COLLECTION=meeting_transcripts
```

`GROQ_API_KEY` and `MISTRAL_API_KEY` are **required** — the app raises a `pydantic` validation error on startup if either is missing.

### Run

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

On first run, `main.py` calls `Base.metadata.create_all(engine)`, so the SQLite file (`meeting_assistant.db`) and the `meetings` table are created automatically — no migration step needed for this stage of the project.

Directories created at runtime (not committed, see `.gitignore`):
- `downloads/` — YouTube audio downloads
- `vector_db/{meeting_id}/` — per-meeting Chroma collections
- WAV chunk files (`{audio}_chunk_N.wav`) next to the source audio

---