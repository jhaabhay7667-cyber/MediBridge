MediBridge --- DESIGN.md

Design specification: Visual language, layout system, interaction
patterns, accessibility rules, responsive behavior, and UI component
standards for MediBridge.

1. Design Vision

MediBridge is designed as a calm, trustworthy, accessibility-first
healthcare coordination interface.

The design must communicate three qualities:

Trust --- users should immediately understand what the
application does.

Clarity --- emergency information must be easy to scan under
stress.

Actionability --- important actions such as SOS, contacting
trusted people, viewing facilities, and reviewing an emergency
should be obvious.

The interface should avoid unnecessary visual decoration that could
distract from emergency information.

Design principle

Calm for everyday use. Clear during emergencies. Honest about system
capabilities.

MediBridge must never visually imply that a simulated/demo action is a
real emergency-service dispatch.

2. Current Design Language

The current MediBridge frontend uses:

Semantic HTML

Vanilla CSS

Vanilla JavaScript

CSS custom properties

Light and dark themes

Responsive grid layouts

Card-based information grouping

High-visibility emergency controls

Accessible focus states

Minimum 44px interactive controls

Reduced-motion support

Print-friendly emergency records

The design intentionally favors functional healthcare UI over a
marketing-heavy visual style.

3. Design Tokens

All shared colors should be controlled through CSS custom properties.

Current light-theme tokens:

:root {
  --ink: #14213d;
  --bg: #f4f6f8;
  --card: #ffffff;
  --line: #d5dbe3;
  --muted: #55627a;
  --teal: #0b6e66;
  --teal-ink: #ffffff;
  --sos: #b3261e;
  --warn: #8a5a00;
  --ok: #1b6b3a;
  --r: 10px;
}

Current dark-theme tokens:

:root[data-theme="dark"] {
  --ink: #e7ecf4;
  --bg: #0f1622;
  --card: #182233;
  --line: #2c3a52;
  --muted: #9fb0c9;
  --teal: #3fb5a8;
  --teal-ink: #06201d;
  --sos: #ff6b5f;
  --warn: #f0b24a;
  --ok: #5fcf8a;
}

Do not scatter hard-coded colors throughout page-specific CSS when a
design token already exists.

4. Color System

4.1 Primary

MediBridge Teal

Used for:

Primary buttons

Active navigation

Links

Focus indicators

Positive primary actions

Brand identity

Light:

#0B6E66

Dark:

#3FB5A8

4.2 Emergency / SOS

SOS Red

Used only for:

SOS control

Critical emergency states

Destructive actions

Failed notification states

High-risk warnings where appropriate

Light:

#B3261E

Dark:

#FF6B5F

Red must not be used as general decoration.

4.3 Warning

Used for:

High-priority status

Important notices

Configuration warnings

Non-fatal problems

#8A5A00

Dark theme:

#F0B24A

4.4 Success

Used for:

Resolved emergencies

Successful notifications

Successful actions

Positive system states

Light:

#1B6B3A

Dark:

#5FCF8A

4.5 Backgrounds

Light:

Page: #F4F6F8
Card: #FFFFFF

Dark:

Page: #0F1622
Card: #182233

Cards must remain visually distinguishable from the page background
without relying only on shadows.

5. Typography

The project currently uses:

font: 16px/1.5 "Atkinson Hyperlegible", system-ui, sans-serif;

Typography principles

Use readable font sizes.

Maintain generous line height.

Avoid overly condensed text.

Keep emergency information highly scannable.

Use bold text for labels and critical values.

Avoid decorative fonts.

Heading hierarchy

H1 → Page title
H2 → Major section
H3 → Subsection

Do not skip heading levels merely for visual sizing.

6. Spacing System

Use a consistent spacing rhythm.

Preferred spacing values:

4px
8px
12px
16px
24px
32px
48px

Typical usage:

Size   Usage

