# DocuMind - Semantic Document Cache

🚀 **Redis AI Challenge Submission**

A FastAPI-powered semantic document cache system using Redis Stack for vector search and intelligent document retrieval.

## 🎯 Features

- **Semantic Search**: Vector-based document similarity search
- **Redis Stack Integration**: Leverages Redis for caching and vector operations
- **FastAPI Backend**: Modern, fast API with automatic documentation
- **Document Processing**: Support for PDF, DOCX, and text files
- **Intelligent Caching**: Smart cache invalidation and result optimization
- **Real-time Analytics**: Redis usage statistics and performance metrics

## 🏗️ Architecture

```
documind/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── main.py           # API entry point
│   │   ├── config.py         # Configuration
│   │   ├── database/         # Redis client
│   │   ├── api/              # API endpoints
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utilities
│   └── requirements.txt
├── frontend/          # React frontend (planned)
├── docs/              # Documentation
├── tests/             # Test suites
└── scripts/           # Utility scripts
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Redis Cloud account (free tier available)
- Git

### Setup

1. **Clone and setup:**
   ```bash
   git clone https://github.com/yourusername/documind.git
   cd documind
   ```

2. **Backend setup:**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Configure Redis:**
   ```bash
   cp .env.example .env
   # Edit .env with your Redis Cloud credentials
   ```

4. **Run the API:**
   ```bash
   python -m app.main
   ```

5. **Test the setup:**
   - API Health: http://localhost:8000/health
   - Interactive Docs: http://localhost:8000/docs
   - Redis Stats: http://localhost:8000/api/stats

## 📊 Redis Cloud Setup

1. Visit [Redis Cloud](https://redis.io/try-free/)
2. Create free account (30MB Redis Stack)
3. Create new subscription → **Essentials** → **Redis Stack**
4. Copy connection details to `.env`
5. Test with `/health` endpoint

## 🧪 Development

- **API Documentation**: Available at `/docs` when running
- **Health Checks**: `/health` endpoint for system status
- **Redis Stats**: `/api/stats` for performance monitoring
- **Test Endpoint**: `/api/test` for development testing

## 📝 Next Steps

- [ ] Document upload and processing
- [ ] Vector embedding generation
- [ ] Semantic search implementation
- [ ] Frontend development
- [ ] Performance optimization
- [ ] Deployment configuration

## 🤝 Contributing

This project is part of the Redis AI Challenge. See the setup guides in the docs folder for detailed development instructions.

## 📄 License

MIT License - see LICENSE file for details
