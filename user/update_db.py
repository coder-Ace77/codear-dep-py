from sqlalchemy import text
from app.database import engine

def update_schema():
    with engine.connect() as connection:
        # 1. Add columns to users table
        try:
            print("Adding chat_count_week column to users table...")
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS chat_count_week INTEGER DEFAULT 0"))
            print("Adding last_chat_reset column to users table...")
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_chat_reset TIMESTAMP"))
        except Exception as e:
            print(f"Error updating users table: {e}")

        # 2. Add columns to chat_messages table
        try:
            print("Adding problem_id column to chat_messages table...")
            connection.execute(text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS problem_id VARCHAR"))
        except Exception as e:
            print(f"Error updating chat_messages table: {e}")
            
        connection.commit()
        print("Schema update completed successfully.")

if __name__ == "__main__":
    update_schema()