4px    Small inline gaps
8px    Icon/text gaps
12px   Compact component spacing
16px   Card padding / standard gaps
24px   Section spacing
32px   Page-level separation
48px   Major layout separation

Avoid arbitrary spacing values unless required by a specific component.

7. Border Radius

The shared radius is:

10px

Inputs use a slightly tighter radius:

8px

The SOS control remains fully circular:

border-radius: 50%;

Avoid excessive rounded/pill styling across the whole application
because healthcare interfaces benefit from clear grouping and hierarchy.

8. Layout System

The main application content uses:

main {
  max-width: 1000px;
  margin: 0 auto;
  padding: 1rem;
}

The layout should:

Keep content centered.

Avoid extremely wide reading lines.

Provide comfortable mobile padding.

Use cards to group related information.

9. Grid System

The application uses a responsive grid:

.grid {
  display: grid;
  gap: 1rem;
  grid-template-columns:
    repeat(auto-fit, minmax(220px, 1fr));
}

This is used for dashboard statistics and similar collections.

Cards should automatically stack when the available width becomes too
small.

10. Header Design

The application header contains:

MediBridge brand

Language selector

Theme toggle

Current user name

Logout action

Conceptually:

┌──────────────────────────────────────────────────────┐
│ MediBridge    Language  Theme  User Name  Log out    │
└──────────────────────────────────────────────────────┘

Header rules

Keep the brand visually prominent.

Keep authentication actions easy to find.

Do not hide logout behind unnecessary navigation.

Allow the header to wrap on narrow screens.

11. Navigation

Primary navigation includes:

Dashboard
History
Contacts
Facilities
SOS

The active page must use:

aria-current="page"

The active navigation item uses the primary teal color.

The SOS navigation action uses a red border to distinguish it from
normal navigation.

Mobile behavior

Navigation may horizontally scroll rather than becoming unusably
compressed.

Do not make important navigation targets smaller than the accessibility
minimum.

12. Card Component

Cards are the primary content container.

Current visual specification:

Background: --card
Border: 1px solid --line
Radius: 10px
Padding: 16px
Bottom spacing: 16px

Cards should contain one logical information group.

Examples:

Dashboard statistics
Active emergency
SOS action
Trusted contacts
Ambulance coordination
Hospital coordination
Notifications
Timeline

Avoid placing unrelated workflows inside one large card.

13. Dashboard Design

The dashboard is the user's main operational screen.

It should prioritize:

Active emergency status

SOS action

Emergency statistics

Trusted contacts

Facility information

Statistics

The dashboard currently presents:

Active emergencies

Resolved emergencies

Trusted contacts

Available/demo facilities

Statistics use large values:

2
Active emergencies

The number should be visually dominant.

14. SOS Interaction Design

The SOS action is the most important interaction in the application.

It uses a press-and-hold interaction rather than a single click.

Current interaction:

Press and hold for 3 seconds
        ↓
Progress indicator
        ↓
Confirmation dialog
        ↓
Incident type + priority + location
        ↓
Create emergency record

Why press-and-hold?

It reduces accidental emergency creation from an unintended tap.

Visual requirements

The SOS button should:

Be large.

Be circular.

Have strong visual contrast.

Clearly say SOS.

Show hold 3 s.

Show progress while being held.

Remain keyboard accessible.

Do not

Trigger an emergency immediately from a casual click.

Hide the confirmation step.

Use confusing animation.

Claim that pressing SOS automatically calls an ambulance.

15. Emergency Confirmation Dialog

The confirmation dialog collects:

Incident type

Priority

Optional location text

Incident types include:

Medical Emergency
Accident
Cardiac Emergency
Breathing Problem
Unconscious Person
Injury
Fire
Other

Priority options:

CRITICAL
HIGH
MEDIUM
LOW

The dialog must have:

Clear heading

Clearly labeled inputs

Primary confirmation action

Cancel action

