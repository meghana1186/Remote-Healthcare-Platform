# Docker troubleshooting

From the repository root:

docker compose down
docker compose build --no-cache api worker
docker compose up

Backend check:
http://localhost:8000/health

API docs:
http://localhost:8000/docs

If API fails:
docker compose logs api --tail=200

If worker fails:
docker compose logs worker --tail=200

Do not expose or commit the GROQ_API_KEY from .env.
