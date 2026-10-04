# MediBridge — Product Requirements Document (PRD)

| | |
|---|---|
| **Product** | MediBridge — Emergency Coordination Platform |
| **Version** | 0.2 (demo / pilot-ready prototype) |
| **Status** | Deployed as a demo; not yet validated with real users |
| **Last updated** | 5 October 2026 |
| **Repository** | github.com/jhaabhay7667-cyber/MediBridge |

> **Safety statement (applies to the whole product).** MediBridge is for coordination and information. It does **not** contact government emergency services, dispatch ambulances, or provide medical advice. In a genuine emergency, call your local emergency number (112 in India).

---

## 1. Overview

MediBridge helps a person in an emergency organise the information and communication around it: who the patient is, where they are, how serious it is, who should be told, and which nearby facilities could help. The central workflow is:

**SOS → patient info → location → priority → trusted-contact alert → nearby facilities → ambulance/hospital status → timeline → resolution**

## 2. Problem statement

In the first minutes of an emergency, people lose time and make mistakes because:
- Family members are not told quickly, or are told incompletely (no location, no patient details).
- Finding the nearest hospital, blood bank or ambulance service means searching in several places under stress.
- Nothing records what happened and when, which hurts handover to hospitals and later review.

## 3. Goals and non-goals

### Goals
1. Start an emergency record in a few interactions, with an accidental-activation guard.
2. Tell trusted contacts quickly, with the details they need (who, what, where, priority).
3. Let a user find the nearest hospitals, blood banks and other facilities by category in one tap.
4. Keep a complete, honest timeline of every action and its real outcome (including failures).
5. Keep medical and location data private to the account that created it.

### Non-goals (for the current version)
- Calling or integrating with government emergency services.
- Real-time ambulance dispatch or tracking (no provider is integrated).
- Verified live hospital bed or blood stock availability.
- Medical diagnosis or treatment advice.
- Native mobile apps.

## 4. Target users

| Persona | Need |
|---|---|
| **Patient / person at risk** | Start an emergency fast, even under stress, and have their details and location shared. |
| **Trusted contact (family/friend)** | Receive a clear alert with patient, incident, priority and location. No account required to receive the email. |
| **Bystander / helper** *(future)* | Open a shared link to see status without logging in. |
| **Hospital / ambulance coordinator** *(future)* | Receive and acknowledge requests. |

## 5. Scope and status

Legend: ✅ built · 🟡 built with limits · ⬜ not built

### 5.1 Authentication and accounts
| ID | Requirement | Status |
|---|---|---|
| A1 | Register and log in with email and password (min 8 chars, letters + digits) | ✅ |
| A2 | Passwords hashed (PBKDF2-SHA256, salted); never stored in plaintext | ✅ |
| A3 | JWT access token with expiry; 401 on missing/invalid/expired token | ✅ |
| A4 | Current-user endpoint | ✅ |
| A5 | Email verification, password reset, change password | ⬜ |
| A6 | Profile page (allergies, medical notes, edit details) | ⬜ (fields exist in the data model) |

### 5.2 Emergency creation and management
| ID | Requirement | Status |
|---|---|---|
| E1 | SOS button: press and hold 3 s (pointer or Space/Enter), then confirm dialog | ✅ |
| E2 | Browser geolocation with permission-denied/timeout/unsupported handling; emergency is still created without coordinates | ✅ |
| E3 | Manual emergency creation via API (incident type, patient, condition, symptoms, notes, location, priority) | ✅ |
| E4 | Unique emergency code (e.g. `MB-2026-001`), timestamps | ✅ |
| E5 | Priority LOW / MEDIUM / HIGH / CRITICAL, shown with text + symbol (not colour alone) | ✅ |
| E6 | View, update, resolve, delete an emergency; users see only their own | ✅ |
| E7 | Full manual-entry form in the UI (SOS dialog covers incident, priority, location only) | 🟡 |
| E8 | One-page printable summary | 🟡 (print / save-as-PDF of the emergency page) |