Keyboard accessibility

16. Emergency Detail Page

The emergency detail page is organized into separate cards.

Recommended order:

1. Emergency summary
2. Trusted contacts
3. Ambulance
4. Hospital
5. Notifications
6. Timeline

This order places the most important emergency context first.

17. Emergency Status Design

Emergency status:

ACTIVE
RESOLVED
CANCELLED

Use badge styling.

Example:

[ ACTIVE ]
[ RESOLVED ]

Critical priority:

▲▲▲ CRITICAL

High priority:

▲▲ HIGH

Medium:

▲ MEDIUM

Low:

▽ LOW

Status must always be communicated through text as well as color.

18. Ambulance Coordination Design

The ambulance section displays:

Current status

Provider, if available

ETA, if available

System notes

Request action

Status controls

Supported statuses:

SEARCHING
REQUESTED
ASSIGNED
EN_ROUTE
ARRIVED
COMPLETED
UNAVAILABLE

Important UX rule

If no real ambulance provider is integrated, the interface must
explicitly say:

The request is recorded in MediBridge only and is not a real ambulance
dispatch.

Never create a fake map marker, ETA, provider identity, or live
location.

19. Hospital Coordination Design

The hospital section displays:

Current hospital status

Selected facility

Nearby facility results

Call action

Directions action

Select facility action

Supported hospital states:

SEARCHING
REQUESTED
PENDING
ACCEPTED
REJECTED
READY
ARRIVED
COMPLETED

Demo facilities must display a visible:

DEMO

badge when applicable.

20. Nearby Facilities Design

Facility cards should display:

Facility name
Distance
Type
Address
Call
Directions
Select facility

Example:

City Hospital                 DEMO
3.4 km · Hospital
Address...

[ Call ] [ Directions ] [ Select facility ]

Distance should be presented in kilometers.

The interface must clearly distinguish between calculated proximity and
confirmed real-time availability.

21. Trusted Contacts Design

Trusted contacts should display:

Name

Relationship

Phone

Email

Primary status

Primary contact can be represented using:

★ primary

The contacts page must make it easy to:

Add a contact

Edit a contact

Remove a contact

Identify the primary contact

22. Notification Design

Notifications are displayed in a responsive table.

Columns may include:

Time
Type
Channel / Recipient
Status
Error

Statuses include:

SENT
FAILED

Errors should be human-readable.

Example:

Email failed

instead of exposing raw server exceptions.

23. Timeline Design

Emergency events use a vertical timeline.

Visual concept:

│
├── 20:15  Emergency created
│
├── 20:16  Location captured
│
├── 20:18  Ambulance requested
│
└── 20:25  Hospital selected

The timeline should:

Remain chronological.

Display timestamps.

Show event descriptions.

Show actor/status when available.

Remain readable on mobile.

24. Authentication Pages

Login and registration use a centered authentication layout.

Current maximum width:

420px

Conceptual structure:

          MediBridge

      ┌──────────────────┐
      │      Log in      │
      │                  │
      │ Email            │
      │ [______________] │
      │                  │
      │ Password         │
      │ [______________] │
      │                  │
      │ [    Log in    ] │
      │                  │
      │ Create account   │
      └──────────────────┘

Registration adds:

Full name

Email

Password

Phone

Age

Blood group

Do not visually overwhelm users with unnecessary decorative elements on
authentication screens.

25. Form Design

All form controls should have:

Visible labels

Minimum 44px height

Clear border

Clear focus state

Readable text

Useful validation messages

Current input height:

44px minimum

Focus style:

:focus-visible {
  outline: 3px solid var(--teal);
  outline-offset: 2px;
}

Never remove visible keyboard focus.

26. Button Design

Primary button:

Teal background
White/dark contrasting text
Bold label

Danger button:

Red border
Red text

Normal button:

Card background
Border
Normal text

Buttons must communicate their action through text.

