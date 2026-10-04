MediBridge --- TASK.md

Project roadmap and implementation checklist for MediBridge.

Status is based on the current Phase 2 project snapshot.

1. Project Status

Current Phase

Phase 2 --- Frontend + Backend Integration

The current project already contains:

FastAPI backend

JWT authentication

SQLAlchemy database layer

Emergency management

Emergency timeline

Trusted contacts

Facility discovery

Haversine nearby-facility search

SMTP emergency notifications

Ambulance coordination state

Hospital coordination state

Automated API tests

Responsive vanilla HTML/CSS/JavaScript frontend

Netlify-ready frontend

Render-ready backend configuration

2. Status Legend

Use the following status markers:

[ ] Not started
[~] In progress
[x] Completed
[!] Blocked / needs decision

3. Phase 1 --- Backend Core

3.1 Project Foundation

Create Python backend structure.

Create FastAPI application.

Configure Uvicorn.

Configure environment variables.

Add .env.example.

Add .gitignore.

Add backend requirements.

Add /api/health endpoint.

Add global exception handling.

Add CORS configuration.

4. Authentication

4.1 Registration

User registration endpoint.

Full-name validation.

Email validation.

Password validation.

Duplicate-email protection.

Secure password hashing.

JWT token generation.

4.2 Login

Login endpoint.

Credential verification.

JWT authentication.

Token expiration validation.

Protected /api/auth/me endpoint.

Invalid-token handling.

Expired-token handling.

4.3 Future Authentication Tasks

Add password reset flow.

Add email verification.

Add optional profile management.

Add refresh-token strategy if required.

Add rate limiting to authentication endpoints.

5. Database

5.1 Current

SQLAlchemy integration.

SQLite development support.

PostgreSQL configuration support.

User model.

Emergency model.

Emergency timeline model.

Emergency notification model.

Trusted contact model.

Facility model.

Ambulance coordination model/state.

Hospital coordination model/state.

5.2 Future

Introduce Alembic migrations.

Create production database migration workflow.

Add database indexes after profiling.

Add backup/restore procedure.

Document production database maintenance.

6. Emergency Management

6.1 Emergency Creation

Create emergency endpoint.

Generate MediBridge emergency code.

Validate incident type.

Validate priority.

Validate patient information.

Validate latitude/longitude.

Associate emergency with authenticated user.

Create initial timeline event.

6.2 Emergency Retrieval

List authenticated user's emergencies.

Retrieve emergency details.

Retrieve timeline.

Retrieve notifications.

Prevent cross-user emergency access.

6.3 Emergency Updates

Update emergency status.

Record relevant timeline changes.

Support resolved status.

Support cancelled status.

6.4 Emergency Deletion

Delete emergency.

Verify ownership before deletion.

Return appropriate status code.

6.5 Future Emergency Improvements

Add richer emergency event types.

Add emergency attachments where legally/technically appropriate.

Add audit logging.

Add emergency export/download.

Add configurable emergency retention policy.

7. Trusted Contacts

Create trusted contact.

Update trusted contact.

Delete trusted contact.

List authenticated user's contacts.

Support primary contact.

Support phone contact.

Support email contact.

Prevent access to another user's contacts.

Use contacts during emergency notifications.

Future

Add contact verification.

Add contact invitation workflow.

Add contact notification preferences.

Add SMS provider integration when appropriate.

Add notification delivery history per contact.

8. Healthcare Facilities

8.1 Facility Data

Facility database model.

Seed demonstration facilities.

Facility listing endpoint.

Facility type support.

Address support.

Latitude/longitude support.

Demo-data distinction.

8.2 Search

Nearby facility search.

Haversine distance calculation.

Radius filtering.

Distance sorting.

Facility type filtering.

Coordinate validation.

Future

Integrate a verified healthcare/facility data provider.

Add live facility verification.

Add operating-hours data.

Add facility phone verification.

Add map visualization.

