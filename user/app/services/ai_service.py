import httpx
import os
from sqlalchemy.orm import Session
from app.models.user import ChatMessage, User

class AiService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv("OPEN_AI_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def get_ai_response(self, user: User, problem_statement: str, code: str, user_message: str):
        system_prompt = f"You are an expert coding assistant. Context:\nProblem: {problem_statement}\nUser's Current Code: {code}\nKeep answers concise."
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            data = response.json()
            ai_reply = data["choices"][0]["message"]["content"]

            # Save to DB
            self.save_message(user.id, user_message, "user")
            self.save_message(user.id, ai_reply, "assistant")
            
            return ai_reply

    def save_message(self, user_id, content, role):
        msg = ChatMessage(user_id=user_id, content=content, role=role)
        self.db.add(msg)
        self.db.commit()