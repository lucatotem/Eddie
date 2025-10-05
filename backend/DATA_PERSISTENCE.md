# Data Persistence & Token Optimization

## 📁 Folder Structure

```
backend/
├── onboarding/
│   ├── *.json                  # Config files (committed to git)
│   ├── courses/               # AI-generated courses (NOT committed)
│   ├── quizzes/               # AI-generated quizzes (NOT committed)
│   └── processed/             # Processing metadata (NOT committed)
└── chroma_db/                  # Vector embeddings database (NOT committed)
```

## 💾 What Gets Saved

### 1. **Configuration Files** (`onboarding/*.json`)
- ✅ **Committed to git**
- Contains course metadata, settings, and linked pages
- Created/updated via Config Editor UI
- Example: `fullstack-dev.json`

### 2. **AI-Generated Courses** (`onboarding/courses/`)
- ❌ **NOT committed to git** (in `.gitignore`)
- Generated once per config creation/update
- Saved as `{course_id}.json`
- Contains:
  - Course modules with AI-generated content
  - Summaries, key points, takeaways
  - Markdown-formatted lessons

### 3. **AI-Generated Quizzes** (`onboarding/quizzes/`)
- ❌ **NOT committed to git** (in `.gitignore`)
- Generated once per config if `test_at_end: true`
- Saved as `{course_id}_final.json` or `{course_id}_module_{number}.json`
- Contains:
  - Multiple-choice questions
  - Correct answers and explanations
  - Difficulty level

### 4. **Processing Metadata** (`onboarding/processed/`)
- ❌ **NOT committed to git** (in `.gitignore`)
- Tracks which pages have been embedded
- Saved as `{course_id}.json`
- Contains:
  - Page IDs, titles, URLs
  - Version numbers for change detection
  - Processing timestamps

### 5. **Vector Embeddings** (`chroma_db/`)
- ❌ **NOT committed to git** (in `.gitignore`)
- ChromaDB persistent storage
- Contains Gemini embeddings for semantic search
- Automatically created on first course processing

## 🔄 When Content is Generated

### On Config Creation (POST `/configs`)
The system automatically:
1. ✅ Fetches all Confluence pages
2. ✅ Generates embeddings with Gemini
3. ✅ Generates AI course content (5 modules)
4. ✅ Generates final quiz (if `test_at_end: true`)

**Result:** Course is immediately ready to use!

### On Config Update (PUT `/configs/{id}`)
The system automatically:
1. ✅ Re-fetches all Confluence pages
2. ✅ Regenerates embeddings
3. ✅ Regenerates AI course content
4. ✅ Regenerates final quiz

**Result:** Course stays in sync with configuration changes!

### Manual Regeneration
You can force regeneration using:
- `POST /configs/{id}/generate-course?force=true`
- `POST /configs/{id}/generate-quiz` with `force: true` in body

## 💰 Token Optimization

### Why This Saves Tokens

1. **One-time Generation**
   - Courses and quizzes are generated ONCE
   - Subsequent requests load from JSON files
   - No repeated API calls to Gemini

2. **Persistent Between Restarts**
   - Files survive server restarts
   - No need to regenerate on deploy
   - Instant loading from disk

3. **Smart Regeneration**
   - Only regenerates when config changes
   - Can manually force if needed
   - Checks existence before generating

### Estimated Token Usage

Per course creation:
- **Embeddings:** ~100-500 tokens per page × number of pages
- **Course Generation:** ~2,000-5,000 tokens per module × 5 modules
- **Quiz Generation:** ~1,000-2,000 tokens per quiz

**Example:** A course with 10 pages might use:
- Initial: ~25,000-35,000 tokens
- Subsequent loads: **0 tokens** ✨

## 🔒 Git Strategy

### What's Committed
```
onboarding/
├── fullstack-dev.json     ✅ Config definitions
├── frontend-basics.json   ✅ Config definitions
└── .gitkeep              ✅ Keep folder structure
```

### What's Ignored
```
onboarding/
├── courses/              ❌ AI-generated (regenerate)
├── quizzes/              ❌ AI-generated (regenerate)
└── processed/            ❌ Processing cache
chroma_db/                ❌ Vector database (rebuild)
```

## 🚀 Deployment Strategy

### On New Environment
1. Clone repository (gets config files)
2. Install dependencies
3. Set environment variables (.env)
4. Start server
5. System auto-generates courses from configs

### On Updates
1. Pull latest config changes
2. System detects config updates
3. Auto-regenerates affected courses

## 📊 Monitoring Generation Status

Check if content exists:
```bash
# Check if course is generated
GET /api/onboarding/configs/{id}/generated-course

# Check processing status
GET /api/onboarding/configs/{id}/processing-status

# Check real-time progress
GET /api/onboarding/configs/{id}/progress
```

## 🧹 Cleanup

To regenerate all content from scratch:
```bash
# Remove all generated data
rm -rf onboarding/courses/
rm -rf onboarding/quizzes/
rm -rf onboarding/processed/
rm -rf chroma_db/

# Restart server - courses will auto-generate
```

## 🎯 Best Practices

1. **Config Files Only**
   - Commit only `onboarding/*.json` config files
   - Never commit generated content

2. **Local Development**
   - Generate courses once
   - They'll persist between restarts
   - Delete folders to force regeneration

3. **Production**
   - Let auto-generation handle everything
   - Monitor processing progress endpoint
   - Use force regeneration sparingly

4. **Version Control**
   - Track config changes in git
   - Generated content rebuilds automatically
   - No merge conflicts on generated files

---

**Summary:** Configs are committed, generated content is ephemeral but persistent. This saves tokens while keeping courses consistent and version-controlled! 🎉
