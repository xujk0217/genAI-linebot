import os
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest
from linebot.v3.webhooks import WebhookHandler, Event
from linebot.v3.webhooks import TextMessageContent, ImageMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import TextMessage
import cloudinary
import cloudinary.uploader
from gpt import process_user_input, extract_stock_id
from twstock import Stock
import matplotlib
matplotlib.use('Agg')  # For server compatibility
import matplotlib.pyplot as plt
import pandas as pd
import io
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
messaging_api = MessagingApi(channel_access_token=line_token)

# 檢查是否設置了環境變數
if not line_token or not line_secret:
    print(f"LINE_TOKEN: {line_token}")  # 調試輸出
    print(f"LINE_SECRET: {line_secret}")  # 調試輸出
    raise ValueError("LINE_TOKEN 或 LINE_SECRET 未設置")

# 初始化 WebhookHandler
handler = WebhookHandler(line_secret)

# 創建 Flask 應用
app = Flask(__name__)

app.logger.setLevel(logging.DEBUG)

# 設置一個路由來處理 LINE Webhook 的回調請求
@app.route("/", methods=['POST'])
def callback():
    # 取得 X-Line-Signature 標頭
    signature = request.headers.get('X-Line-Signature')

    # 取得請求的原始內容
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # 驗證簽名並處理請求
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def upload_to_cloudinary(image_data, public_id=None):
    """上傳圖片到 Cloudinary 並返回 URL"""
    try:
        response = cloudinary.uploader.upload(image_data, public_id=public_id)
        return response['secure_url']  # 使用 HTTPS 的 URL
    except Exception as e:
        app.logger.error(f"圖片上傳失敗: {e}")
        return None

# 設置一個事件處理器來處理 TextMessage 事件
@handler.add(Event)
def handle_message(event: Event):
    if isinstance(event.message, TextMessageContent):
        user_message = event.message.text  # 使用者的訊息
        app.logger.info(f"收到的訊息: {user_message}")

        # 使用 GPT 生成回應
        reply_text = process_user_input(user_message)

        # 處理股票代碼並生成圖片
        stock_id = extract_stock_id(user_message)
        messages = [TextMessageContent(text=reply_text)]  # 儲存回應訊息

        for sid in stock_id:
            stock = Stock(sid)
            stock_data = {
                'date': stock.date,
                'open': stock.open,
                'high': stock.high,
                'low': stock.low,
                'close': stock.close
            }
            df = pd.DataFrame.from_dict(stock_data)

            # 繪製圖片
            plt.figure(figsize=(10, 5))
            df.plot(x='date', y='close')
            plt.title(f'{sid} five-day stock price')
            plt.xlabel('Date')
            plt.ylabel('Close Price')

            # 保存圖片至 BytesIO
            image_buffer = io.BytesIO()
            plt.savefig(image_buffer, format='png')
            plt.close()
            image_buffer.seek(0)

            # 上傳到 Cloudinary
            image_url = upload_to_cloudinary(image_buffer, public_id=f"stocks/{sid}")
            if image_url:
                messages.append(ImageMessageContent(
                    original_content_url=image_url,
                    preview_image_url=image_url
                ))
            else:
                messages.append(TextMessageContent(text=f"無法生成 {sid} 的圖片，請稍後再試。"))

        # 發送回應
        reply_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages
        )
        messaging_api.reply_message(reply_request)

# 應用程序入口點
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
