# Seatwise

An events platform. Organizers publish events; attendees discover them, reserve seats, save favorites, comment, and review events they attended.

The project is built around the problems the domain forces:

- **Capacity under concurrency:** two people cannot take the last seat.
- **Integrity across collections:** a reservation, its event's seat count, and a cancellation always agree.
- **Rules that depend on time and history:** you can review only an event you attended, after it ended.
- **Moderation:** comments written by one user, hidden by another.

> **Status:** phase 0, project setup. See [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for the full specification and the phase plan.

## Stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.14, FastAPI, Motor, Pydantic, PyJWT, Argon2, Pillow, uv |
| Frontend | React, TypeScript, Vite, TanStack Router, TanStack Query, Zustand, React Hook Form, Zod, Tailwind CSS |
| Database | MongoDB 9.0 as a single-node replica set (transactions) |
| Tests | pytest + httpx, Vitest + Testing Library |
| Delivery | Docker Compose for production, GitHub Actions |

## Documentation

- [PROJECT_BRIEF.md](PROJECT_BRIEF.md): domain, data model, rules, API, permissions and phases
- [CLAUDE.md](CLAUDE.md): conventions and the definition of done
- [docs/decisions.md](docs/decisions.md): decisions and the reasons behind them

Setup instructions will be added with the backend and frontend skeletons.

## License

MIT. See [LICENSE](LICENSE).
