import os
from dotenv import load_dotenv
load_dotenv()
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

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
