from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, 
    TextMessage, 
    TextSendMessage,
    ImageSendMessage)
from flagchat import chat, func_table
import openai
import os

from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

api = LineBotApi(os.getenv('LINE_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_SECRET'))

app = Flask(__name__)

@app.post("/")
def callback():
    # 取得 X-Line-Signature 表頭電子簽章內容
    signature = request.headers['X-Line-Signature']

    # 以文字形式取得請求內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 比對電子簽章並處理請求內容
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("電子簽章錯誤, 請檢查密鑰是否正確？")
        abort(400)

    return 'OK'

def txt_to_img_url(prompt):
    response = openai.Image.create(prompt=prompt, n=1, 
                                   size='1024x1024')
    return response['data'][0]['url']

func_table.append(
    {                    # 每個元素代表一個函式
        "chain": False,  # 生圖後不需要傳回給 API
        "func": txt_to_img_url,
        "spec": {        # function calling 需要的函式規格
            "name": "txt_to_img_url",
            "description": "可由文字生圖並傳回圖像網址",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "描述要產生圖像內容的文字",
                    }
                },
                "required": ["prompt"],
            },
        }
    }
)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("收到的消息內容：", event.message.text)  # 調試打印
    for reply in chat('使用繁體中文的小助手', event.message.text):
        print("生成的回覆：", reply)  # 調試打印
        pass

    if reply.startswith('https://'):
        api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url=reply,
                             preview_image_url=reply))
    else:
        api.reply_message(event.reply_token, 
                          TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