Add facility filtering UI.

Add verified-provider badges.

Important: Never present seeded demo facilities as live verified
healthcare availability.

9. Ambulance Coordination

Current

Ambulance coordination state.

Status update endpoint.

Status validation.

Timeline integration.

Frontend ambulance status display.

Supported states:

SEARCHING
REQUESTED
ASSIGNED
EN_ROUTE
ARRIVED
COMPLETED
UNAVAILABLE

Future

Integrate a real ambulance provider.

Add provider authentication.

Add verified dispatch confirmation.

Add live ambulance location only when actually provided.

Add real ETA only from a verified provider.

Add dispatch failure/retry handling.

Do not implement fake dispatch or fake live tracking.

10. Hospital Coordination

Current

Hospital coordination state.

Facility selection.

Hospital request creation.

Hospital status updates.

Hospital status validation.

Timeline integration.

Frontend hospital status display.

Future

Integrate verified hospital availability.

Add hospital acceptance confirmation.

Add verified bed/department availability if supported by a real
provider.

Add provider response timestamps.

Add hospital communication workflow.

11. Notifications

Email

SMTP configuration.

Emergency notification endpoint.

Contact-level notification status.

Retry behavior.

Notification record creation.

Honest failure state when SMTP is unavailable.

Successful-send test with mocked SMTP.

Future

Add email templates.

Add configurable notification preferences.

Add delivery provider webhooks where supported.

Add SMS provider integration.

Add push notifications.

Add in-app notification center.

12. Emergency Timeline

Create initial emergency event.

Store timeline events.

Retrieve timeline.

Display timeline in frontend.

Show timestamps.

Show event descriptions.

Future

Add event categories.

Add actor/source information.

Add richer timeline filters.

Add audit-friendly event IDs.

Add exportable timeline.

13. Backend Testing

Current

Authentication tests.

Invalid credential test.

Duplicate registration test.

Protected endpoint tests.

Invalid JWT test.

Expired JWT test.

Emergency CRUD tests.

User isolation test.

Input validation tests.

Contact tests.

Notification failure test.

Mocked notification success test.

Facility tests.

Nearby search tests.

Coordination tests.

Health endpoint test.

Run:

cd backend
pytest

Future

Increase coverage for edge cases.

Add notification retry edge-case tests.

Add database migration tests.

Add CORS/security tests.

Add rate-limit tests after rate limiting is implemented.

Add integration tests against a test PostgreSQL database.

14. Frontend Phase 2

14.1 Authentication UI

Login page.

Registration page.

JWT storage/usage.

Authentication redirects.

Logout.

User information display.

Future

Password reset UI.

Email verification UI.

Profile page.

15. Dashboard

Dashboard page.

Active emergency statistics.

Resolved emergency statistics.

Trusted-contact count.

Facility count.

Press-and-hold SOS.

Emergency confirmation flow.

Safety/disclaimer notice.

Responsive dashboard layout.

Future

Add richer emergency analytics.

Add recent emergency activity.

Add profile summary.

Add verified facility highlights.

Add optional map view.

16. SOS Workflow

Press-and-hold interaction.

Three-second hold requirement.

Progress indication.

Confirmation step.

Incident selection.

Priority selection.

Location input.

Emergency creation.

Redirect/display emergency details.

Future

Optional browser geolocation permission flow.

Better cancellation feedback.

Accessibility testing with keyboard and screen readers.

Emergency workflow analytics.

17. Emergency Frontend

Emergency summary.

Trusted contacts.

Email alerts.

Ambulance status.

Hospital status.

Nearby facilities.

Timeline.

Notifications.

Print/PDF support.

Emergency resolution controls.

Future

More detailed provider state.

Live provider integration.

Map-based facility selection.

Richer notification history.

Emergency export.

18. Contacts Frontend

Contact list.

Add contact.

Edit contact.

Delete contact.

Primary-contact display.

Responsive contact UI.

