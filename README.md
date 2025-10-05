# Eddie - Confluence Onboarding Platform# Eddie - Confluence Onboarding Platform# Eddie - Confluence Onboarding Platform



> Making onboarding suck less, one new hire at a time



**Built with FastAPI + React | File-based configs | Zero database required**> AI-powered onboarding that doesn't make new hires cry> Making onboarding suck less, one new hire at a time



---



## 🚀 Quick Start**Built with FastAPI + React | File-based configs | Zero database required**## 🎉 NEW: File-Based Config System



### 1. Setup (One Time)

```powershell

.\setup.ps1---**Eddie now uses file-based configs instead of Confluence labels!**

```



### 2. Configure Confluence

Edit `backend\.env`:## 🚀 Quick Start- ✅ Create courses right in the UI

```env

CONFLUENCE_URL=https://your-company.atlassian.net- ✅ Save and reuse configurations

CONFLUENCE_USER_EMAIL=your.email@company.com

CONFLUENCE_API_TOKEN=your_api_token### 1. Setup (One-time)- ✅ Per-course settings (folder recursion, quizzes, etc.)

```

```powershell- ✅ No more manual Confluence page setup

**Get API Token**: https://id.atlassian.com/manage-profile/security/api-tokens

.\setup.ps1

⚠️ **IMPORTANT**: URL should be `https://company.atlassian.net` (**NO** `/wiki` at the end!)

```**👉 See [QUICK_START.md](./QUICK_START.md) for the new workflow**

### 3. Run Both Servers

```powershell

.\dev.ps1

```### 2. Run Both Servers**👉 Full details in [CONFIG_FILE_SYSTEM.md](./CONFIG_FILE_SYSTEM.md)**



Then open: **http://localhost:3000**```powershell



---.\dev.ps1---



## 📝 How to Create a Course```



1. Click **"Create New Course"**## What is this?

2. Fill in:

   - **Name**: e.g., "Backend Developer Onboarding"### 3. Open the App

   - **Emoji & Color**: Pick visuals for the course card

   - **Settings**:- **Frontend**: http://localhost:3000Eddie is an AI-powered onboarding tool that pulls from your Confluence documentation and serves it up in a way that doesn't make new hires want to cry. 

     - ✅ Folder Recursion (auto-include child pages)

     - ✅ Quiz at End (show quiz after modules)- **Backend API**: http://localhost:8000

   - **Instructions**: What should new hires learn?

   - **Linked Pages**: Paste Confluence page URLs (see below)- **API Docs**: http://localhost:8000/docsBuilt with FastAPI (backend) and React (frontend) because apparently that's what the cool kids are using these days.

3. Save!



---

### 4. Configure Confluence## Project Structure

## 🔗 Adding Confluence Pages

Edit `backend/.env`:

### ✅ Recommended: Paste Full URL

``````env```

https://company.atlassian.net/wiki/spaces/DEV/pages/123456/Page-Title

```CONFLUENCE_URL=https://your-company.atlassian.net/wikiEddie/

We automatically extract the page ID!

CONFLUENCE_USER_EMAIL=your.email@company.com├── backend/           # FastAPI server

### ✅ Alternative: Just the Page ID

```CONFLUENCE_API_TOKEN=your_api_token_here│   ├── onboarding/   # 📁 NEW: Config files stored here

123456

``````│   ├── app/

Also works!

│   │   ├── api/      # API endpoints

### How to Get a URL

1. Open any page in ConfluenceGet your API token: https://id.atlassian.com/manage-profile/security/api-tokens│   │   ├── models/   # 📁 NEW: Config schemas

2. Copy the URL from your browser

3. Paste it into Eddie│   │   ├── services/ # Business logic



------│   │   └── main.py   # App entry point



## 🔐 Confluence Access & Permissions│   ├── requirements.txt



### Which Spaces Can Eddie Access?## 📚 How It Works│   └── .env.example

**All spaces that YOU can access** with your Confluence account!

│

Your API token inherits your personal permissions. If you can see a page in Confluence, Eddie can fetch it.

### Create a Course├── frontend/          # React app

### Do I Need Special Setup for Each Space?

**No!** Eddie automatically has access to all your spaces. No configuration needed.1. Go to http://localhost:3000│   ├── src/



### Troubleshooting Access Issues2. Click **"Create New Course"**│   │   ├── components/



**Pages won't load?** Check:3. Fill in:│   │   │   ├── ConfigManager.jsx  # 📁 NEW: Home screen

1. ✅ URL in `.env` is `https://company.atlassian.net` (NO `/wiki`)

