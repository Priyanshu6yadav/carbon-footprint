<USER_REQUEST>
# CarbonTrack — Phased Build Prompt for AI Coding Agents

> **How to use this file:** Feed one phase at a time to your AI agent (Claude Code, Cursor, etc.). Don't paste the whole thing at once — agents produce shallower work when asked to do everything simultaneously. Finish and verify Phase 0–1 before moving on. Each phase says explicitly what "done" looks like.

---

## ⚠️ Secret Handling — Read Before Phase 0

Never paste real API keys into a prompt, a chat with an AI agent, or commit them to git.

- All secrets live in a `.env` file (gitignored), referenced as environment variables.
- The agent should be told to use `os.getenv("GROQ_API_KEY")` (Python) or `process.env.GROQ_API_KEY` (Node), **never** a literal string.
- Ship a `.env.example` with empty placeholders so the repo is safe to make public.
- If a key is ever pasted anywhere outside your local `.env` — chat, GitHub issue, Discord — rotate it immediately in the provider's console.

```
# .env.example
GROQ_API_KEY=
DATABASE_URL=
JWT_SECRET=
JWT_REFRESH_SECRET=
REDIS_URL=
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
```

---

## Project Brief (give this to the agent as shared context every phase)

Build **CarbonTrack**, a full-stack carbon footprint awareness platform where users calculate emissions, track eco-habits, get AI-personalized sustainability advice, and stay motivated through gamification and analytics.

**Tech stack:**
- Frontend: React + TypeScript, Tailwind CSS, ShadCN UI, Recharts, Framer Motion
- Backend: FastAPI (Python), Pydantic v2
- Database: PostgreSQL (SQLAlchemy or SQLModel + Alembic migrations)
- Cache/Queue: Redis
- AI: Groq API (OpenAI-compatible chat completions endpoint), model `llama-3.3-70b-versatile` or similar — loaded via `GROQ_API_KEY` env var
- Auth: JWT access + refresh tokens, bcrypt password hashing, optional Google OAuth
- Deployment: Docker Compose locally, GitHub Actions CI

**Design direction:** Clean, premium SaaS aesthetic (think Linear/Notion, not a generic Bootstrap te
<truncated 7111 bytes>
itignored, `.env.example` committed instead, secrets never logged.
- [ ] Audit logging: log auth events and admin actions (who/when/what), not full request bodies (avoid logging PII/passwords).
- [ ] Dependency hygiene: `pip-audit` / `npm audit` in CI.

Drop from the original list: CSRF protection (not meaningful for a stateless JWT-bearer API unless you're also using cookies for auth state — if you do use httpOnly refresh cookies, add `SameSite=Strict` instead, which is the actual mitigation), and generic "OWASP best practices" as a line item — replace with the specific OWASP Top 10 items you've actually addressed above.

---

## What Changed From Your Original Draft (so you can explain it to judges)

- **Phased instead of all-at-once:** judges and reviewers can see a coherent MVP rather than 12 half-finished subsystems.
- **Groq key handled via environment variable**, never hardcoded — this alone is something experienced judges specifically check for and penalize when missing.
- **Emission factors sourced and stored as config**, not arbitrary numbers — makes the "carbon calculator" defensible if anyone asks where the numbers came from.
- **AI outputs are validated/clamped and cached** — prevents the advisor from hallucinating impossible stats live in front of judges, and avoids surprise Groq quota burn.
- **XP/badges are server-side and rule-based**, not AI-assigned — closes an obvious cheating vector.
- **Removed unimplementable security theater** (generic CSRF mention on a token API, "OWASP best practices" with no specifics) in favor of a short list you can actually point to in the running app.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-06-18T00:08:36+05:30.
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from None to Claude Sonnet 4.6 (Thinking). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>