Future

Contact verification.

Notification preferences.

Contact invitation.

19. Facilities Frontend

Facility list.

Nearby facility search.

Distance display.

Facility type display.

Call action where applicable.

Directions action.

Facility selection.

Future

Interactive map.

Search/filter controls.

Verified facility badges.

Opening-hours display.

Real-time availability when supported.

20. History Frontend

History page.

Emergency listing.

History filters.

Status visibility.

Responsive history UI.

Future

Date-range filtering.

Search by emergency code.

Export history.

Pagination for large datasets.

21. Theme

Light theme.

Dark theme.

Theme persistence.

Theme toggle.

Theme-aware status colors.

Future

System-theme detection.

User profile theme preference.

22. Internationalization

Current

English navigation/safety text.

Hindi navigation/safety text.

Bengali navigation/safety text.

Language preference persistence.

Future

Translate all page strings.

Translate validation errors.

Translate API-facing UI messages.

Add language metadata.

Improve multilingual accessibility.

Add additional languages if required.

23. Accessibility

Semantic page structure.

Visible focus states.

Form labels.

aria-current.

aria-live feedback.

Keyboard-friendly SOS interaction.

Reduced-motion support.

Responsive touch targets.

Future

Run automated accessibility audit.

Run keyboard-only test across every page.

Test with a screen reader.

Verify color contrast.

Verify all icon-only controls have accessible labels.

24. Security Hardening

High Priority

Add API rate limiting.

Add stronger production CORS configuration.

Review JWT secret requirements.

Add security headers.

Add request size limits.

Review authentication brute-force protection.

Review sensitive logging.

Review dependency vulnerabilities.

Privacy

Document data retention.

Document user-data deletion behavior.

Minimize stored location data.

Ensure demo screenshots contain no real patient data.

Review all production logs for sensitive information.

25. Profile

Status: Not started

Create:

profile.html
profile.js

Potential features:

Profile photo.

Full name.

Email.

Phone.

Age.

Blood group.

Emergency preferences.

Theme preference.

Language preference.

Account deletion.

Profile update API.

26. AI Layer

Status: Not started

Possible future AI functionality:

AI emergency information assistant.

Natural-language emergency intake.

Intelligent facility search.

Emergency-summary generation.

Timeline summarization.

Multilingual assistance.

AI safety requirements

AI must not:

Diagnose medical conditions.

Replace a doctor.

Claim certainty about a medical emergency.

Pretend to contact emergency services.

Invent hospital availability.

Invent ambulance availability.

AI responses must remain clearly informational.

27. Progressive Web App

Status: Not started

Add manifest.json.

Add service worker.

Add installability.

Add offline shell.

Add offline-safe status page.

Define which actions require an internet connection.

Test mobile installation.

Do not allow offline mode to imply that an emergency request was
successfully transmitted when the network is unavailable.

28. In-App Notification Center

Status: Not started

Create a dedicated notification center.

Potential features:

Notification list.

Read/unread status.

Notification timestamps.

Emergency-linked notifications.

Filter by notification type.

Mark as read.

Delete/archive notifications.

Mobile notification UI.

29. Production Deployment

Backend --- Render

Render deployment instructions documented.

Production Uvicorn command documented.

Environment variable requirements documented.

Before production:

Set strong SECRET_KEY.

Set PostgreSQL DATABASE_URL.

Set production CORS_ORIGINS.

Set FRONTEND_URL.

Configure SMTP if email is required.

Verify /api/health.

Run backend tests.

Verify production logs.

Test authentication from deployed frontend.

Frontend --- Netlify

Netlify deployment configured.

Base directory set to:

frontend

Build command left empty.

Publish directory set to:

.

Before production:

Set API_BASE in frontend/config.js to the deployed backend
URL.

Deploy frontend/.

Verify login.

Verify registration.

Verify dashboard.

Verify SOS.

Verify facilities.

Verify contacts.

