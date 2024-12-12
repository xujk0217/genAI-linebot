import os
from dotenv import load_dotenv
load_dotenv()
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
import requests

# Alpha Vantage API 設定
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

def chat_with_gpt(prompt: str) -> str:
    """
    處理使用者輸入，結合 OpenAI 和 Alpha Vantage API 回應。
    """
    try:
        # 判斷使用者是否輸入股票相關查詢
        if "查詢" in prompt and "股票" in prompt:
            # 從輸入中提取股票代碼
            parts = prompt.split()
            if len(parts) >= 2:
                symbol = parts[1].upper()  # 股票代碼轉為大寫
                interval = "5min"
                outputsize = "compact"
                month = None

                # 處理額外參數（選擇性）
                if "完整" in prompt:
                    outputsize = "full"
                if "月份" in prompt:
                    month = prompt.split("月份")[-1].strip()

                # 查詢股票 API
                stock_response = get_stock_data(symbol, interval, outputsize, month)
                return stock_response
            else:
                return "請提供有效的股票代碼，例如：查詢 TSLA 股票。"

        # 使用 OpenAI 處理一般問題
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個使用繁體中文的聊天機器人。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )

        return response.choices[0].message.content

    except openai.error.OpenAIError as e:
        # 處理 OpenAI API 的特定錯誤
        print(f"GPT API 錯誤: {e}")
        return "抱歉，我無法回應您的問題，請稍後再試。"

    except Exception as e:
        # 處理未知錯誤
        print(f"未知錯誤: {e}")
        return "抱歉，我無法回應您的問題，請稍後再試。"
