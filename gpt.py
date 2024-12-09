import os
from dotenv import load_dotenv
load_dotenv()
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_gpt(prompt: str) -> str:
    """
    使用 OpenAI GPT 模型生成回應。
    :param prompt: 使用者輸入的提示
    :return: GPT 模型生成的回應
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": "你好！"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        # Print Response
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"GPT API 錯誤: {e}")
        return "抱歉，我無法回應您的問題，請稍後再試。"