Verify history.

Verify emergency details.

Verify CORS from the Netlify domain.

30. Documentation

Current

README.md

RULES.md

DESIGN.md

TASK.md

Future

API documentation.

Deployment guide.

Database setup guide.

Environment-variable reference.

Troubleshooting guide.

Architecture diagram.

Screenshots.

Demo account instructions if required.

31. GitHub Repository Quality

Add project screenshots.

Add architecture diagram.

Add live-demo link.

Add technology badges.

Add clear setup instructions.

Add contribution guidelines if collaboration is opened.

Add license if required.

Verify no secrets are committed.

Verify .env is ignored.

Keep README status synchronized with implementation.

32. Final Testing Checklist

Before a public release:

Authentication

Register a new user.

Login with valid credentials.

Reject incorrect credentials.

Reject duplicate email.

Reject expired JWT.

Reject invalid JWT.

Logout successfully.

Emergency

Create emergency.

Validate incident type.

Validate priority.

Validate coordinates.

View emergency.

View timeline.

Update emergency.

Resolve emergency.

Cancel emergency.

Delete emergency.

Verify user isolation.

Contacts

Add contact.

Edit contact.

Delete contact.

Set primary contact.

Verify contact ownership.

Facilities

List facilities.

Search nearby facilities.

Test radius.

Test facility type.

Test invalid coordinates.

Verify demo-data labeling.

Notifications

Test without SMTP.

Confirm honest failure state.

Test mocked successful delivery.

Verify notification records.

Verify retry behavior.

Frontend

Login.

Register.

Dashboard.

SOS.

Emergency page.

Contacts.

Facilities.

History.

Dark mode.

Light mode.

Hindi.

Bengali.

Mobile.

Desktop.

Print/PDF.

33. Release Checklist

A release can be marked READY only when:

All critical tests pass.

No secrets are committed.

Production environment variables are configured.

CORS is restricted to trusted origins.

Frontend points to the correct backend.

Backend health endpoint works.

Authentication works.

Emergency ownership isolation works.

Emergency UI is understandable.

Demo facility data is clearly labeled.

No fake emergency dispatch claims exist.

Mobile layout has been tested.

Accessibility checks have been completed.

README is up to date.

RULES.md is up to date.

DESIGN.md is up to date.

TASK.md is up to date.

34. Priority Roadmap

🔴 P0 --- Critical

Production security review.

Production CORS configuration.

Strong production secret configuration.

Verify PostgreSQL production database.

Verify frontend-to-backend deployment.

Full authentication test.

Full emergency workflow test.

Confirm no misleading emergency-service claims.

🟠 P1 --- Important

API rate limiting.

Profile page.

Full multilingual translation.

Accessibility audit.

Better production logging.

Database migrations.

Improved documentation.

🟡 P2 --- Enhancement

In-app notification center.

Interactive map.

PWA.

Richer facility filters.

Emergency export.

Advanced history filters.

🟢 P3 --- Future

AI assistant.

Verified healthcare provider integrations.

Real ambulance integration.

Real hospital coordination integration.

Push notifications.

Advanced analytics.

35. Definition of Done

A task is complete only when:

Code is implemented.

Relevant frontend behavior works.

Relevant backend behavior works.

Validation is implemented.

Authentication/authorization is correct.

User ownership is enforced.

Errors are handled.

Tests pass.

Mobile layout is verified.

Accessibility is considered.

No secrets are exposed.

Documentation is updated.

The feature does not introduce misleading healthcare/emergency
claims.

36. Project Completion Goal

The long-term goal is to evolve MediBridge from a demo
emergency-coordination platform into a secure, accessible, verified,
and production-ready healthcare coordination system.

The project must always prioritize:

Safety
   ↓
Privacy
   ↓
Reliability
   ↓
Accessibility
   ↓
Clarity
   ↓
Features

Features should never be added at the cost of safety, privacy, or
honesty.