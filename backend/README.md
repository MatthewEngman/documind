# DocuMind Backend

FastAPI-based backend for the DocuMind semantic document cache system.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Redis Cloud credentials
   ```

3. **Run the server:**
   ```bash
   python -m app.main
   ```

4. **Test the API:**
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs
   - Redis stats: http://localhost:8000/api/stats

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database/
│   │   └── redis_client.py  # Redis operations
│   ├── api/                 # API endpoints
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── requirements.txt
├── .env.example
└── README.md
```

## Redis Cloud Setup

1. Create account at [Redis Cloud](https://redis.io/try-free/)
2. Create new database with Redis Stack
3. Copy connection details to `.env`
4. Test connection with `/health` endpoint
