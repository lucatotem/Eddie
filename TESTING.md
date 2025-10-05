# End-to-End Testing Guide

This guide walks through testing the complete AI-powered onboarding system.

## Prerequisites

1. **Backend Running**: `python -m uvicorn app.main:app --reload` (port 8000)
2. **Frontend Running**: `npm run dev` (port 5173)
3. **Environment Variables Set**:
   - `GEMINI_API_KEY` - Your Google Gemini API key
   - `CONFLUENCE_URL` - Your Confluence instance URL
   - `CONFLUENCE_USER_EMAIL` - Your Confluence email
   - `CONFLUENCE_API_TOKEN` - Your Confluence API token

## Test Flow

### 1. Create an Onboarding Course Config

**Goal**: Create a new course configuration with Confluence pages

**Steps**:
1. Open the frontend (http://localhost:5173)
2. Click "Create New Config" button
3. Fill in the form:
   - **Name**: "Backend Developer Onboarding"
   - **Title**: "Welcome to Backend Development"
   - **Description**: "Learn our backend architecture, APIs, and best practices"
   - **Emoji**: 🚀
   - **Linked Pages**: Add your Confluence page IDs (e.g., 131472)
   - **Settings**:
     - ✅ Enable folder recursion (if pages have children)
     - ✅ Enable test at end
4. Click "Create Config"

**Expected Result**:
- Config appears in the list
- Background processing starts automatically
- Processing status shows in backend logs

**Backend Logs to Check**:
```
[CourseProcessor] Processing course: Backend Developer Onboarding (...)
[CourseProcessor] Fetching all Confluence pages...
[VectorStore] Generating embeddings...
✓ Successfully embedded
```

---

### 2. Monitor Page Processing & Embedding

**Goal**: Verify Confluence pages are fetched and embedded into vector database

**Steps**:
1. Click on your newly created config
2. Click "🎓 Take AI Course" button
3. Observe the processing status

**Expected Result**:
- Shows "⏳ Processing Content" if still embedding
- Shows "✓ Content Processed" when complete with page count

**API Check**:
```bash
# Check processing status
curl http://localhost:8000/api/onboarding/configs/{config-id}/processing-status
```

**Expected Response**:
```json
{
  "course_id": "...",
  "total_pages": 5,
  "processed_pages": 5,
  "failed_pages": 0,
  "processed_time": "2025-10-05T10:30:00",
  "processed_pages": [...]
}
```

**Vector Database Check**:
- Check `backend/chroma_db/` folder exists
- Collections created for each course

---

### 3. Generate AI Course Content

**Goal**: Use Gemini AI to generate interactive course modules from embedded content

**Steps**:
1. After processing completes, you'll see "Generate AI Course" UI
2. Select number of modules (try 5 modules)
3. Click "✨ Generate Course"
4. Wait 30-60 seconds for AI generation

**Expected Result**:
- Spinner shows "AI is creating your course modules..."
- Course appears with module structure
- Each module has:
  - Title and description
  - Overview section
  - Main content (markdown formatted)
  - Key points
  - Takeaways

**API Check**:
```bash
# Trigger generation
curl -X POST http://localhost:8000/api/onboarding/configs/{config-id}/generate-course?num_modules=5

# Check generated course
curl http://localhost:8000/api/onboarding/configs/{config-id}/generated-course
```

**File Check**:
- Generated course saved to `backend/onboarding/courses/{config-id}.json`

---

### 4. Navigate Through Course Modules

**Goal**: Test the interactive course viewer

**Steps**:
1. Course viewer should open automatically after generation
2. Test navigation:
   - Click modules in sidebar to jump
   - Use "Next Module →" button
   - Use "← Previous" button
   - Check progress bar updates
3. Verify content display:
   - Markdown formatting works (bold, code, lists)
   - Key points show with 🔑 icons
   - Takeaways show with 💡 icons
4. Complete all modules

**Expected Result**:
- Smooth navigation between modules
- Progress bar shows completion percentage
- Completed modules marked with ✓
- "Take Final Quiz" button appears on last module

---

### 5. Generate and Take Final Quiz

**Goal**: Test AI quiz generation and interactive quiz interface

**Steps**:
1. Click "Take Final Quiz →" on last module
2. If quiz not generated yet:
   - Select 5 questions, medium difficulty
   - Click "✨ Generate Quiz"
   - Wait 20-30 seconds
3. Take the quiz:
   - Answer all questions (select options A/B/C/D)
   - Navigation: Use numbered buttons to jump between questions
   - Check progress: See "X answered" count
4. Submit quiz when all questions answered

**Expected Result**:
- Quiz UI shows with question navigation grid
- Each question has 4 options
- Visual feedback when selecting answers
- Can navigate freely between questions
- Submit button enabled when all answered

**API Check**:
```bash
# Generate quiz
curl -X POST http://localhost:8000/api/onboarding/configs/{config-id}/generate-quiz \
  -H "Content-Type: application/json" \
  -d '{"num_questions": 5, "difficulty": "medium"}'

# Get quiz (answers hidden)
curl http://localhost:8000/api/onboarding/configs/{config-id}/quiz

# Submit answers
curl -X POST http://localhost:8000/api/onboarding/configs/{config-id}/quiz/submit \
  -H "Content-Type: application/json" \
  -d '{"answers": [0, 2, 1, 3, 0]}'
```

**File Check**:
- Quiz saved to `backend/onboarding/quizzes/{config-id}_final.json`

---

### 6. Review Quiz Results

**Goal**: Verify quiz grading and feedback system

**Steps**:
1. After submission, view results page
2. Check score display:
   - Animated circular progress
   - Percentage score
   - Pass/Fail status (70% threshold)
3. Review breakdown:
   - Each question marked correct/incorrect
   - See your answer vs correct answer
   - Read AI explanations

**Expected Result**:
- Score calculated correctly
- Visual distinction between correct (green) and incorrect (orange)
- Detailed explanations for all answers
- Option to retake quiz or continue

---

### 7. Test Change Detection

**Goal**: Verify the system detects when Confluence pages are updated

**Steps**:
1. Edit a Confluence page that's part of your course
2. In the course viewer, the system auto-checks for updates
3. If updates detected, see orange banner:
   - "🔄 Content Updates Available"
   - Shows number of changes
4. Click "Re-process Course" button
5. Wait for re-processing to complete

**API Check**:
```bash
# Check for updates
curl http://localhost:8000/api/onboarding/configs/{config-id}/check-updates
```

**Expected Response**:
```json
{
  "needs_update": true,
  "reason": "1 updated page(s)",
  "changed_pages": [{
    "page_id": "131472",
    "title": "Backend Setup",
    "old_version": 5,
    "new_version": 6
  }],
  "new_pages": [],
  "deleted_pages": [],
  "total_changes": 1
}
```

**Expected Result**:
- System detects version changes
- Re-processing updates embeddings
- Generated course can be regenerated with new content

---

### 8. Test Update/Delete Operations

**Goal**: Verify CRUD operations work correctly

**Steps**:
1. **Update Config**:
   - Click "✏️ Edit Config" in dashboard
   - Modify title or add pages
   - Save changes
   - Verify re-processing starts
   
2. **Delete Config**:
   - Delete a test config
   - Verify all data cleaned up:
     - Vector embeddings deleted
     - Processing metadata removed
     - Generated course removed
     - Generated quiz removed

**Expected Result**:
- Updates trigger re-processing
- Deletes clean up all associated files
- No orphaned data left behind

---

## Test Checklist

- [ ] Create course config with Confluence pages
- [ ] Pages are fetched and embedded successfully
- [ ] Processing status shows correct page count
- [ ] AI generates course with multiple modules
- [ ] Course viewer displays all content correctly
- [ ] Module navigation works smoothly
- [ ] Progress tracking updates properly
- [ ] AI generates quiz with questions
- [ ] Quiz interface allows answering all questions
- [ ] Quiz submission calculates score correctly
- [ ] Results show detailed feedback
- [ ] Change detection identifies updated pages
- [ ] Re-processing updates embeddings
- [ ] Update config triggers re-processing
- [ ] Delete config cleans up all data

---

## Common Issues & Solutions

### Issue: "GEMINI_API_KEY not set"
**Solution**: Add to `backend/.env` file
```env
GEMINI_API_KEY=your_api_key_here
```

### Issue: Confluence 404 errors
**Solution**: 
- Verify page IDs are correct
- Check Confluence URL doesn't have `/wiki` suffix
- Ensure API token has access to pages

### Issue: Processing stuck/fails
**Solution**:
- Check backend logs for errors
- Verify ChromaDB folder has write permissions
- Ensure enough disk space for embeddings

### Issue: Course generation fails
**Solution**:
- Verify pages were processed first
- Check Gemini API quota/rate limits
- Review backend logs for API errors

### Issue: Quiz not generating
**Solution**:
- Ensure course was generated first
- Check Gemini API key is valid
- Verify enough content exists for quiz questions

---

## Performance Benchmarks

**Expected Timings** (varies by content size):
- Page processing: ~2-5 seconds per page
- Embedding generation: ~1-2 seconds per page
- Course generation (5 modules): ~30-60 seconds
- Quiz generation (5 questions): ~20-30 seconds

**Resource Usage**:
- ChromaDB storage: ~1-5 MB per course
- Memory: ~200-500 MB during processing
- API calls: 1 embedding call per text chunk, 1 generation call per module/quiz

---

## Success Criteria

✅ **System is working if**:
1. Confluence pages are fetched without errors
2. Vector embeddings are created and searchable
3. AI generates coherent, relevant course content
4. Quiz questions test understanding of material
5. Change detection identifies page updates
6. All CRUD operations work correctly
7. Background processing completes without blocking

🎉 **Congratulations!** You have a fully functional AI-powered onboarding system!

---

## Next Steps

After successful testing:
1. Add more course configurations
2. Customize module count for different topics
3. Experiment with difficulty levels for quizzes
4. Monitor Gemini API usage and costs
5. Set up automated re-processing schedules
6. Add user progress tracking (future enhancement)
7. Implement course completion certificates (future enhancement)