Avoid icon-only buttons unless the icon has an accessible label.

27. Toast Notifications

Toast messages appear near the bottom of the viewport.

Success/default:

Dark background
Light text

Error:

SOS red background
White text

Toast messages should:

Be short.

Explain what happened.

Disappear automatically where appropriate.

Remain readable.

Use aria-live for dynamic feedback.

28. Notice / Disclaimer Design

Important notices use a warning-colored left border.

The MediBridge disclaimer should remain visible on authenticated
application pages.

Core message:

MediBridge is for coordination and information. It does not call
emergency services or replace medical advice. In a genuine emergency,
call your local emergency number.

The application currently references 112 in India in its interface
copy.

29. Theme System

MediBridge supports:

Light
Dark

Theme state is stored in:

localStorage

Key:

mb_theme

Theme changes should preserve the same semantic meaning.

For example:

Critical remains critical in both themes.
Success remains success in both themes.

Do not create a completely different visual hierarchy for dark mode.

30. Language System

The frontend currently supports:

English
Hindi
Bengali

Language preference is stored using:

mb_lang

Supported language codes:

en
hi
bn

Navigation, logout, SOS, and disclaimer text currently have
translations.

Future UI text should use the translation system instead of introducing
hard-coded strings where practical.

31. Responsive Design

The application must work on:

Mobile

320px+

Tablet

600px+

Desktop

1000px content width

At narrow widths:

Grids should stack.

Tables should transform into block-style rows.

Navigation may horizontally scroll.

Buttons must remain tappable.

Forms must remain readable.

Cards must not overflow.

Current responsive table behavior begins below:

600px

32. Accessibility

Accessibility is a core design requirement.

The UI must provide:

Semantic HTML

Labels for inputs

Keyboard operation

Visible focus

aria-current

aria-live

role="alert" for important form errors

Descriptive button labels

Sufficient contrast

Text-based status indicators

The SOS interaction must be accessible through keyboard controls.

Supported keyboard activation:

Space
Enter

33. Reduced Motion

Users who request reduced motion must not receive unnecessary animation.

The project currently supports:

@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
    animation: none !important;
  }
}

Future animations must respect the same preference.

34. Print Design

Emergency details support printing / saving as PDF.

During print:

header → hidden
navigation → hidden
non-print controls → hidden
toast messages → hidden

The page becomes:

white background
black text
clear borders

This makes emergency records suitable for documentation.

35. Iconography

If icons are introduced:

Prefer simple, recognizable icons.

Use icons together with text for critical actions.

Never rely only on color or icon shape.

Provide accessible labels for icon-only controls.

Emergency actions should remain understandable without icons.

36. Motion & Animation

MediBridge should use animation sparingly.

Good uses:

SOS hold-progress feedback

Toast appearance

Small state transitions

Loading indicators

Avoid:

Decorative full-screen animation

Flashing emergency effects

Excessive parallax

Motion that could distract during an emergency

The system should feel responsive rather than flashy.

37. Loading States

When waiting for an API request, display a readable loading state.

Current pattern:

Loading…

with:

aria-busy="true"

Future loading indicators should not block the whole interface unless
the requested operation genuinely requires it.

38. Error States

Error messages should answer:

What happened?

What can the user do next?

Good:

Unable to reach the MediBridge server.
Check your connection and try again.

Avoid:

500 Internal Server Error

as the only user-facing explanation.

39. Empty States

Empty states should be helpful.

Examples:

No active emergency.
Press and hold SOS if you need to start one.

No contacts yet.
Add a trusted contact so they can be notified during an emergency.

No facilities found within 25 km.

Do not leave blank screens when there is no data.

40. Security-Aware UI

The UI must never expose:

JWT secrets

Database credentials

SMTP passwords

Internal stack traces

Private records belonging to another user

Location information should only be displayed to the authenticated owner
of the emergency record.

41. Data Honesty in UI