2. ✅ Page IDs are correct   - Name, emoji, color│   │   │   ├── ConfigEditor.jsx   # 📁 NEW: Create/edit UI

3. ✅ You have access to those pages in Confluence (log in and verify)

4. ✅ API token is valid and not expired   - Settings (folder recursion, quiz)│   │   │   └── Dashboard.jsx



**Test your connection:**   - Instructions (what new hires learn)│   │   ├── services/

```powershell

.\test-confluence.ps1   - Linked pages (Confluence page IDs)│   │   └── App.jsx

```

4. Save!│   ├── package.json

---

│   └── vite.config.js

## 📁 Project Structure

### Get Confluence Page IDs│

```

Eddie/1. Open any page in Confluence└── README.md         # You are here

├── backend/

│   ├── onboarding/          # Course configs (auto-created)2. Look at URL: `https://company.atlassian.net/wiki/pages/123456/Title````

│   ├── app/

│   │   ├── api/            # REST endpoints3. Copy the number: `123456`

│   │   ├── models/         # Config schemas

│   │   ├── services/       # Confluence + storage## Quick Start

│   │   └── main.py

│   └── .env                # YOUR Confluence credentials### Settings Explained

│

├── frontend/- **Folder Recursion**: Link a parent page → auto-includes all children**🚀 Both servers are already running!**

│   └── src/

│       ├── components/     # ConfigManager, Editor, Dashboard- **Quiz at End**: Show/hide quiz after course completion- Frontend: http://localhost:3000

│       └── services/       # API client

│- Backend: http://localhost:8000

├── setup.ps1               # One-time setup

├── dev.ps1                 # Start both servers---- API Docs: http://localhost:8000/docs

├── test-confluence.ps1     # Test connection

└── README.md               # You are here

```

## 📁 Project Structure**First time?** See [QUICK_START.md](./QUICK_START.md)

---



## 🧪 Testing Confluence Integration

```---

### Quick Test

```powershellEddie/

.\test-confluence.ps1

```├── backend/### Setup From Scratch



### Manual Test│   ├── onboarding/          # Course config files (auto-created)

Open in browser:

```│   ├── app/**Easy mode:** Run the setup script

http://localhost:8000/api/confluence/page/YOUR_PAGE_ID

```│   │   ├── api/            # REST endpoints```powershell



Replace `YOUR_PAGE_ID` with a real page ID from your Confluence.│   │   ├── models/         # Config schemas.\setup.ps1



---│   │   ├── services/       # Confluence + file storage```



## 🔧 Troubleshooting│   │   └── main.py



### "No source pages" Error│   └── .env                # Your Confluence credentialsThen follow the instructions it prints out.



**Cause**: Pages can't be loaded from Confluence│



**Fix**:├── frontend/### Manual Setup (if you like doing things the hard way)

1. Check backend terminal for error messages (look for `404` errors)

2. Verify `.env` URL is `https://company.atlassian.net` (NO `/wiki`)│   └── src/

3. Run `.\test-confluence.ps1` to test connection

4. Make sure you have access to the pages in Confluence│       ├── components/     # ConfigManager, ConfigEditor, Dashboard#### Backend

5. Check page IDs are correct

│       └── services/       # API client

### Backend Won't Start

```powershell│```powershell

