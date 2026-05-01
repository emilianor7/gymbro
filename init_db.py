from app.database import init_db, DB_PATH

if __name__ == "__main__":
    init_db()
    print(f"Base inicializada en: {DB_PATH}")
