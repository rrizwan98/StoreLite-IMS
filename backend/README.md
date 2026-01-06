---
title: Schema Query Agent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Schema Query Agent API

AI-powered natural language database query agent deployed on Hugging Face Spaces.

## Features

- **Natural Language Queries**: Ask questions in plain English, get SQL results
- **7 Integrated Tools**:
  - WebSearch (Google Search)
  - FileSearch (Semantic file search)
  - Analytics (Data visualization)
  - Gmail (Email integration)
  - GDrive (Google Drive)
  - Notion (Workspace integration)
  - RetellAI (Voice agent)
- **File Processing**: PDF, Excel, CSV, Images
- **OAuth Connectors**: Connect your external services

## Quick Start

1. **Connect Your Database**
   ```
   POST /schema-agent/connect
   {
     "database_uri": "postgresql://user:pass@host:5432/db"
   }
   ```

2. **Query with Natural Language**
   ```
   POST /schema-agent/chatkit
   {
     "message": "How many orders were placed last month?"
   }
   ```

## API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Environment Variables

Set these in HF Space Settings > Variables:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key (optional) |
| `LLM_PROVIDER` | "gemini" or "openai" |
| `GOOGLE_API_KEY` | For Google Search |
| `GOOGLE_CSE_ID` | Custom Search Engine ID |
| `GOOGLE_CLIENT_ID` | OAuth for Gmail/GDrive |
| `GOOGLE_CLIENT_SECRET` | OAuth secret |
| `NOTION_CLIENT_ID` | Notion OAuth |
| `NOTION_CLIENT_SECRET` | Notion secret |
| `RETELL_API_KEY` | Retell AI key |
| `TOKEN_ENCRYPTION_KEY` | For OAuth token encryption |

## Local Development

1. Install dependencies: `pip install -e .`
2. Create `.env` file with configuration
3. Run FastAPI: `uvicorn app.main:app --reload`
4. Access API docs: http://localhost:8000/docs

## License

MIT
