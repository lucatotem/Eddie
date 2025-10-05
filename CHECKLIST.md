# Pre-Deployment Checklist

Use this checklist to verify your AI-powered onboarding system is ready for testing and deployment.

## ✅ Environment Setup

- [ ] Backend virtual environment activated
- [ ] All Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] `.env` file created with all required variables:
  - [ ] `GEMINI_API_KEY` set
  - [ ] `CONFLUENCE_URL` set (without `/wiki` suffix)
  - [ ] `CONFLUENCE_USER_EMAIL` set
  - [ ] `CONFLUENCE_API_TOKEN` set

## ✅ Backend Services

- [ ] Backend running on port 8000
- [ ] No startup errors in console
- [ ] API docs accessible at `http://localhost:8000/docs`
- [ ] Can ping backend: `curl http://localhost:8000/api/confluence/ping`
- [ ] Directory structure created:
  - [ ] `backend/onboarding/` exists
  - [ ] `backend/chroma_db/` exists (will be created on first use)

## ✅ Frontend Application

- [ ] Frontend running on port 5173
- [ ] No build errors in console
- [ ] Can access UI at `http://localhost:5173`
- [ ] Config Manager loads without errors
- [ ] API connection working (can see configs list)

## ✅ Confluence Integration

- [ ] Can fetch Confluence pages
- [ ] Test page ID works (e.g., 131472)
- [ ] API token has correct permissions
- [ ] No 403/404 errors when fetching pages

## ✅ Core Features

### Config Management
- [ ] Can create new config
- [ ] Can edit existing config
- [ ] Can delete config
- [ ] Configs persist to `onboarding/{id}.json`
- [ ] List view shows all configs

### Page Processing
- [ ] Creating config triggers background processing
- [ ] Processing status endpoint returns data
- [ ] Pages are fetched from Confluence
- [ ] Embeddings are generated
- [ ] Processing metadata saved to `onboarding/processed/{id}.json`
- [ ] ChromaDB collections created in `chroma_db/course_{id}/`

### Course Generation
- [ ] Can trigger course generation
- [ ] Gemini API generates modules
- [ ] Course saved to `onboarding/courses/{id}.json`
- [ ] Generated course has proper structure (modules, content, etc.)
- [ ] CourseViewer displays course correctly

### Quiz Generation
- [ ] Can generate quiz
- [ ] Quiz saved to `onboarding/quizzes/{id}_final.json`
- [ ] Quiz has questions with 4 options each
- [ ] Quiz interface displays correctly
- [ ] Can submit answers
- [ ] Results show with correct score

### Change Detection
- [ ] Check updates endpoint works
- [ ] Detects new pages
- [ ] Detects deleted pages
- [ ] Detects modified pages (version changes)
- [ ] Re-processing updates embeddings

## ✅ User Interface

### Config Manager
- [ ] Lists all configs
- [ ] "Create New Config" button works
- [ ] Can click config to view dashboard
- [ ] Responsive design works

### Config Editor
- [ ] All form fields editable
- [ ] Validation works (required fields)
- [ ] Can add/remove linked pages
- [ ] Settings toggles work
- [ ] Save triggers re-processing

### Dashboard
- [ ] Shows config details
- [ ] Displays linked pages
- [ ] "Take AI Course" button works
- [ ] "Edit Config" button works
- [ ] Page count accurate

### Course Viewer
- [ ] Full-screen mode works
- [ ] Module sidebar navigation
- [ ] Progress bar updates
- [ ] Content displays with markdown formatting
- [ ] Key points and takeaways show
- [ ] Next/Previous buttons work
- [ ] Can close viewer
- [ ] Update banner shows when changes detected

### Quiz Interface
- [ ] Question navigation grid works
- [ ] Can select answers for all questions
- [ ] Progress tracking accurate
- [ ] Submit button enables when all answered
- [ ] Results page displays
- [ ] Score circle animates
- [ ] Question breakdown shows
- [ ] Explanations visible
- [ ] Retry button works

## ✅ Data Persistence

- [ ] Configs saved and reload correctly
- [ ] Processing status persists
- [ ] Generated courses persist
- [ ] Generated quizzes persist
- [ ] Vector embeddings persist in ChromaDB
- [ ] Delete operation cleans up all files:
  - [ ] Config file deleted
  - [ ] Processing metadata deleted
  - [ ] Generated course deleted
  - [ ] Generated quiz deleted
  - [ ] ChromaDB collection deleted

## ✅ Error Handling

