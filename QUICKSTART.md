# Eddie - AI-Powered Confluence Onboarding System

## Quick Start Guide

### System Overview

Eddie transforms your Confluence documentation into interactive, AI-powered onboarding courses with:
- 🤖 **AI Course Generation** - Gemini 2.0 Flash Lite creates engaging learning modules
- 📚 **Vector Search** - Semantic search using ChromaDB and Gemini embeddings
- 📝 **Smart Quizzes** - AI-generated assessments with detailed explanations
- 🔄 **Change Detection** - Automatically detects when Confluence pages are updated
- 📊 **Progress Tracking** - Visual progress through modules

---

## Architecture

```
Frontend (React + Vite)
    ↓
FastAPI Backend
    ↓
    ├── Confluence API → Fetch pages
    ├── Gemini Embeddings → Vector DB (ChromaDB)
    ├── Gemini 2.0 Flash Lite → Generate courses & quizzes
    └── File Storage → Save configs, courses, quizzes
```

---

## Key Components

### Backend Services

1. **`confluence_service.py`** - Fetch pages from Confluence
   - Get pages by ID
   - Expand folders recursively
   - Track page versions

2. **`vector_store.py`** - Semantic search with embeddings
   - Gemini text-embedding-004 (768 dimensions)
   - ChromaDB for persistent storage
   - HTML stripping and text chunking

3. **`course_processor.py`** - Orchestrate page processing
   - Fetch → Embed → Store metadata
   - Change detection
   - Re-processing triggers

4. **`gemini_service.py`** - AI content generation
   - Course module generation
   - Quiz question generation
   - Answer grading with explanations

5. **`config_storage.py`** - File-based config management
   - CRUD operations
   - JSON file storage

### Frontend Components

1. **`ConfigManager.jsx`** - Browse and select courses
2. **`ConfigEditor.jsx`** - Create/edit course configs
3. **`Dashboard.jsx`** - View course details
4. **`CourseViewer.jsx`** - Interactive course interface
5. **`Quiz.jsx`** - Quiz taking and results

---

## Data Flow

### 1. Create Course Config
```
User → ConfigEditor → POST /api/onboarding/configs
    ↓
Backend saves to onboarding/{id}.json
    ↓
BackgroundTask: course_processor.process_course()
```

### 2. Process Pages
```
Fetch Confluence pages → Extract content → Strip HTML
    ↓
Generate embeddings (Gemini) → Chunk text
    ↓
Store in ChromaDB (collection: course_{id})
    ↓
Save metadata to onboarding/processed/{id}.json
```

### 3. Generate Course
```
User → CourseViewer → POST /api/onboarding/configs/{id}/generate-course
    ↓
Vector search → Retrieve relevant chunks
    ↓
Gemini generates module structure → Content for each module
    ↓
Save to onboarding/courses/{id}.json
```

### 4. Generate Quiz
```
User → Quiz → POST /api/onboarding/configs/{id}/generate-quiz
    ↓
Load generated course → Vector search for context
    ↓
Gemini generates questions with options & explanations
    ↓
Save to onboarding/quizzes/{id}_final.json
```

### 5. Take & Grade Quiz
```
User answers → POST /api/onboarding/configs/{id}/quiz/submit
    ↓
Compare answers to correct answers
    ↓
Calculate score → Generate feedback
    ↓
Return results with explanations
```

---

## API Endpoints

### Config Management
- `GET /api/onboarding/configs` - List all configs
- `POST /api/onboarding/configs` - Create new config
- `GET /api/onboarding/configs/{id}` - Get config
- `PUT /api/onboarding/configs/{id}` - Update config
- `DELETE /api/onboarding/configs/{id}` - Delete config

### Processing & Status
- `GET /api/onboarding/configs/{id}/processing-status` - Check embedding status
- `GET /api/onboarding/configs/{id}/check-updates` - Check for page changes
- `POST /api/onboarding/configs/{id}/reprocess` - Trigger re-processing

### Course Generation
- `POST /api/onboarding/configs/{id}/generate-course` - Generate AI course
- `GET /api/onboarding/configs/{id}/generated-course` - Get generated course

### Quiz Generation
- `POST /api/onboarding/configs/{id}/generate-quiz` - Generate quiz
- `GET /api/onboarding/configs/{id}/quiz` - Get quiz (answers hidden)
- `POST /api/onboarding/configs/{id}/quiz/submit` - Submit answers for grading

