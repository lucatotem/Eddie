# Changelog

## v3.0 - File-Based Config System (Oct 5, 2025)

**Major upgrade: No more Confluence setup required!**

### New Features
- ✅ File-based config storage (`backend/onboarding/*.json`)
- ✅ Full UI for creating/editing courses
- ✅ Per-course settings (folder recursion, quiz toggle)
- ✅ ConfigManager component (home screen)
- ✅ ConfigEditor component (create/edit form)

### What Changed
- Configs now saved locally instead of Confluence pages
- No need for "onboarding-config" labels
- Settings customizable per course
- Edit configs anytime via UI

### Migration
- Old Confluence-based system still works
- Can use both systems simultaneously
- Recommended: Create new configs in UI

---

## v2.0 - Folder Expansion (Oct 5, 2025)

### New Features
- ✅ Recursive folder expansion
- Link to a parent page → auto-includes all children
- `get_child_pages()` method in ConfluenceService

---

## v1.0 - Dynamic Course System (Initial Release)

### Features
- Dynamic course system (no hardcoded roles)
- Confluence integration via REST API
- React + FastAPI monorepo
- Course dashboard with modules and quizzes
- Real-time doc fetching from Confluence

---

**Built with realistic junior dev code style** 😄
