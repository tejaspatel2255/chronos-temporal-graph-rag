import sys
from config.settings import settings, validate_settings

def main():
    print("====================================================")
    print("       Project Chronos Scaffolding Initialized      ")
    print("====================================================")
    print(f"Python Version: {sys.version}")
    print(f"Chroma DB Directory: {settings.CHROMA_PERSIST_DIR}")
    print(f"Neo4j URI: {settings.NEO4J_URI}")
    print(f"Neo4j User: {settings.NEO4J_USERNAME}")
    print(f"OpenRouter Base URL: {settings.OPENROUTER_BASE_URL}")
    
    missing = validate_settings()
    if missing:
        print("\n[WARNING] The following required configuration variables are missing:")
        for var in missing:
            print(f"  - {var}")
        print("Please copy .env.example to .env and configure these values.")
    else:
        print("\n[SUCCESS] Environment variables loaded successfully!")

if __name__ == "__main__":
    main()
