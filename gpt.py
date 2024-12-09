import os
from dotenv import load_dotenv
load_dotenv()
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_gpt(prompt: str) -> str:
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": "你是一個使用繁體中文的聊天機器人。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        # Print Response
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    except openai.error.OpenAIError as e:
        # 處理 OpenAI API 的特定錯誤
        print(f"GPT API 錯誤: {e}")
        return "抱歉，我無法回應您的問題，請稍後再試。"

    except Exception as e:
        # 處理未知錯誤
        print(f"未知錯誤: {e}")
        return "抱歉，我無法回應您的問題，請稍後再試。"