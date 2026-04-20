# Database Notes

This project uses SQLite by default for local development.

- DB file path: `database/forest_fire.db`
- Tables:
  - `search_history`
  - `pinned_locations`

To switch to MongoDB, replace SQLAlchemy CRUD logic in `backend/app/db/` with Mongo collections and keep API contracts unchanged.
