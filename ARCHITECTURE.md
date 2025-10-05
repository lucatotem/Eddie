# Architecture Overview

## Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React 18 + Vite
- **Storage**: JSON files (no database)
- **Integration**: Confluence REST API v1
- **Deployment**: Local development (production-ready)

---

## System Flow

```
User Browser (React)
    ↓ 
FastAPI Backend
    ↓
Confluence Cloud API
    ↓
Returns Pages
    ↓
Display in UI
```

---

## Backend (`backend/`)

```
app/
├── main.py                 # FastAPI app entry
├── config.py               # Environment settings
├── api/
│   ├── confluence.py       # Confluence endpoints
│   └── onboarding.py       # Course CRUD + data
├── models/
│   └── onboarding_config.py  # Config schemas
└── services/
    ├── confluence_service.py  # Confluence API client
    └── config_storage.py      # File I/O for configs
```

### Key Services

**ConfluenceService** (`confluence_service.py`)
- `get_page_by_id()` - Fetch single page
- `get_child_pages()` - Recursive folder expansion
- `search_pages_by_label()` - CQL-based search

**ConfigStorage** (`config_storage.py`)
- `create()` - Save new config to JSON
- `get()` - Load config by ID
- `list_all()` - Get all configs
- `update()` - Modify existing config
- `delete()` - Remove config file

---

## Frontend (`frontend/src/`)

```
components/
├── ConfigManager.jsx      # Home screen (list all courses)
├── ConfigEditor.jsx       # Create/edit course form
└── Dashboard.jsx          # View course + modules + quiz

services/
└── api.js                 # Axios HTTP client
```

### Component Flow

1. **ConfigManager** → Shows all saved courses
2. **ConfigEditor** → Create/edit course settings
3. **Dashboard** → Display course with Confluence pages

---

## Data Storage

### Config Files (`backend/onboarding/*.json`)

```json
{
  "id": "course-name",
  "name": "Readable Course Name",
  "emoji": "🚀",
  "color": "#36B37E",
  "settings": {
    "folder_recursion": true,
    "test_at_end": true
  },
  "instructions": "HTML instructions",
  "linked_pages": ["123456", "789012"],
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

---

## API Endpoints

### Config Management
- `GET /api/onboarding/configs` - List all configs
- `POST /api/onboarding/configs` - Create new config
- `GET /api/onboarding/configs/{id}` - Get config
- `PUT /api/onboarding/configs/{id}` - Update config
- `DELETE /api/onboarding/configs/{id}` - Delete config

### Course Data
- `GET /api/onboarding/course/{id}` - Get course with Confluence pages
- `GET /api/onboarding/summary/{id}` - AI summary (TODO)
- `GET /api/onboarding/quiz/{id}` - Generate quiz (TODO)

### Confluence
- `GET /api/confluence/page/{id}` - Fetch single page
- `GET /api/confluence/search?label=X` - Search by label

---

## Environment Variables

```env
CONFLUENCE_URL=https://company.atlassian.net/wiki
CONFLUENCE_USER_EMAIL=user@company.com
CONFLUENCE_API_TOKEN=your_token
ENVIRONMENT=development
```

---

## Why This Design?

### File-Based Storage
- ✅ No database setup required
- ✅ Easy to backup (copy folder)
- ✅ Git-friendly (version control configs)
- ✅ Human-readable JSON

### Monorepo Structure
- ✅ Everything in one place
- ✅ Shared dev environment
- ✅ Easy deployment

### Confluence Integration
- ✅ Single source of truth for docs
- ✅ Real-time updates
- ✅ No content duplication

---

## Future Enhancements

- [ ] OpenAI integration for summaries
- [ ] OpenAI integration for quiz generation
- [ ] Vector database for RAG
- [ ] User authentication
- [ ] Multi-tenant support
- [ ] Database migration (if needed at scale)

---

**Built for simplicity and maintainability** 🚀
