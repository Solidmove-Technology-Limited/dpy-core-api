# SolidMove Access — V1 Build Specification

**Company:** SOLIDMOVE TECHNOLOGY LIMITED  
**Ecosystem:** Steph-Tech  
**Backend:** Pyramide / DPY Core  
**Governance:** UMBRAE  
**Status:** In development  
**Working branch:** feature/solidmove-access-v1

## Product objective

SolidMove Access is the identity and authentication entry point for SolidMove services. V1 must provide secure registration, sign-in, account recovery, profile management, and auditable account-security controls.

## V1 scope

1. Registration with verified email, unique username, and securely hashed password.
2. Sign-in with generic failure messages and rate limiting.
3. Email verification before an account is treated as fully verified.
4. Password-reset request that does not reveal whether an email is registered.
5. Cryptographically random, single-use, expiring reset tokens. Store only a hash of each token; invalidate outstanding reset tokens after successful password change.
6. Session lifecycle: short-lived access tokens, refresh-token rotation, revocation/logout, and clear expiry rules.
7. Authenticated profile and account-security settings.
8. Audit events for security-relevant actions without recording passwords, raw tokens, or reset secrets.
9. Tests for successful flows, invalid credentials, expiry, reuse, rate limits, and unauthorized access.

## Architecture

- Client: SolidMove Access web/mobile interface (implementation target to be confirmed).
- API: existing FastAPI service in dpy-core-api.
- Persistence: existing SQLAlchemy database layer; add migration-managed tables for verification/reset tokens and refresh sessions.
- Email: configurable transactional email provider; credentials supplied only through deployment secrets.
- Governance: UMBRAE-aligned audit events and permission checks.

## Existing repository findings

- Existing routes: /auth/register, /auth/login, /users/me.
- Existing password hashing and JWT helpers are present in app/security.py.
- Existing refresh-token helper is not yet exposed as a complete rotation/revocation API.
- Password-reset request, verification, and completion flow are not present in the inspected source.
- Current /health response reports configuration flags; it does not establish database or email-provider readiness.

## Acceptance criteria

- A user can register, verify their email, sign in, and access only their own authenticated profile.
- A user can request a reset without account enumeration; a valid reset link works once and expires.
- Expired, malformed, or reused reset tokens are rejected.
- Password changes revoke existing refresh sessions.
- Login and reset endpoints have abuse controls.
- Security events are auditable without leaking secrets.
- Automated tests pass against an isolated test database.
- Deployment readiness is checked separately from local test success.

## Build sequence

1. Confirm client target and deployment/email-provider choices.
2. Implement backend account recovery and session lifecycle on this feature branch.
3. Add automated tests and database migrations.
4. Build the SolidMove Access client and connect it to the API.
5. Run end-to-end security tests and document deployment readiness.

## Security rules

Never commit API keys, SMTP credentials, JWT secrets, production database URLs, passwords, or raw reset tokens. Use environment secrets, HTTPS, secure token storage, and production-grade database migrations. Do not claim production readiness until tests and live health checks have passed.