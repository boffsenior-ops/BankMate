docker logs --tail=50 bankmate_celery > celery_logs.txt
docker compose exec backend sh -c "env | grep -E 'ANTHROPIC|OPENAI|QDRANT'" > env_logs.txt
