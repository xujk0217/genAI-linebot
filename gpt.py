import os
from dotenv import load_dotenv
load_dotenv()
import openai
import requests
import json
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")

# def chat_with_gpt(prompt: str) -> str:
    
#     try:
#         response = openai.chat.completions.create(
#             model="gpt-3.5-turbo", 
#             messages=[
#                 {"role": "system", "content": "你是一個使用繁體中文的聊天機器人。"},
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=100,
#             temperature=0.7
#         )
#         # Print Response
#         print(response.choices[0].message.content)
#         return response.choices[0].message.content
    
#     except openai.error.OpenAIError as e:
#         # 處理 OpenAI API 的特定錯誤
#         print(f"GPT API 錯誤: {e}")
#         return "抱歉，我無法回應您的問題，請稍後再試。"

#     except Exception as e:
#         # 處理未知錯誤
#         print(f"未知錯誤: {e}")
#         return "抱歉，我無法回應您的問題，請稍後再試。"
    


#---------------------------------------------------
# Test
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def get_stock_data(symbol: str, interval: str = "5min", outputsize: str = "compact", month: str = None) -> str:
    """
    查詢 Alpha Vantage API，根據參數取得股票數據。
    """
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": interval,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "outputsize": outputsize
    }
    if month:
        params["month"] = month

    response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if "Time Series" in data:
            return "成功取得數據，請檢查回應內容。"
        else:
            return f"無法查詢到 {symbol} 的數據，請檢查輸入的股票代碼。"
    else:
        return "無法連接至 Alpha Vantage API，請稍後再試。"


def parse_user_input(prompt: str) -> dict:
    """
    使用 GPT 解析使用者輸入，提取股票相關參數或判斷為一般問題。
    """
    try:
        response = openai.chat.completions.create(...)
        content = response.choices[0].message.content
        return json.loads(content)  # Safer alternative to eval()
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return {"type": "error", "message": "解析錯誤"}

def chat_with_gpt(prompt: str) -> str:
    """
    處理使用者輸入，結合 OpenAI 和 Alpha Vantage API 回應。
    """
    try:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Received user input: %s", prompt)
        # 使用 GPT 解析使用者輸入
        parsed_input = parse_user_input(prompt)

        if parsed_input.get("type") == "stock":
            # 股票相關查詢
            symbol = parsed_input.get("symbol")
            interval = parsed_input.get("interval", "5min")
            outputsize = parsed_input.get("outputsize", "compact")
            month = parsed_input.get("month")

            # 查詢股票 API
            stock_response = get_stock_data(symbol, interval, outputsize, month)
            return stock_response

        elif parsed_input.get("type") == "error":
            return parsed_input.get("message", "解析失敗，請稍後再試。")

        else:
            # 使用 OpenAI GPT 處理其他一般問題
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個使用繁體中文的聊天機器人。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            return response.choices[0].message.content
    except Exception as e:
        # 處理未知錯誤
        print(f"未知錯誤: {e}")
        return "抱歉，我無法回應您的問題，請稍後再試。"