cd backend

.\venv\Scripts\Activate.ps1├── setup.ps1              # One-time setupcd backend

pip install -r requirements.txt

uvicorn app.main:app --reload├── dev.ps1                # Start both servers

```

├── test-confluence.ps1    # Test Confluence connection# Create virtual environment (do this or suffer dependency hell)

### Frontend Won't Start

```powershell└── README.md              # You are herepython -m venv venv

cd frontend

npm install```.\venv\Scripts\activate

npm run dev

```



### Invalid API Token---# Install dependencies

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens

2. Create a new tokenpip install -r requirements.txt

3. Update `backend\.env` with new token

4. Restart backend## 🧪 Testing Confluence



---# Copy env file and add your Confluence credentials



## 📖 FeaturesRun the test script:copy .env.example .env



✅ **File-Based Configs** - No database required  ```powershell# Edit .env with your actual credentials

✅ **UI-Driven** - Create courses in browser  

✅ **URL Parsing** - Paste full Confluence URLs  .\test-confluence.ps1

✅ **Folder Expansion** - Auto-include child pages  

✅ **Per-Course Settings** - Customize each course  ```# Run the server

✅ **Confluence Integration** - Real-time doc fetching  

✅ **AI-Ready** - Prepared for OpenAI integration  uvicorn app.main:app --reload



---It will:```



## 📚 Documentation1. Check backend health



- **[DOCS.md](./DOCS.md)** - Documentation index2. Prompt for a Confluence page IDBackend will be running at `http://localhost:8000`

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical details

- **[CHANGELOG.md](./CHANGELOG.md)** - Version history3. Try to fetch the page



---4. Confirm if integration works#### Frontend



## 💡 Tips



