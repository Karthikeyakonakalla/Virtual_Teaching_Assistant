# VTA JEE Setup Guide

## Prerequisites

- Python 3.8 or higher
- Git
- Groq API key

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/vta-jee.git
cd vta-jee
```

### 2. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Sign in with your account
3. Click "Get API Key"
4. Copy the generated API key

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Groq API key
# Replace 'your-groq-api-key-here' with your actual key
```

### 4. Run Setup Script

#### Windows:
```bash
python run.py
```

#### Linux/Mac:
```bash
python3 run.py
```

Follow the prompts to:
- Install dependencies
- Initialize the database
- Load the knowledge base

### 5. Access the Application

Once the server starts, open your browser and navigate to:
```
http://localhost:5000
```

## Manual Setup

If you prefer manual setup:

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
python init_db.py
```

### 4. Load Knowledge Base

```bash
python scripts/load_knowledge_base.py
```

### 5. Run the Application

```bash
python app.py
```

## Docker Setup

### 1. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d
```

### 2. Stop Services

```bash
docker-compose down
```

## Using the Application

### Input Methods

1. **Text Input**
   - Type your JEE question directly
   - Select subject (optional - auto-detected)
   - Click "Get Solution"

2. **Voice Input**
   - Click the microphone button
   - Speak your question clearly
   - Click stop when done
   - Review the transcription

3. **Image Input**
   - Drag and drop or click to upload
   - Supported formats: JPG, PNG, PDF
   - Add context if needed
   - Click "Analyze Image"

### Features

- **Step-by-Step Solutions**: Detailed explanations with intermediate steps
- **LaTeX Rendering**: Mathematical expressions rendered beautifully
- **Audio Output**: Listen to solutions with text-to-speech
- **References**: See which knowledge sources were used
- **Confidence Score**: Understand solution reliability
- **Feedback System**: Rate and comment on solutions

## Troubleshooting

### Common Issues

1. **"Groq API key not set" error**
   - Ensure you've added your API key to the `.env` file
   - Restart the application after adding the key

2. **"Module not found" errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check that you're in the virtual environment

3. **"Port 5000 already in use"**
   - Another application is using port 5000
   - Stop the other application or change the port in `app.py`

4. **OCR/Image processing not working**
   - Ensure the image is clear and readable
   - Try different image formats (JPG, PNG)
   - Add context to help the AI understand

5. **Audio features not working**
   - Check microphone permissions in your browser
   - Ensure your browser supports Web Audio API

### Browser Compatibility

Recommended browsers:
- Google Chrome (latest)
- Mozilla Firefox (latest)
- Microsoft Edge (latest)
- Safari 14+

## Development

### Project Structure

```
vta-jee/
├── app.py              # Main Flask application
├── api/                # API endpoints
├── services/           # Core services (Groq, RAG, etc.)
├── models/             # Database models
├── static/             # Frontend assets
├── templates/          # HTML templates
├── knowledge_base/     # Knowledge corpus
└── scripts/            # Utility scripts
```

### Adding Knowledge Content

1. **NCERT Content**: Add JSON files to `knowledge_base/ncert/{subject}/`
2. **Formulas**: Update `knowledge_base/formulas/{subject}.json`
3. **Past Papers**: Add to `knowledge_base/past_papers/`

After adding content, reload the knowledge base:
```bash
python scripts/load_knowledge_base.py
```

### API Endpoints

- `POST /api/query` - Submit a question
- `GET /api/query/<id>` - Get query result
- `POST /api/feedback` - Submit feedback
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - User login

## Performance Tips

1. **Knowledge Base Optimization**
   - Keep passages concise (100-300 tokens)
   - Index by subject and topic for faster retrieval
   - Update embeddings when adding new content

2. **Response Time**
   - Text queries: ~2-5 seconds
   - Image queries: ~5-10 seconds
   - Audio queries: ~3-7 seconds

3. **Scaling**
   - Use Redis for caching frequent queries
   - Deploy with Docker for easy scaling
   - Consider GPU for faster embeddings

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the README.md
3. Open an issue on GitHub

## License

This project is licensed under the MIT License.