- [ ] Missing Gemini API key shows helpful error
- [ ] Invalid Confluence credentials show error
- [ ] Page not found errors handled gracefully
- [ ] Network errors show user-friendly messages
- [ ] Loading states display during operations
- [ ] Background task failures logged

## ✅ Performance

- [ ] Page processing completes in reasonable time (~2-5s per page)
- [ ] Course generation completes in 30-60 seconds
- [ ] Quiz generation completes in 20-30 seconds
- [ ] UI remains responsive during background tasks
- [ ] No memory leaks during extended use
- [ ] Vector search returns results quickly (<1s)

## ✅ API Endpoints

Test each endpoint:

### Config CRUD
- [ ] `GET /api/onboarding/configs`
- [ ] `POST /api/onboarding/configs`
- [ ] `GET /api/onboarding/configs/{id}`
- [ ] `PUT /api/onboarding/configs/{id}`
- [ ] `DELETE /api/onboarding/configs/{id}`

### Processing
- [ ] `GET /api/onboarding/configs/{id}/processing-status`
- [ ] `GET /api/onboarding/configs/{id}/check-updates`
- [ ] `POST /api/onboarding/configs/{id}/reprocess`

### Course Generation
- [ ] `POST /api/onboarding/configs/{id}/generate-course`
- [ ] `GET /api/onboarding/configs/{id}/generated-course`

### Quiz
- [ ] `POST /api/onboarding/configs/{id}/generate-quiz`
- [ ] `GET /api/onboarding/configs/{id}/quiz`
- [ ] `POST /api/onboarding/configs/{id}/quiz/submit`

### Confluence
- [ ] `GET /api/confluence/page/{id}`
- [ ] `GET /api/confluence/search?label=X`
- [ ] `GET /api/confluence/ping`

## ✅ Documentation

- [ ] README.md up to date
- [ ] TESTING.md created with test scenarios
- [ ] QUICKSTART.md created with system overview
- [ ] IMPLEMENTATION_SUMMARY.md created
- [ ] ARCHITECTURE.md exists
- [ ] Code comments are clear

## ✅ Security

- [ ] `.env` file in `.gitignore`
- [ ] No API keys committed to git
- [ ] Confluence credentials secure
- [ ] Input validation on all endpoints
- [ ] File paths sanitized

## ✅ Browser Compatibility

- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Edge
- [ ] Works in Safari
- [ ] Mobile responsive

## ✅ Final Verification

Run through complete user journey:

1. [ ] Create new course config
2. [ ] Wait for processing to complete
3. [ ] Generate AI course
4. [ ] Navigate through all modules
5. [ ] Generate quiz
6. [ ] Take quiz and submit
7. [ ] View results
8. [ ] Edit a Confluence page
9. [ ] See update notification
10. [ ] Re-process course
11. [ ] Regenerate course with updated content
12. [ ] Delete config and verify cleanup

## 📊 Testing Results

### Performance Benchmarks
- Average page processing time: _____ seconds
- Course generation time (5 modules): _____ seconds
- Quiz generation time (5 questions): _____ seconds
- Vector search response time: _____ ms

### Resource Usage
- Backend memory usage: _____ MB
- Frontend bundle size: _____ MB
- ChromaDB storage per course: _____ MB
- Total disk space used: _____ MB

### Test Statistics
- Total configs tested: _____
- Total pages processed: _____
- Total courses generated: _____
- Total quizzes generated: _____
- Total quiz submissions: _____

## 🐛 Known Issues

Document any issues found during testing:

1. _____________________________________
2. _____________________________________
3. _____________________________________

## ✅ Deployment Readiness

Final check before deployment:

- [ ] All tests passing
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Environment variables documented
- [ ] Backup strategy in place
- [ ] Monitoring configured (optional)
- [ ] Error logging working
- [ ] User training material prepared (optional)

## 🚀 Ready for Deployment!

Once all items are checked:

- [ ] System is ready for production use
- [ ] Team has been trained
- [ ] Support process established
- [ ] Rollback plan in place

---

**Sign-off**:

- Tested by: _____________________
- Date: _____________________
- Status: _____ PASS / FAIL
- Notes: _____________________

---

## Quick Test Commands

```bash
# Backend health check
curl http://localhost:8000/api/confluence/ping

# List configs
curl http://localhost:8000/api/onboarding/configs

# Check processing status
curl http://localhost:8000/api/onboarding/configs/{id}/processing-status

# Check for updates
curl http://localhost:8000/api/onboarding/configs/{id}/check-updates
```

---

**Good luck with your deployment!** 🎉
