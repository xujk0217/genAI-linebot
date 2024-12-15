import os
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhooks import WebhookHandler, Event
from linebot.v3.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, ImageSendMessage, MessageEvent, TextMessage
from gpt import process_user_input, extract_stock_id
import cloudinary
import cloudinary.uploader
from twstock import Stock
import matplotlib
matplotlib.use('Agg')  # For server compatibility
import matplotlib.pyplot as plt
import pandas as pd
import logging

# Load .env variables
load_dotenv()
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Read LINE Channel Access Token and Channel Secret
line_token = os.getenv('LINE_TOKEN')
line_secret = os.getenv('LINE_SECRET')

if not line_token or not line_secret:
    raise ValueError("LINE_TOKEN or LINE_SECRET not set in the environment variables.")

# Initialize LINE Messaging API and WebhookHandler
messaging_api = MessagingApi(channel_access_token=line_token)
handler = WebhookHandler(line_secret)

# Create Flask application
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# Flask route for LINE Webhook
@app.route("/", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def upload_to_cloudinary(file_path, public_id=None):
    """Upload an image to Cloudinary and return its URL."""
    try:
        response = cloudinary.uploader.upload(file_path, public_id=public_id)
        return response['secure_url']
    except Exception as e:
        print(f"Image upload failed: {e}")
        return None

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: Event):
    user_message = event.message.text
    app.logger.info(f"Received message: {user_message}")

    # Use GPT to process user input (if needed)
    reply_text = process_user_input(user_message)

    # Extract stock IDs from user message
    stock_ids = extract_stock_id(user_message)

    try:
        reply_messages = []

        for sid in stock_ids:
            stock = Stock(sid)
            file_name = f'{sid}.png'

            # Prepare stock data for plotting
            stock_data = {
                'close': stock.close,
                'date': stock.date,
                'high': stock.high,
                'low': stock.low,
                'open': stock.open
            }
            df = pd.DataFrame.from_dict(stock_data)

            # Plot stock data
            df.plot(x='date', y='close')
            plt.title(f'{sid} five-day stock price')
            plt.savefig(file_name)
            plt.close()

            # Upload the image to Cloudinary
            image_url = upload_to_cloudinary(file_name, public_id=f"stocks/{sid}")

            if image_url:
                reply_messages.append(ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                ))
            else:
                reply_messages.append(TextSendMessage(text="Image upload failed. Please try again later."))

            # Remove the local file
            if os.path.exists(file_name):
                os.remove(file_name)

        # If no stock IDs were processed, send a default reply
        if not reply_messages:
            reply_messages.append(TextSendMessage(text="No valid stock IDs found in your message."))

        # Reply to the user
        messaging_api.reply_message(
            reply_token=event.reply_token,
            messages=reply_messages
        )
    except Exception as e:
        app.logger.error(f"Error processing message: {e}")
        messaging_api.reply_message(
            reply_token=event.reply_token,
            messages=[TextSendMessage(text=f"An error occurred: {str(e)}")]
        )

# Main entry point for the application
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