- **Paste Full URLs**: Easier than finding page IDs manually---```powershell

- **Folder Recursion**: Link to a parent page, get all children automatically

- **Version Control**: Commit `onboarding/*.json` to share courses with your teamcd frontend

- **Backup**: Just copy the `onboarding/` folder

- **Edit Anytime**: Use the UI to update courses on the fly## 🛠️ Manual Setup (if setup.ps1 fails)



---# Install dependencies



## 🎯 Next Steps### Backendnpm install



1. ✅ Run `.\setup.ps1````powershell

2. ✅ Configure `backend\.env`

3. ✅ Run `.\dev.ps1`cd backend# Copy env file (optional, has defaults)

4. ✅ Create your first course at http://localhost:3000

5. 🔜 Add OpenAI API key for AI summaries (optional)python -m venv venvcopy .env.example .env



---.\venv\Scripts\Activate.ps1



**Made with ❤️  by developers who hate reading 47 Confluence pages on day one** 😄pip install -r requirements.txt# Run dev server


Copy-Item .env.example .envnpm run dev

# Edit .env with your Confluence credentials```

uvicorn app.main:app --reload

```Frontend will be running at `http://localhost:3000`



### Frontend## How to Use

```powershell

cd frontendInstead of hardcoded roles, Eddie uses **dynamic, admin-created courses**:

npm install

npm run dev1. **In Confluence**, create a page with onboarding instructions (e.g., "Dev Onboarding")

```2. **In that page**, link to the actual learning material (e.g., "backend-overview", "frontend-overview")

3. **Label it** with `onboarding-config`

---4. **Eddie automatically** picks it up and creates a course



## 📖 Key Features### Detailed Setup



✅ **File-Based Configs** - No database, just JSON files  See **[USER_GUIDE.md](./USER_GUIDE.md)** for complete instructions on creating courses.

✅ **UI-Driven** - Create/edit courses in the browser  

✅ **Folder Expansion** - Link a parent, get all children  **Quick example:**

✅ **Per-Course Settings** - Customize each onboarding type  ```

✅ **Confluence Integration** - Pull real docs from your wiki  Your "Dev Onboarding" page (labeled: onboarding-config):

✅ **AI-Ready** - Prepared for OpenAI summaries & quizzes  - Instructions: "Learn our backend and frontend"

- Links to: backend-overview page

---- Links to: frontend-overview page



## 📝 Config File ExampleEddie will:

- Show "Dev Onboarding" as a course

Stored in `backend/onboarding/{course-id}.json`:- Pull content from both linked pages

- Generate summaries and quizzes from the combined content

```json```

{

  "id": "backend-dev",## Features

  "name": "Backend Developer Onboarding",

  "emoji": "🚀",- ✅ Role-based content filtering

  "color": "#36B37E",- ✅ Confluence integration

  "settings": {- 🚧 AI summaries (placeholder for now)

    "folder_recursion": true,- 🚧 Quiz generation (TODO)

    "test_at_end": true- 🚧 Progress tracking (on the list)

  },

  "instructions": "Learn our FastAPI architecture and best practices",## API Documentation

  "linked_pages": ["123456", "789012"],

  "created_at": "2025-10-05T10:00:00",Once the backend is running, check out:

  "updated_at": "2025-10-05T10:00:00"- Interactive docs: `http://localhost:8000/docs`

}- Alternative docs: `http://localhost:8000/redoc`

```

## Development Notes

---

This is set up as a monorepo but backend and frontend are completely separate. You can deploy them independently if needed.

## 🔧 Troubleshooting

The AI features currently return mock data. To enable real AI:

### Backend won't start?1. Get an OpenAI API key

```powershell2. Uncomment the openai dependency in requirements.txt

cd backend3. Actually implement the AI calls (see TODOs in the code)

.\venv\Scripts\Activate.ps1

pip install -r requirements.txt## Common Issues

```

**"Backend won't start!"**

### Frontend won't start?- Did you activate the virtual environment?

```powershell- Did you fill in the .env file?

cd frontend- Is port 8000 already in use?

npm install

```**"Frontend can't connect to backend!"**

- Is the backend actually running?

### Confluence not working?- Check the console for CORS errors

1. Check `backend/.env` has valid credentials- Make sure backend is on port 8000

2. Run `.\test-confluence.ps1`

3. Verify page ID is correct**"No content showing up!"**

4. Check API token is valid- Check if your Confluence pages have the right labels

- Verify your Confluence credentials in backend/.env

### No courses showing?- Look at the backend logs

- Backend must be running

- Check `backend/onboarding/` folder exists## Tech Stack

- Create a test course in the UI

**Backend:**

---- FastAPI (because it's fast and has cool docs)

- Requests (for Confluence API calls)

## 🎯 Next Steps- Pydantic (type safety ftw)



1. ✅ Setup complete? Run `.\dev.ps1`**Frontend:**

2. ✅ Servers running? Open http://localhost:3000- React (hooks only, class components are dead)

3. ✅ Create your first course- Vite (way faster than CRA)

4. ✅ Add Confluence page IDs- Axios (for API calls)

5. ✅ Test with real pages

6. 🔜 Add OpenAI API key for AI summaries (optional)## TODO



---- [ ] Implement actual AI integration

- [ ] Add quiz component

## 📚 Additional Docs- [ ] Progress tracking

- [ ] Better error handling

- **CONFIG_FILE_SYSTEM.md** - Deep dive into the config system- [ ] Tests (lol someday)

- **ARCHITECTURE.md** - Technical architecture details- [ ] Deployment docs

- **CHANGELOG.md** - Version history

## License

---

MIT or whatever, it's for hiring anyway

## 💡 Tips

---

- **Version Control**: Commit `onboarding/*.json` to share courses with your team

- **Backup**: Just copy the `onboarding/` folderBuilt by a junior dev who Googles everything 🔍

- **Reuse**: Clone configs for similar roles

- **Edit Anywhere**: Update configs in UI or directly edit JSON files

---

**Made with ❤️ and junior dev energy** 😄

Built by developers who got tired of reading 47 Confluence pages on day one.