### 5.3 Trusted contacts and notifications
| ID | Requirement | Status |
|---|---|---|
| C1 | Add, edit, delete contacts; one primary contact; priority order | ✅ |
| N1 | Email all contacts that have an email address | ✅ |
| N2 | Per-contact delivery status (SENT/FAILED), error text, attempts; retries | ✅ |
| N3 | If every email fails, return 502 and show the real error — no fake success | ✅ |
| N4 | In-app records for created / facility selected / ambulance & hospital status / resolved | 🟡 (stored and shown on the emergency page; no standalone notification centre) |
| N5 | SMS, WhatsApp, push notifications | ⬜ |
| N6 | Public tracking link for contacts (no login) | ⬜ |

### 5.4 Facilities
| ID | Requirement | Status |
|---|---|---|
| F1 | Facility list, nearby (distance-sorted), and filtered search by type, city, radius, emergency-only | ✅ |
| F2 | One-tap category buttons: Hospitals, Blood banks, Ambulances, Emergency centres, Clinics, Pharmacies | ✅ |
| F3 | Auto-widen search to 200 km when nothing is found | ✅ |
| F4 | Call and Directions (Google Maps link) for each result | ✅ |
| F5 | Data is **seeded demo data** around Kolkata, labelled DEMO and "unverified" | 🟡 |
| F6 | Real facility data (e.g. OpenStreetMap) | ⬜ |
| F7 | Verified live availability (beds, blood stock) | ⬜ |

### 5.5 Ambulance and hospital coordination
| ID | Requirement | Status |
|---|---|---|
| H1 | Ambulance status: SEARCHING → REQUESTED → ASSIGNED → EN_ROUTE → ARRIVED → COMPLETED / UNAVAILABLE | 🟡 manual status record only; no provider; UI says nothing is dispatched |
| H2 | Hospital status: SEARCHING → REQUESTED → PENDING → ACCEPTED/REJECTED → READY → ARRIVED → COMPLETED | 🟡 manual status record only |
| H3 | Select a facility for an emergency | ✅ |

### 5.6 Timeline and history
| ID | Requirement | Status |
|---|---|---|
| T1 | Timeline entry for each event: event, time, actor, status | ✅ |
| T2 | History page with filters (ID search, status, priority, incident type, from-date) | ✅ |

### 5.7 Experience
| ID | Requirement | Status |
|---|---|---|
| X1 | Responsive layout (desktop to mobile), navigation always visible | ✅ |
| X2 | Light/dark theme | ✅ |
| X3 | Languages: English, Hindi, Bengali | 🟡 (navigation and the safety notice only) |
| X4 | Accessibility: semantic HTML, labels, focus states, ARIA live toasts, large touch targets | 🟡 (not formally audited) |
| X5 | PWA (installable, offline shell) | ⬜ |

### 5.8 AI assistance *(optional layer, not built)*
Classification, summary, information extraction and an assistant, always labelled as assistance and never as diagnosis. ⬜

## 6. User flows

**Primary — "I need help now"**
1. Dashboard → press and hold SOS for 3 s → confirm incident, priority, fallback location.
2. Device location requested; emergency created even if it is denied.
3. Emergency page opens → "Email trusted contacts" → per-contact result shown.
4. User finds nearby facilities, selects one, records ambulance/hospital status.
5. User marks the emergency resolved; the timeline keeps the full record.

**Secondary — "Where is the nearest blood bank?"**
Facilities → tap **Blood banks** → allow location → nearest results with Call and Directions.

## 7. Architecture

| Layer | Technology | Hosting |
|---|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript (multi-page) | Netlify (publish directory `frontend`) |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, JWT | Render (free web service) |
| Database | SQLite (development), PostgreSQL (production) | Render PostgreSQL (free) |
| Email | Brevo transactional email over HTTPS (production); SMTP supported locally | Brevo |

The frontend reads the backend address from `frontend/config.js` (`API_BASE`). CORS allows only the origins in `CORS_ORIGINS`. All state is stored in the database; the frontend holds only the login token.

## 8. API summary

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Emergencies | `POST/GET /api/emergencies`, `GET/PATCH/DELETE /api/emergencies/{id}` |
| Notifications | `POST /api/emergencies/{id}/notify`, `GET /api/emergencies/{id}/notifications` |
| Coordination | `POST /api/emergencies/{id}/ambulance`, `POST /api/emergencies/{id}/hospital`, `PATCH /api/emergencies/{id}/coordination` |
| Timeline | `GET /api/emergencies/{id}/timeline` |
| Contacts | `GET/POST /api/contacts`, `PUT/DELETE /api/contacts/{id}` |
| Facilities | `GET /api/facilities`, `GET /api/facilities/nearby`, `GET /api/facilities/nearby/search` |
| Health | `GET /api/health` |

