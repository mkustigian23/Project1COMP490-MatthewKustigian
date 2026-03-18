# Project 1 - COMP490 - Matthew Kustigian

Room booking capstone project at Bridgewater State University.

---

## Sprint History

| Sprint | What was built |
|--------|----------------|
| 1 | Speech-to-text transcription (`speech_to_text.py`) |
| 2 | Room Booking REST API client (`room_booking_client.py`) |
| 3 | Voice agent with LangChain + Ollama (`voice_agent.py`) |
| 4 | Textual TUI admin panel to manage rooms in the SQLite DB |

---

## Sprint 4 — Room Admin TUI

A terminal UI (built with [Textual](https://textual.textualize.io/)) that lets an
admin directly manage the meeting-room database:

- **Add** a new room (name, capacity, amenities)
- **Remove** a room — automatically cancels all its bookings and reports
  which usernames were affected; saves a timestamped `.txt` report to `reports/`
- **Change capacity** of any existing room
- Live **activity log** panel showing every action taken

The UI (`tui_app.py`) and the database logic (`db/database.py`) are intentionally
kept in separate files with no cross-imports.

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/mkustigian23/Project1COMP490-MatthewKustigian.git
cd Project1COMP490-MatthewKustigian

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Get the database
#    Option A — copy the real db.sqlite3 from Slack into this folder
#    Option B — generate a sample DB for local testing:
python create_test_db.py db.sqlite3

# 5. Launch the TUI
python tui_app.py db.sqlite3
```

### TUI key bindings

| Key | Action |
|-----|--------|
| `A` | Add a new room |
| `D` | Delete selected room (confirmation dialog + report file) |
| `C` | Change capacity of selected room |
| `R` | Refresh table |
| `Q` | Quit |

---

## Project Structure

```
.
├── tui_app.py              ← Sprint 4 Textual TUI (UI only)
├── create_test_db.py       ← Seeds a sample SQLite DB
├── room_booking_client.py  ← Sprint 2/3 API client
├── speech_to_text.py       ← Sprint 1 transcription
├── voice_agent.py          ← Sprint 3 LangChain voice agent
├── requirements.txt
├── db/
│   ├── __init__.py
│   └── database.py         ← All SQL logic (no UI imports)
├── reports/                ← Auto-created; deletion reports saved here
├── server/                 ← Clone of jsantore/Room_booking_serve
│   └── ...
└── tests/
    └── test_database.py    ← Sprint 4 automated tests (22 tests)
```

---

## Running the Tests

```bash
# All tests (server connectivity skips gracefully if server is offline)
pytest tests -v --tb=short

# With your deployed server
SERVER_URL=http://<your-droplet-ip>:8000 pytest tests -v --tb=short
```

---

## Test Coverage Map

The table below maps each Sprint 4 requirement to the test(s) that cover it.

| Sprint 4 Requirement | Test Class | Test Method(s) |
|----------------------|------------|----------------|
| **Add a room** — function inserts and returns id | `TestAddRoom` | `test_add_room_returns_new_id` |
| **Add a room** — values stored correctly | `TestAddRoom` | `test_add_room_data_persists` |
| **Add a room** — appears in room list | `TestAddRoom` | `test_add_room_appears_in_get_all` |
| **Add a room** — rejects blank name | `TestAddRoom` | `test_add_room_empty_name_raises` |
| **Add a room** — rejects zero/negative capacity | `TestAddRoom` | `test_add_room_zero_capacity_raises`, `test_add_room_negative_capacity_raises` |
| **Remove a room** — returns cancelled usernames | `TestRemoveRoom` | `test_remove_returns_affected_usernames` |
| **Remove a room** — no bookings → empty list | `TestRemoveRoom` | `test_remove_no_bookings_returns_empty` |
| **Remove a room** — room gone from DB | `TestRemoveRoom` | `test_remove_deletes_room` |
| **Remove a room clears its bookings** | `TestRemoveRoom` | `test_remove_clears_bookings` |
| **Remove a room** — error on missing room | `TestRemoveRoom` | `test_remove_nonexistent_raises` |
| **Remove a room** — other rooms unaffected | `TestRemoveRoom` | `test_remove_leaves_other_rooms` |
| **Change capacity** — new value persists | `TestUpdateCapacity` | `test_update_capacity_persists` |
| **Change capacity** — rejects 0/negative | `TestUpdateCapacity` | `test_update_capacity_zero_raises`, `test_update_capacity_negative_raises` |
| **Change capacity** — error on missing room | `TestUpdateCapacity` | `test_update_nonexistent_room_raises` |
| **Change capacity** — other fields unchanged | `TestUpdateCapacity` | `test_update_other_fields_unchanged` |
| **Report saved to file** — file created | `TestSaveDeletionReport` | `test_report_file_created` |
| **Report contains room name** | `TestSaveDeletionReport` | `test_report_contains_room_name` |
| **Report lists affected usernames** | `TestSaveDeletionReport` | `test_report_contains_usernames` |
| **Report notes no reservations** when empty | `TestSaveDeletionReport` | `test_report_empty_usernames_message` |
| **Server is up after deploy** | `TestServerConnectivity` | `test_server_is_reachable` |

---

## GitHub Actions / Deployment

### Required GitHub Secrets

Go to: **Repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Used for |
|--------|----------|
| `SERVER_URL` | Sprint 2/3 API calls + server smoke test |
| `EMAIL` | API login |
| `PASSWORD` | API login |
| `DO_HOST` | DigitalOcean droplet IP/hostname |
| `DO_USER` | SSH username (usually `root`) |
| `DO_SSH_KEY` | Full private key for SSH access |

### Pipeline flow

```
push to main
    │
    ▼
build-and-test job
  ├─ apt deps (portaudio)
  ├─ pip install -r requirements.txt + flake8 + pytest
  ├─ Download Vosk model
  ├─ flake8 lint (E9, F63, F7, F82 — hard errors only)
  ├─ Create .env from secrets
  ├─ python create_test_db.py test_ci.sqlite3
  └─ pytest tests/ -v
         │
         │  (only on push, only if build-and-test passes)
         ▼
deploy job
  ├─ rsync server/ → droplet:/opt/room_booking_server/
  ├─ SSH: venv + migrate + restart gunicorn
  └─ pytest tests/test_database.py::TestServerConnectivity
```

### Setting up the SSH key for DigitalOcean

```bash
# Generate a dedicated deploy key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/do_deploy -N ""

# Add the public key to your droplet
ssh-copy-id -i ~/.ssh/do_deploy.pub root@<your-droplet-ip>

# Paste the PRIVATE key into the DO_SSH_KEY GitHub Secret
cat ~/.ssh/do_deploy
```

### Cloning the server into your repo

```bash
# From the repo root:
git clone https://github.com/jsantore/Room_booking_serve server/
# Then commit the server/ folder (or add it as a git submodule)
```

---

## Features (Sprints 1–3)

### Speech-to-Text (`speech_to_text.py`)
- Live microphone input or audio file
- Google Speech Recognition (free tier) + Vosk offline model
- Ambient noise adjustment and timeout handling

### Room Booking Client (`room_booking_client.py`)
- JWT authentication with email/password
- List available rooms, book a room, view history, cancel bookings

### Voice Agent (`voice_agent.py`)
- Natural-language questions: "Do I have any bookings today?"
- LangChain + Ollama (local LLM — no API key needed)
- Uses `langchain-ollama` with `ibm/granite4:1b-h` or similar

---

## Prerequisites

- Python 3.10+
- Git
- PortAudio (`sudo apt-get install portaudio19-dev` on Linux)
- Ollama + a pulled model (optional, for Sprint 3 voice mode)
- Microphone (optional, for live speech input)
