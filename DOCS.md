# 📋 Eddie Documentation Index

All the docs you need, organized by purpose.

---

## 🚀 Getting Started

**→ Start here: [README.md](./README.md)**
- Quick start guide
- How to create courses
- Troubleshooting tips
- All the essentials

---

## 🛠️ Scripts

### `setup.ps1`
One-time setup for Eddie
- Creates Python virtual environment
- Installs backend dependencies
- Installs frontend dependencies
- Copies .env template

**Run once:**
```powershell
.\setup.ps1
```

### `dev.ps1`
Start both backend and frontend servers
- Activates Python venv
- Starts FastAPI on port 8000
- Starts React on port 3000

**Run every time you work:**
```powershell
.\dev.ps1
```

### `test-confluence.ps1`
Test your Confluence integration
- Checks backend health
- Prompts for a page ID
- Tests page fetching
- Confirms if integration works

**Run to verify setup:**
```powershell
.\test-confluence.ps1
```

---

## 📚 Documentation

### [README.md](./README.md)
**Main documentation**
- Quick start
- How it works
- Project structure
- Troubleshooting
- Tips & tricks

### [ARCHITECTURE.md](./ARCHITECTURE.md)
**Technical details**
- System architecture
- Tech stack
- Data flow
- API endpoints
- Design decisions

### [CHANGELOG.md](./CHANGELOG.md)
**Version history**
- v3.0: File-based configs
- v2.0: Folder expansion
- v1.0: Initial release

---

## 🎯 Quick Reference

### First Time Setup
1. Run `.\setup.ps1`
2. Edit `backend\.env` with Confluence credentials
3. Run `.\dev.ps1`
4. Open http://localhost:3000

### Create a Course
1. Click "Create New Course"
2. Fill in name, emoji, instructions
3. Add Confluence page IDs
4. Save!

### Get a Confluence Page ID
1. Open any page in Confluence
2. Look at URL: `pages/123456/Title`
3. Copy the number: `123456`

### Test Confluence
```powershell
.\test-confluence.ps1
```
Enter a real page ID when prompted

---

## 🆘 Need Help?

**Backend won't start?**
→ See README.md → Troubleshooting → Backend

**Frontend won't start?**
→ See README.md → Troubleshooting → Frontend

**Confluence not working?**
1. Run `.\test-confluence.ps1`
2. Check `backend\.env` credentials
3. Verify page ID is correct

**Technical details?**
→ See ARCHITECTURE.md

**What changed?**
→ See CHANGELOG.md

---

## 📁 File Structure

```
Eddie/
├── README.md              ← Start here
├── ARCHITECTURE.md        ← Technical details
├── CHANGELOG.md           ← Version history
├── DOCS.md                ← This file
│
├── setup.ps1              ← One-time setup
├── dev.ps1                ← Start servers
├── test-confluence.ps1    ← Test integration
│
├── backend/               ← FastAPI server
│   ├── onboarding/       ← Config files (auto-created)
│   ├── app/              ← Source code
│   └── .env              ← Your credentials
│
└── frontend/              ← React app
    └── src/              ← Components
```

---

**Questions? Check README.md first, then ARCHITECTURE.md for deeper details.**