MediBridge must distinguish clearly between:

Recorded
Requested
Simulated/Demo
Confirmed

For example:

Correct

Ambulance request recorded.
No ambulance provider is connected.

Incorrect

Ambulance dispatched!

unless an actual provider integration confirms the dispatch.

This rule is especially important for emergency-related interfaces.

42. Component Naming

Recommended conceptual components:

Header
Navigation
Card
StatCard
StatusBadge
PriorityBadge
SOSButton
ConfirmationDialog
Notice
Toast
FacilityCard
ContactCard
Timeline
NotificationTable
EmergencySummary

Even though the current implementation uses vanilla JavaScript instead
of a component framework, these concepts should guide reusable UI
functions and CSS classes.

43. Page Design Map

Page                Primary purpose

login.html        User authentication
register.html     Account creation
dashboard.html    Overview + emergency initiation
emergency.html    Emergency coordination/details
history.html      Previous emergencies
contacts.html     Trusted contact management
facilities.html   Healthcare facility discovery
index.html        Entry redirect to dashboard

44. Frontend File Responsibilities

app.js
↓
Shared application shell, API helper,
theme, language, authentication state,
toasts, common utilities.

auth.js
↓
Login and registration behavior.

dashboard.js
↓
Dashboard statistics and SOS workflow.

emergency.js
↓
Emergency detail, coordination,
notifications, timeline, and resolution.

facilities.js
↓
Facility discovery and nearby facility UI.

contacts.js
↓
Trusted contact management.

history.js
↓
Emergency history UI.

config.js
↓
Frontend API configuration.

style.css
↓
Shared visual system and responsive behavior.

45. Backend Design Relationship

The frontend design maps to the backend API domains:

Authentication
    ↓
/api/auth

Trusted Contacts
    ↓
/api/contacts

Emergencies
    ↓
/api/emergencies

Healthcare Facilities
    ↓
/api/facilities

The UI should not bypass API validation or assume that frontend
validation alone is sufficient.

46. Design Do's

Do

Keep emergency actions obvious.

Use consistent colors.

Use readable typography.

Keep cards logically grouped.

Provide loading states.

Provide meaningful empty states.

Provide clear errors.

Maintain keyboard accessibility.

Test mobile layouts.

Clearly label demo information.

Clearly distinguish recorded actions from real-world actions.

47. Design Don'ts

Don't

Use excessive animation.

Use red for ordinary decorative elements.

Hide emergency status.

Create fake ambulance tracking.

Claim hospital acceptance without confirmation.

Hide important warnings.

Use tiny touch targets.

Remove keyboard focus.

Use inaccessible color-only status indicators.

Display private medical data publicly.

Turn the interface into a visually noisy dashboard.

48. Future Visual Enhancements

Future iterations may introduce:

More polished healthcare illustrations

Facility map visualization

Real-time status indicators when backed by verified integrations

Better mobile bottom navigation

Patient profile cards

Emergency severity visualization

Accessible icon system

Skeleton loading states

Offline-friendly PWA behavior

Improved print templates

Verified provider badges

More advanced facility filters

Any visual enhancement must preserve the project's core principles:

Clarity, accessibility, trust, safety, and honesty.

49. Design Acceptance Checklist

Before considering a UI feature complete:

Works on mobile.

Works on desktop.

Uses shared design tokens.

Has visible keyboard focus.

Has accessible labels.

Uses readable contrast.

Has loading state where needed.

Has error state.

Has empty state where applicable.

Does not expose private data.

Does not imply unsupported real-world functionality.

Respects light/dark themes.

Respects reduced-motion preferences.

Does not break existing navigation.

Does not introduce unnecessary visual complexity.

50. Final Design Principle

MediBridge is an emergency and healthcare coordination interface.

Therefore:

When a user is calm, the interface should feel simple.
When a user is stressed, the interface should become even clearer.

Every design decision should support that principle.