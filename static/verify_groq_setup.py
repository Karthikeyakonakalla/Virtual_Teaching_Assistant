"""Verification script to ensure Groq setup is complete."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_api_key():
    """Check if Groq API key is set."""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key or api_key == 'your-groq-api-key-here':
        print("❌ GROQ_API_KEY not set in .env file")
        return False
    print(f"✅ GROQ_API_KEY is set: {api_key[:20]}...")
    return True

def check_groq_package():
    """Check if groq package is installed."""
    try:
        import groq
        print(f"✅ groq package is installed (version: {groq.__version__ if hasattr(groq, '__version__') else 'unknown'})")
        return True
    except ImportError:
        print("❌ groq package is not installed. Run: pip install groq==0.4.1")
        return False

def test_groq_client():
    """Test Groq client initialization."""
    try:
        from services.gemini_client import GeminiClient
        client = GeminiClient()
        print(f"✅ Groq client initialized successfully with model: {client.model}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {str(e)}")
        return False

def test_ocr_service():
    """Test OCR service initialization."""
    try:
        from services.ocr_service import OCRService
        ocr = OCRService()
        print(f"✅ OCR service initialized successfully with model: {ocr.model}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize OCR service: {str(e)}")
        return False

def test_rag_pipeline():
    """Test RAG pipeline initialization."""
    try:
        from services.rag_pipeline import RAGPipeline
        rag = RAGPipeline()
        print(f"✅ RAG pipeline initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize RAG pipeline: {str(e)}")
        return False

def check_no_gemini_references():
    """Check that no Gemini packages are in use."""
    try:
        import google.generativeai
        print("⚠️  WARNING: google-generativeai is still installed (not needed)")
        return False
    except ImportError:
        print("✅ No Gemini packages found (clean migration)")
        return True

def main():
    """Run all verification checks."""
    print("="*60)
    print("VTA JEE - Groq Migration Verification")
    print("="*60)
    print()
    
    results = []
    
    print("1. Checking API Key Configuration...")
    results.append(check_api_key())
    print()
    
    print("2. Checking Groq Package Installation...")
    results.append(check_groq_package())
    print()
    
    print("3. Testing Groq Client Initialization...")
    results.append(test_groq_client())
    print()
    
    print("4. Testing OCR Service...")
    results.append(test_ocr_service())
    print()
    
    print("5. Testing RAG Pipeline...")
    results.append(test_rag_pipeline())
    print()
    
    print("6. Checking for Legacy Packages...")
    results.append(check_no_gemini_references())
    print()
    
    print("="*60)
    if all(results):
        print("🎉 SUCCESS! All checks passed!")
        print("Your VTA JEE application is fully migrated to Groq API.")
        print()
        print("Next steps:")
        print("  1. Run the application: python app.py")
        print("  2. Visit: http://localhost:5000")
        print("="*60)
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
