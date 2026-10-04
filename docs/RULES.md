MediBridge --- Project Rules

Purpose: Development, security, UI, API, and deployment rules for
the MediBridge healthcare emergency-coordination platform.

1. Project Purpose

MediBridge is a healthcare and emergency-coordination web application
intended to help users:

Create and manage emergency records.

Store basic patient information.

Manage trusted emergency contacts.

Find healthcare facilities.

Record ambulance requests.

Record hospital/facility coordination.

Maintain emergency timelines and notification history.

Access the system through a responsive web interface.

Important: MediBridge is an educational/project platform for
information and coordination. It is not a replacement for professional
medical advice, diagnosis, treatment, ambulances, hospitals, police,
fire services, or other emergency services.

2. Core Technology Rules

Frontend

The frontend must use:

HTML5

CSS3

Vanilla JavaScript (ES6+)

Responsive Web Design

Do not introduce a frontend framework unless the project architecture is
intentionally migrated and documented.

Backend

The backend must use:

Python

FastAPI

SQLAlchemy

Pydantic

PyJWT

Uvicorn

Database

The application must support:

SQLite for simple/local development and testing.

PostgreSQL for production deployments when configured through
DATABASE_URL.

Never hard-code production database credentials.

3. Repository Structure

The repository should maintain the following high-level structure:

MediBridge/
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── emergency.html
│   ├── facilities.html
│   ├── contacts.html
│   ├── history.html
│   ├── *.js
│   ├── style.css
│   └── config.js
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routers/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── README.md
├── RULES.md
├── DESIGN.md
├── TASK.md
└── .gitignore

Keep frontend and backend responsibilities separated.

4. Authentication Rules

Authentication is required for protected API resources.

Registration

Email must be validated.

Password must be at least 8 characters.

Password must contain both letters and numbers.

Duplicate email addresses must be rejected.

Passwords must never be stored in plain text.

Password Storage

Passwords must be securely hashed.

Do not:

Store plain-text passwords.

Commit passwords to GitHub.

Put passwords in frontend JavaScript.

Put secret values directly inside source code.

JWT

Authentication tokens must:

Be signed using the server-side secret.

Have an expiration time.

Be validated before accessing protected resources.

Never expose the signing secret to the frontend.

5. Environment & Secrets Rules

All secrets must be stored in environment variables.

Examples:

SECRET_KEY=
DATABASE_URL=
ACCESS_TOKEN_EXPIRE_MINUTES=
CORS_ORIGINS=

SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=
SMTP_USE_TLS=
FRONTEND_URL=

Never commit:

.env
passwords
API keys
JWT secrets
SMTP passwords
database credentials
private certificates
private tokens

The .env.example file may contain variable names and safe placeholder
values only.

6. API Security Rules

Every protected endpoint must verify the authenticated user.

Examples of protected resources include:

/api/auth/me
/api/contacts
/api/emergencies
/api/facilities

User Ownership

A user must only be able to access their own:

Emergency records

Emergency timeline

Emergency notifications

Trusted contacts

Never expose another user's private emergency data.

When a requested emergency record does not belong to the authenticated
user, return a safe 404 response instead of revealing that the record
exists.

7. Input Validation Rules

All API input must be validated using Pydantic schemas.

Validate:

Email addresses

Password length and strength

Names

Phone numbers where applicable

Ages

Blood groups

Latitude and longitude

Emergency priority

Incident type

Emergency status

Ambulance status

Hospital status

Facility IDs

Contact priority

Invalid input must return an appropriate validation response rather than
causing an unhandled server error.

Never trust data coming from the browser.

8. Emergency Rules

Emergency records must contain enough information to identify the
emergency safely.

Supported incident types include:

Accident

Medical Emergency

Fire

Injury

Unconscious Person

Cardiac Emergency

Breathing Problem

Other

Supported priorities:

LOW
MEDIUM
HIGH
CRITICAL

Supported emergency statuses:

ACTIVE
RESOLVED
CANCELLED

Every newly created emergency should:

Belong to the authenticated user.

Receive a unique MediBridge emergency code.

Record creation time.

Create ambulance coordination state.

Create hospital coordination state.

Create an initial timeline event.

Create an in-app notification record.

9. Emergency Safety Rules

MediBridge must never falsely claim that emergency services have been
dispatched when no real provider integration exists.

For example:

An ambulance request currently records a request in MediBridge. It
does not automatically dispatch an ambulance.

