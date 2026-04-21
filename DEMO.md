# Demo: Quick Walkthrough

1. Start backend (see README).
2. Open `FRONTEND/admin/admin.html` in a browser and update `API_BASE` at top of `admin.js` to point to `http://localhost:5000`.
3. Submit an example via `/submit` (use Postman or the AI Lab input) and verify it appears in Reports.
4. In AI Lab, click `Build Index`, then use `Search similar reports` to find related issues.
5. Use `Explain` on a report row to view priority breakdown.

Use `pytest` to run automated checks; see `BACKEND/tests` for examples.