### Legacy (Backwards Compatibility)
- `GET /api/onboarding/course/{id}` - Get course with Confluence pages
- `GET /api/onboarding/summary/{id}` - Get course summary
- `GET /api/onboarding/quiz/{id}` - Generate quiz (old format)

---

## File Structure

```
backend/
├── onboarding/          # Course configs
│   ├── {id}.json        # Config files
│   ├── processed/       # Processing metadata
│   │   └── {id}.json
│   ├── courses/         # Generated courses
│   │   └── {id}.json
│   └── quizzes/         # Generated quizzes
│       ├── {id}_final.json
│       └── {id}_module_{n}.json
├── chroma_db/           # Vector database
│   └── course_{id}/     # Collections per course
└── app/
    ├── services/        # Business logic
    ├── api/             # API routes
    └── models/          # Data models

frontend/
└── src/
    ├── components/      # React components
    └── services/        # API client
```

---

## Configuration

### Environment Variables (`backend/.env`)

```env
# Required
GEMINI_API_KEY=your_gemini_api_key
CONFLUENCE_URL=https://yourcompany.atlassian.net
CONFLUENCE_USER_EMAIL=your_email@company.com
CONFLUENCE_API_TOKEN=your_confluence_token

# Optional
OPENAI_API_KEY=  # Not used, legacy
```

### Course Config Schema

```json
{
  "id": "unique-id",
  "name": "Backend Onboarding",
  "title": "Welcome to Backend",
  "description": "Learn our stack",
  "emoji": "🚀",
  "linked_pages": ["131472", "131473"],
  "settings": {
    "folder_recursion": true,
    "test_at_end": true
  },
  "created_at": "2025-10-05T10:00:00",
  "updated_at": "2025-10-05T10:00:00"
}
```

---

## Key Features

### 1. Vector Search
- **Model**: Gemini text-embedding-004
- **Dimensions**: 768
- **Chunk Size**: 500 characters with 50 char overlap
- **Task Types**: 
  - `retrieval_document` for storing
  - `retrieval_query` for searching

### 2. Course Generation
- **Model**: Gemini 2.0 Flash Lite
- **Modules**: 3-10 (configurable)
- **Content**: Overview, main content, key points, takeaways
- **Format**: Markdown with rich formatting

### 3. Quiz Generation
- **Questions**: 3-10 (configurable)
- **Difficulty**: Easy, Medium, Hard
- **Format**: Multiple choice (4 options)
- **Features**: Explanations, grading, retry option

### 4. Change Detection
- **Method**: Confluence version numbers
- **Checks**: New, deleted, and modified pages
- **Actions**: One-click re-processing

---

## Development

### Running the System

**Backend**:
```bash
cd backend
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
python -m uvicorn app.main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

### Adding Features

1. **New API endpoint**: Add to `backend/app/api/onboarding.py`
2. **New service**: Create in `backend/app/services/`
3. **New component**: Create in `frontend/src/components/`
4. **New API method**: Add to `frontend/src/services/api.js`

---

## Troubleshooting

### Common Issues

1. **ChromaDB errors**
   - Solution: Delete `chroma_db/` folder and re-process

2. **Gemini API quota**
   - Solution: Check API console, upgrade quota if needed

3. **Confluence 403/404**
   - Solution: Verify page IDs, check API token permissions

4. **Empty course content**
   - Solution: Ensure pages were processed first, check embeddings exist

---

## Performance Tips

1. **Batch processing**: Process multiple pages at once
2. **Caching**: Reuse generated courses unless content changed
3. **Lazy loading**: Only generate quizzes when needed
4. **Incremental updates**: Use change detection vs full re-processing

---

## Future Enhancements

- [ ] User progress tracking
- [ ] Course completion certificates
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Role-based course recommendations
- [ ] Scheduled re-processing
- [ ] Course templates
- [ ] Custom quiz question bank

---

## Support

For issues or questions:
1. Check `TESTING.md` for detailed testing guide
2. Review `ARCHITECTURE.md` for system design
3. Check backend logs for error details
4. Verify all environment variables are set

---

**Built with**: FastAPI • React • Gemini AI • ChromaDB • Confluence API
