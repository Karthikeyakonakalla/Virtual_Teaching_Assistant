"""Simple script to run the VTA JEE application."""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are met."""
    print("Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        return False
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("Creating .env file from template...")
        if Path('.env.example').exists():
            with open('.env.example', 'r') as f:
                content = f.read()
            with open('.env', 'w') as f:
                f.write(content)
            print("✓ .env file created. Please add your Groq API key.")
        else:
            print("ERROR: .env.example file not found")
            return False
    
    # Check if Groq API key is set
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('GROQ_API_KEY') or os.getenv('GROQ_API_KEY') == 'your-groq-api-key-here':
        print("\n⚠️  WARNING: Groq API key not set!")
        print("Please edit the .env file and add your Groq API key.")
        print("You can get one from: https://console.groq.com/")
        return False
    
    return True


def install_dependencies():
    """Install required dependencies."""
    print("\nInstalling dependencies...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies")
        return False


def initialize_database():
    """Initialize the database."""
    print("\nInitializing database...")
    
    try:
        subprocess.check_call([sys.executable, 'init_db.py'])
        print("✓ Database initialized successfully")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Failed to initialize database")
        return False


def load_knowledge_base():
    """Load the knowledge base."""
    print("\nLoading knowledge base...")
    
    try:
        subprocess.check_call([sys.executable, 'scripts/load_knowledge_base.py'])
        print("✓ Knowledge base loaded successfully")
        return True
    except subprocess.CalledProcessError:
        print("WARNING: Failed to load knowledge base. The app will still work but without RAG features.")
        return True  # Continue anyway


def run_application():
    """Run the Flask application."""
    print("\n" + "="*50)
    print("Starting VTA JEE Application...")
    print("="*50)
    print("\nThe application will be available at:")
    print("  → http://localhost:5000")
    print("\nPress Ctrl+C to stop the server\n")
    print("="*50 + "\n")
    
    try:
        subprocess.call([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n\nApplication stopped.")


def main():
    """Main execution function."""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║     VTA JEE - Virtual Teaching Assistant        ║
    ║         for JEE Mains Preparation               ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        return
    
    # Ask user if they want to install dependencies
    response = input("\nDo you want to install/update dependencies? (y/n): ").lower()
    if response == 'y':
        if not install_dependencies():
            return
    
    # Check if database exists
    if not Path('vta_jee.db').exists():
        response = input("\nDatabase not found. Initialize database? (y/n): ").lower()
        if response == 'y':
            if not initialize_database():
                return
    
    # Check if knowledge base index exists
    if not Path('knowledge_base/index/faiss_index.index').exists():
        response = input("\nKnowledge base index not found. Load knowledge base? (y/n): ").lower()
        if response == 'y':
            load_knowledge_base()
    
    # Run the application
    run_application()


if __name__ == '__main__':
    main()
