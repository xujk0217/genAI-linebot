import os
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhooks import TextMessageContent, ImageMessageContent
from linebot.v3.webhook import WebhookHandler, Event
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import TextMessage
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage
from linebot.exceptions import InvalidSignatureError
from linebot.models import ImageSendMessage
from gpt import process_user_input
import cloudinary
import cloudinary.uploader
from gpt import extract_stock_id
from twstock import Stock
import matplotlib
matplotlib.use('Agg')  # For server compatibility
import matplotlib.pyplot as plt
import pandas as pd
from imgurpython import ImgurClient
import logging

# 加載 .env 文件中的變數
load_dotenv()
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# 從環境變數中讀取 LINE 的 Channel Access Token 和 Channel Secret
line_token = os.getenv('LINE_TOKEN')
line_secret = os.getenv('LINE_SECRET')

# 檢查是否設置了環境變數
if not line_token or not line_secret:
    print(f"LINE_TOKEN: {line_token}")  # 調試輸出
    print(f"LINE_SECRET: {line_secret}")  # 調試輸出
    raise ValueError("LINE_TOKEN 或 LINE_SECRET 未設置")

# 初始化 LineBotApi 和 WebhookHandler
line_bot_api = LineBotApi(line_token)
handler = WebhookHandler(line_secret)

# 創建 Flask 應用
app = Flask(__name__)

app.logger.setLevel(logging.DEBUG)

# 設置一個路由來處理 LINE Webhook 的回調請求
@app.route("/", methods=['POST'])
def callback():
    # 取得 X-Line-Signature 標頭
    signature = request.headers['X-Line-Signature']

    # 取得請求的原始內容
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # 驗證簽名並處理請求
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def upload_to_cloudinary(file_path, public_id=None):
    """上傳圖片到 Cloudinary 並返回 URL"""
    try:
        response = cloudinary.uploader.upload(file_path, public_id=public_id)
        return response['secure_url']  # 使用 HTTPS 的 URL
    except Exception as e:
        print(f"圖片上傳失敗: {e}")
        return None
    


# 設置一個事件處理器來處理 TextMessage 事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: Event):
    if event.message.type == "text":
        user_message = event.message.text  # 使用者的訊息
        app.logger.info(f"收到的訊息: {user_message}")

        # 使用 GPT 生成回應
        reply_text = process_user_input(user_message)

        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextMessage(text=reply_text)
        # )

        stock_id = extract_stock_id(user_message)
        try:
            for sid in stock_id:
                stock = Stock(sid)
                fn = '%s.png' % (sid)
                stock = Stock(sid)
                stock_data = {'close': stock.close, 'date': stock.date, 'high': stock.high, 'low': stock.low, 'open': stock.open}
                df = pd.DataFrame.from_dict(stock_data)

                df.plot(x='date', y='close')
                plt.title(f'{sid} five-day stock price')
                plt.savefig(fn)
                plt.close()

                image_url = upload_to_cloudinary(fn, public_id=f"stocks/{sid}")
                if image_url:
                    image_message = ImageMessageContent(
                        id=event.message.id,
                        original_content_url=image_url, 
                        preview_image_url=image_url,
                        contentProvider={"type": "line", "id": "content_provider_id"}
                        )
                else:
                    # 上傳失敗處理
                    image_message = (TextMessageContent(
                        id=event.message.id,
                        text="圖片上傳失敗，請稍後再試。",
                        quoteToken=event.reply_token
                        ))

                # 刪除本地圖片文件
                if os.path.exists(fn):
                    os.remove(fn)
            line_bot_api.reply_message(
                event.reply_token,
                TextMessageContent(
                    id=event.message.id,
                    text=reply_text,
                    quoteToken=event.reply_token
                    ),
                image_message
            )   
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessageContent(
                    id=event.message.id,
                    text=reply_text,
                    quoteToken=event.reply_token
                    )
            )   
# 應用程序入口點
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