The UI and API must clearly distinguish between:

Searching

Requested

Assigned

En route

Arrived

Completed

Unavailable

Do not display a fake real-time ambulance location, ETA, hospital
acceptance, or dispatch status unless a genuine service integration
provides that information.

10. Healthcare Facility Rules

Facility information must be treated carefully.

The current seeded facilities are demonstration/project data unless
verified through a real provider.

Never claim that:

A hospital currently has a bed available.

An ambulance is physically available.

Blood is currently available.

A facility has accepted a patient.

A doctor is currently available.

unless the information comes from a verified live integration.

Facility distance calculations may use latitude/longitude and the
Haversine formula.

11. Location Rules

Location data is sensitive.

Only collect location when required for an application feature.

The application must:

Validate latitude between -90 and 90.

Validate longitude between -180 and 180.

Clearly communicate when location is captured.

Avoid exposing a user's location to unauthorized users.

Do not publish private user location data in GitHub repositories, logs,
screenshots, or demo data.

12. Trusted Contact Rules

Trusted contacts may contain:

Name

Relationship

Phone

Email

Priority

Primary-contact status

A contact must contain at least one communication method:

Phone OR Email

If a contact is marked as primary, other contacts for the same user
should not remain primary.

Never expose another user's contacts.

13. Notification Rules

Email notifications must only be sent when SMTP is correctly configured.

If SMTP is not configured:

Do not pretend the email was sent.

Record the notification as failed where appropriate.

Return an honest error to the frontend.

Notification logs may contain:

Notification type

Channel

Recipient

Status

Error information

Attempt count

Timestamp

Never log SMTP passwords, JWT secrets, or other credentials.

14. Error Handling Rules

The backend must return clear and safe errors.

Use appropriate HTTP status codes, such as:

200 — Successful request
201 — Resource created
204 — Resource deleted successfully
400 — Bad request
401 — Authentication required
404 — Resource not found
409 — Conflict
422 — Validation error
502 — External notification/service failure
500 — Unexpected server error

Do not expose stack traces, database errors, passwords, secrets, or
internal implementation details to users.

15. Frontend Rules

The frontend must:

Remain responsive.

Work on desktop, tablet, and mobile.

Provide visible loading states when appropriate.

Provide useful success/error feedback.

Avoid broken buttons and dead links.

Keep navigation consistent.

Handle API failures gracefully.

Never expose backend secrets.

User-facing messages should be understandable and action-oriented.

Example:

Good:
"Unable to send the notification. Please check your email configuration."

Avoid:
"SMTPException: [internal server error details]"

16. Accessibility Rules

The UI should follow basic accessibility practices.

Use:

Semantic HTML.

Proper heading hierarchy.

Labels for form controls.

Descriptive button text.

Keyboard-accessible controls.

Sufficient text contrast.

Meaningful alt text for important images.

Visible focus states.

Do not rely only on color to communicate emergency status.

17. Responsive Design Rules

The application must remain usable at:

Mobile phone sizes

Tablet sizes

Laptop/desktop sizes

Do not allow:

Horizontal overflow caused by the application layout.

Buttons that become impossible to tap on mobile.

Text that overlaps important controls.

Forms that become unusable on small screens.

Test important pages on both desktop and mobile widths.

18. JavaScript Rules

Frontend JavaScript must:

Use clear function names.

Avoid unnecessary global variables.

Handle failed API requests.

Validate important user input before submission.

Never contain private secrets.

Avoid silently swallowing errors.

Keep API communication centralized where practical.

Do not place passwords, database credentials, SMTP credentials, or JWT
signing secrets in frontend JavaScript.

19. Backend Code Rules

Backend code should:

Keep routes focused on HTTP/API responsibilities.

Keep database models in models.py.

Keep validation schemas in schemas.py.

Keep authentication logic in auth.py.

Keep database configuration in database.py.

Keep reusable external-service logic in services/.

Keep route groups separated inside routers/.

Avoid putting the entire backend into a single file.

20. Database Rules

Database models must use:

Primary keys.

Foreign keys where relationships exist.

Appropriate nullable/non-nullable settings.

Appropriate data types.

Relationships where useful.

User-owned records must include an ownership relationship to the
authenticated user.

Database changes must not silently destroy existing production data.

For future production schema changes, use a proper migration strategy
rather than relying only on automatic table creation.

21. Testing Rules

Backend changes should be tested before deployment.