Interactive documentation is served at `/docs`.

## 9. Data model

`User` · `Contact` · `Emergency` · `Facility` · `Notification` · `TimelineEvent` · `AmbulanceRequest` · `HospitalCoordination`

A User owns Contacts and Emergencies. An Emergency owns its timeline, notifications, one ambulance request and one hospital coordination record. Deleting an emergency deletes its dependent records.

## 10. Non-functional requirements

### Security
- Passwords hashed and salted; JWT expiry; secrets only in environment variables, never in the repository or frontend.
- Input validated by Pydantic (including latitude/longitude ranges); database access through the ORM.
- Authorization: every emergency and contact query is scoped to the logged-in user; another user's record returns 404.
- CORS restricted to the deployed frontend origin.
- **Not yet built:** rate limiting, email verification, account lockout, audit logging.

### Privacy
- Collect the minimum needed; medical fields are optional.
- Emergency emails contain patient name, incident, priority and location, so contacts can act. Treat this as sensitive.
- **Still needed before real use:** privacy policy, consent screen, account/data deletion, and legal review under India's DPDP Act 2023 (this document is not legal advice).

### Reliability and performance
- Failures are shown honestly: the app never reports success for a failed email or request.
- Free hosting limits (see §11) mean the backend can take about a minute to wake after idling.

### Accessibility
- Colour is never the only carrier of meaning (priority badges use symbols and text); keyboard-operable SOS; visible focus; labelled forms. A formal audit is pending.

## 11. Constraints and known limitations

1. **Demo data only:** facilities are seeded around Kolkata and are not verified.
2. **No dispatch:** ambulance and hospital "coordination" are status records kept by the user.
3. **Render free web service** sleeps when idle (first request can take ~50 s or more) and blocks outbound SMTP, which is why email uses Brevo's HTTPS API.
4. **Render free PostgreSQL** expires on **3 November 2026** unless upgraded; data is deleted after that.
5. **Brevo free plan** has a daily send limit (about 300/day at the time of writing); a Gmail sender address can land in spam.
6. **No email verification:** anyone can register with any address.
7. **Location accuracy** depends on the device and browser; the app does not claim GPS precision.

## 12. Success metrics (for a pilot)

- Time from SOS press to emergency created (target: under 10 s excluding the 3 s hold).
- Share of notification attempts delivered (SENT ÷ attempted).
- Share of emergencies with coordinates captured.
- Pilot users' rating of clarity of the alert email and of finding a nearby facility.
- Zero cross-account data exposure in testing.

## 13. Risks

| Risk | Mitigation |
|---|---|
| Users rely on the app instead of calling emergency services | Persistent safety notice on every page and in every email |
| Unverified facility data leads to a wasted trip | DEMO/unverified labels; "call to confirm" wording; move to real data with a clear source |
| Email lands in spam or is not seen quickly | Add SMS/WhatsApp/push; authenticate a real sending domain |
| Sensitive data exposure | Strict per-user scoping, secrets management, privacy review before launch |
| Free-tier outage or expiry | Paid plan, backups and uptime monitoring before real use |

## 14. Roadmap

**Phase 3 — Trust and polish**
Email verification, password reset, rate limiting, profile and settings pages, privacy policy and consent, full-string translations.

**Phase 4 — Reach**
Public tracking link for contacts, notification centre page, PWA, SMS/WhatsApp alerts.

**Phase 5 — Real data**
OpenStreetMap-based facilities with source attribution, blood-bank data source evaluation, hospital/ambulance partner pilot, real-time updates (WebSockets).

**Phase 6 — Intelligence and scale**
AI classification and handover summaries (labelled as assistance), analytics, multi-organisation support, paid hosting with backups and monitoring.

## 15. Open questions

1. Which first pilot group (college, residential society, NGO) and what local emergency partners are available?
2. Which SMS/WhatsApp provider fits budget and Indian regulations?
3. What is the authoritative, legally usable source of facility and blood-bank data?
4. What retention period and deletion process should apply to emergency records?
5. What review is needed before handling real medical information?