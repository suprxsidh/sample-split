# SampleSplit - Roadmap

An open-source expense splitting app inspired by Splitwise. Built for groups of friends to track shared expenses and settle up easily.

## Philosophy
- **Simple first**: Core features work flawlessly before adding complexity
- **User-owned**: Self-hostable, no lock-in
- **Privacy-first**: No tracking, no data sharing

---

## Version 0.1 - MVP
### Goal: Get a working app running locally with friends

- [x] User registration/login (simple)
- [x] Create groups with 6-digit invite codes
- [x] Join groups via invite code
- [x] Add expenses (equal split among selected members)
- [x] View group balances
- [x] Record settlements
- [x] Simplify debts algorithm
- [x] Dark mode toggle

**Status**: Complete ✅

---

## Version 0.2 - Enhanced Splitting & Features
### Goal: More split options and basic management features

- [x] Split by percentage (must total 100%)
- [x] Split by exact amounts
- [x] Expense date picker
- [x] Search expenses
- [x] Delete expense (creator only)
- [x] Edit group name
- [x] Leave group
- [x] Copy invite code

**Status**: Complete ✅

---

## Version 0.3 - Friends Release (For Sharing Now)
### Goal: Get friends using the app ASAP

**Phase 1 - Critical** ✅
- [x] GitHub repository created
- [x] `.gitignore` (exclude venv, db, __pycache__)
- [x] LICENSE file (MIT)
- [x] README.md with features + screenshots
- [x] Dockerfile
- [x] Basic pytest tests (registration, balances, settlements)
- [x] Railway deployment (free tier)

**Phase 2 - Polish (Before Public Release)** ✅
- [x] Automated test suite (9 tests passing)
- [x] Flask-WTF CSRF protection
- [x] Rate limiting on auth routes
- [x] CONTRIBUTING.md
- [x] CHANGELOG.md

**Status**: Phase 1 & 2 Complete ✅
**Live URL**: https://sample-split-production.up.railway.app
**Priority**: High
**Timeline**: This week

---

## Version 0.4 - Open Source Release
### Goal: Community-ready release

**Documentation**
- [x] Complete README with installation guide
- [x] Deployment guides (Railway, Render, Fly.io, Docker)
- [x] SECURITY.md
- [ ] Demo screenshots/GIFs (deferred - friends testing UI)

**Code Quality**
- [x] Automated tests (>80% coverage) - 81% coverage
- [x] Security audit (basic)
- [x] Code formatter (black)
- [x] Linting (flake8)
- [x] CI/CD pipeline (GitHub Actions)

**Community**
- [x] CONTRIBUTING.md
- [x] CODE_OF_CONDUCT.md
- [x] Issue templates
- [x] Pull request template

**Status**: Complete ✅ (Demo screenshots deferred to friends testing)
**Priority**: High
**Timeline**: Complete - pending friends testing

---

## Version 0.5 - Stability & Polish
### Goal: Fix bugs, improve UX, make it reliable

- [x] Loading states for all async operations
- [x] Empty states (no groups, no expenses)
- [x] Confirmation dialogs for actions
- [x] Session timeout handling
- [x] Responsive mobile design improvements
- [x] Password reset functionality (Admin-mediated)

**Status**: Complete
**Priority**: High

---

## Version 0.6 - Categories & Organization
### Goal: Help users organize and analyze spending

- [x] User-defined categories
- [x] Category icons/colors
- [x] Filter expenses by category
- [x] Category spending summary
- [x] Tags for expenses
- [x] Sort expenses (by date, amount, category)

**Status**: Complete ✅
**Priority**: Medium

---

## Version 0.7 - Groups & Social
### Goal: Improve group management

- [x] Remove members (group admin only)
- [x] Group chat/comments on expenses
- [x] Expense history/receipts upload
- [x] Recurring expenses

**Status**: Complete ✅
**Priority**: Medium

---

## Version 0.8 - Export & Reports
### Goal: Data ownership and insights

- [x] Export to PDF
- [x] Monthly/weekly spending summaries
- [x] Per-person spending breakdown
- [x] Charts and visualizations
- [x] Budget limits per category

**Status**: Complete ✅
**Priority**: Low

---

## Version 1.0 - Production Release
### Goal: Production-ready open source

- [x] PostgreSQL support (for scaling)
- [x] PWA support
- [x] Docker Compose with PostgreSQL
- [x] Multi-stage Dockerfile with health checks
- [x] .env.example with production config

**Status**: Complete ✅
**Priority**: High

---

## Version 1.1 - OAuth + Real-time
### Goal: Modern auth and live updates

- [ ] OAuth authentication (Google/GitHub)
- [ ] Redis for caching
- [ ] WebSocket for real-time updates
- [ ] Comprehensive API documentation

**Priority**: Medium

---

## Version 1.2 - Mobile App
### Goal: iOS/Android app via PWA + Capacitor

**Phase 1 - PWA (Completed in v1.0)** ✅
- [x] Add `manifest.json` (app name, icons, theme, standalone display)
- [x] Create service worker for offline caching
- [x] Add "Add to Home Screen" prompt
- [x] PWA meta tags in `base.html`

**Phase 2 - Capacitor + APK**
- [ ] Wrap PWA with Capacitor for Android APK
- [ ] GitHub Actions workflow for automated APK builds
- [ ] GitHub Releases with APK downloads
- [ ] README with install instructions

**Files to Create/Modify:**
| File | Action |
|------|--------|
| `static/manifest.json` | ✅ Done |
| `static/sw.js` | ✅ Done |
| `static/icons/` | ✅ Done |
| `templates/base.html` | ✅ Done |
| `.github/workflows/apk.yml` | New |
| `ROADMAP.md` | Modify |

**Priority**: Medium
**Timeline**: TBD

---

## Future Ideas (Backlog)

### User Experience
- [x] Offline support (partial - PWA shell cached, offline fallback)
- [ ] Push notifications
- [ ] Keyboard shortcuts
- [ ] Email/SMTP password reset (self-service via Resend/SendGrid)

### Integration
- [ ] WhatsApp/Telegram bot
- [ ] QR code generation for payment links
- [ ] UPI/Venmo payment links

### Advanced Features
- [ ] Monthly settle-up reminders
- [ ] Receipt scanning with OCR
- [ ] AI suggestions

---

## Technical Debt / Refactoring

- [ ] Migrate from Flask to FastAPI (better async support)
- [ ] Replace Jinja2 with React/HTMX
- [ ] Add TypeScript to frontend
- [ ] Add background job processing (Celery)
- [ ] Add monitoring (Sentry)

---

## Architecture Decisions

| Decision | Current | Options |
|----------|---------|---------|
| Frontend | Jinja2 | React, HTMX, Vue |
| Mobile | PWA-ready (v1.0) | PWA + Capacitor (v1.2) |
| Database | SQLite (default), PostgreSQL (production) | PostgreSQL, Supabase |
| Auth | Session-based | JWT, OAuth |
| Hosting | Local, Docker | Railway, Vercel, Fly.io, Docker Compose |
| Real-time | Polling | WebSocket |
| Testing | pytest | None |

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Follow existing code style (see AGENTS.md)
4. Add tests for new features
5. Submit a pull request

---

## License
MIT License

---

*Last updated: 2026-03-21*
*v1.0 Production Release: 2026-03-21*
