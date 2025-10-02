# JEE Mains Virtual Teaching Assistant (VTA)

An AI-powered Virtual Teaching Assistant for JEE Mains preparation that provides step-by-step, syllabus-aligned solutions for Mathematics, Physics, and Chemistry questions.

## Features

- **Multi-modal Input Support**
  - Text input via typing
  - Voice input via microphone (Speech-to-Text)
  - Image input (handwritten/printed problems) via OCR
  
- **Intelligent Answer Generation**
  - RAG (Retrieval-Augmented Generation) pipeline
  - Grounded in NCERT content, formula sheets, and past papers
  - Step-by-step solutions with intermediate steps
  - LaTeX rendering for mathematical expressions
  
- **Dual Output Format**
  - Formatted text with collapsible explanations
  - Audio output via Text-to-Speech
  
- **Knowledge Base**
  - Curated NCERT chapters
  - Topic-wise formula sheets
  - Previous year JEE questions and solutions
  - Exemplar problems

## Tech Stack

- **Backend**: Python Flask REST API
- **AI/ML**: Groq API with Llama 4 Scout (LLM, Vision, OCR)
- **Vector Database**: FAISS for semantic search
- **Frontend**: HTML/CSS/JavaScript with MathJax
- **Database**: SQLite for user data and logs
- **Containerization**: Docker

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vta-jee.git
cd vta-jee
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

5. Initialize the database:
```bash
python init_db.py
```

6. Load knowledge base:
```bash
python scripts/load_knowledge_base.py
```

7. Run the application:
```bash
python app.py
```

## Usage

1. Access the application at `http://localhost:5000`
2. Choose your input method:
   - Type your question
   - Click the microphone to speak
   - Upload an image of the problem
3. Get step-by-step solutions with references
4. Listen to audio explanations if needed

## Project Structure

```
vta-jee/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
│
├── api/                  # API endpoints
│   ├── __init__.py
│   ├── query.py         # Query handling routes
│   ├── auth.py          # Authentication routes
│   └── feedback.py      # User feedback routes
│
├── services/            # Core services
│   ├── __init__.py
│   ├── gemini_client.py    # Groq API integration (Llama 4 Scout)
│   ├── ocr_service.py      # OCR processing
│   ├── stt_service.py      # Speech-to-Text
│   ├── tts_service.py      # Text-to-Speech
│   ├── rag_pipeline.py     # RAG implementation
│   └── solution_formatter.py # Solution formatting
│
├── models/              # Data models
│   ├── __init__.py
│   ├── user.py         # User model
│   ├── query.py        # Query model
│   └── feedback.py     # Feedback model
│
├── database/           # Database utilities
│   ├── __init__.py
│   ├── connection.py   # DB connection
│   └── migrations/     # DB migrations
│
├── knowledge_base/     # Knowledge corpus
│   ├── ncert/         # NCERT chapters
│   ├── formulas/      # Formula sheets
│   ├── past_papers/   # Previous year papers
│   └── index/         # Vector index files
│
├── static/            # Frontend static files
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/         # HTML templates
│   ├── index.html
│   ├── base.html
│   └── components/
│
├── scripts/           # Utility scripts
│   ├── load_knowledge_base.py
│   ├── create_embeddings.py
│   └── evaluate_model.py
│
└── tests/             # Test files
    ├── test_api.py
    ├── test_rag.py
    └── test_services.py
```

## API Endpoints

- `POST /api/query` - Submit a question (text/audio/image)
- `GET /api/query/<id>` - Get query result
- `POST /api/feedback` - Submit feedback
- `GET /api/history` - Get query history
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