Important test areas include:

Registration

Login

Invalid credentials

Authentication protection

JWT expiration

Emergency creation

Emergency ownership/isolation

Emergency updates

Emergency deletion

Contact creation/update/deletion

Notification failure

Notification success

Facility search

Nearby facility calculations

Invalid coordinates

Hospital coordination

Ambulance coordination

Health endpoint

Run tests using:

pytest

A feature is not considered complete if its critical backend behavior is
untested.

22. Git & GitHub Rules

Use meaningful commit messages.

Examples:

feat: add emergency coordination
fix: correct facility search
feat: add trusted contacts
fix: improve mobile dashboard
docs: update deployment instructions
test: add emergency API tests

Do not commit:

.env
*.db
__pycache__/
.venv/
secrets
credentials
private keys

Before pushing code, check:

git status

and inspect the files being committed.

23. Pull Request Rules

Before merging a feature:

Confirm the feature works.

Run tests.

Check the browser console.

Check API errors.

Test mobile layout.

Verify authentication.

Verify ownership/isolation.

Review changed files.

Remove debugging code.

Remove temporary credentials.

Update documentation if behavior changed.

24. Deployment Rules

Netlify Frontend

The Netlify frontend deployment uses:

Branch:
main

Base directory:
frontend

Build command:
(empty)

Publish directory:
.

Functions directory:
(empty)

The frontend must have its required files inside the frontend/
directory.

Backend

The backend must run using a production ASGI server such as:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

Production environment variables must be configured through the hosting
provider.

Never commit production .env files.

25. CORS Rules

Only trusted frontend origins should be configured in production.

Development may use a local origin such as:

http://localhost:5500

Production should use the actual deployed frontend URL.

Do not use unrestricted production CORS unless there is a documented
security reason.

26. Demo Data Rules

Demo facilities may be seeded for development and testing.

Demo records must be clearly identifiable as demo data.

Never present demo data as verified live healthcare information.

When screenshots are published:

Use test accounts.

Avoid real patient information.

Avoid real medical records.

Avoid private addresses.

Avoid real emergency cases.

27. Privacy Rules

MediBridge may handle sensitive information such as:

Patient name

Age

Blood group

Medical notes

Allergies

Symptoms

Emergency location

Trusted contacts

Therefore:

Collect only necessary information.

Protect authenticated resources.

Do not expose private records.

Do not publish real patient data.

Do not use real personal medical information in demonstrations.

Do not commit private data to GitHub.

28. Medical Disclaimer Rule

The application must maintain a clear disclaimer that MediBridge is an
informational and coordination platform.

Emergency-related UI should encourage users to contact appropriate local
emergency services when immediate professional assistance is required.

The application must not provide a false impression of being an official
government, hospital, ambulance, police, or fire-service platform unless
a real official partnership exists.

29. UI/UX Consistency Rules

Maintain a consistent design system across all pages.

Use consistent:

Typography

Colors

Buttons

Cards

Forms

Spacing

Navigation

Status indicators

Error messages

Success messages

Do not redesign unrelated pages while implementing a small feature
unless the change is intentional and documented.

30. Performance Rules

Avoid unnecessary:

API requests

DOM operations

Large assets

Repeated database queries

Blocking frontend scripts

Optimize images before committing them.

Keep JavaScript modular and readable.

31. Change Management Rules

Before changing an existing feature:

Understand the current implementation.

Identify dependent frontend and backend code.

Make the smallest safe change.

Test the affected feature.

Test related functionality.

Update documentation when necessary.

Do not remove existing functionality without a clear reason.

32. Definition of Done

A MediBridge feature is considered complete only when:

The feature is implemented.

The UI works on desktop and mobile.

API validation is implemented where needed.

Authentication/authorization is correct.

User ownership is enforced.

Errors are handled.

Sensitive information is protected.

Tests are added or updated when applicable.

No secrets are committed.

Documentation is updated when necessary.

The feature has been manually verified.

33. Final Golden Rules

Never expose secrets.

Never store plain-text passwords.

Never expose another user's private data.

Never fake an emergency-service dispatch.

Never present demo facility information as verified live data.

Never claim an ambulance or hospital has accepted a request
without real confirmation.

Always validate backend input.

Always enforce authentication on protected resources.

Always keep emergency information clear and honest.

Always test before deployment.

Keep frontend and backend responsibilities separated.

Keep the project documentation synchronized with the
implementation.