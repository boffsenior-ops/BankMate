# BankMate

BankMate is an internal, private, on-premise AI assistant for bank branch staff. It works fully self-hosted, allowing staff to ask questions in Uzbek or Russian and get accurate answers with citations, based ONLY on internal bank documents.

## Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.11+

## How to start the infrastructure

1. **Set up environment variables:**
   Copy the example environment file and fill in your secrets if necessary.
   ```bash
   cp .env.example .env
   ```

2. **Start the Docker Compose services:**
   Start PostgreSQL, Redis, Qdrant, and MinIO in the background.
   ```bash
   docker-compose up -d
   ```

3. **Verify services are healthy:**
   Check the status of the containers to ensure they are running and healthy.
   ```bash
   docker-compose ps
   ```
