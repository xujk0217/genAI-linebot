import os
from dotenv import load_dotenv
load_dotenv()
import openai
import twstock
import re


openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_stock_id(user_input: str) -> str:
    """
    從使用者輸入中提取股票代號。
    股票代號應為 4~6 位的數字。
    如果沒有找到，請求 OpenAI API 提取股票代號。
    """
    # 嘗試從使用者輸入中提取股票代號
    match = re.search(r'\b\d{4,6}\b', user_input)
    if match:
        return match.group(0)

    # 如果沒有找到，請求 OpenAI API 協助提取
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # 或其他你設定的模型
            messages=[
                {"role": "system", "content": "你是一個可以提取與辨識公司股票代號的助手。"},
                {"role": "user", "content": f"請從這段文字中提取股票代號或是依據內容提到的公司回答該公司的股票代號：{user_input}，並只回傳股票代碼的數字，如”2330“；如果沒有找到與公司相關的股票資訊的話，不要回傳數字"}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        # 從 API 回應中提取文字
        ai_response = response.choices[0].message.content
        print(f"OpenAI API response: {ai_response}")
        match = re.search(r'\b\d{4,6}\b', ai_response)
        return match.group(0) if match else None
    except Exception as e:
        print(f"Error contacting OpenAI API: {e}")
        return None

def get_stock_info(stock_id: str) -> str:
    """
    查詢股票資訊，返回近五日數據。
    """
    try:
        stock = twstock.Stock(stock_id)
        recent_dates = stock.date[-30:]
        recent_prices = stock.price[-30:]
        recent_highs = stock.high[-30:]

        if None in recent_prices or None in recent_highs:
            return f"抱歉，無法取得 {stock_id} 的完整數據，請稍後再試。"

        result = f"股票代號：{stock_id}\n近五日數據：\n"
        for i in range(len(recent_dates)):
            date_str = recent_dates[i].strftime("%Y-%m-%d")
            result += f"- 日期：{date_str}，收盤價：{recent_prices[i]}，高點：{recent_highs[i]}\n"
        return result
    except Exception as e:
        return f"抱歉，無法取得股票代號 {stock_id} 的資訊。\n錯誤原因：{e}"

def process_user_input(user_input: str) -> str:
    """
    處理使用者輸入，執行股票查詢並交由 GPT 分析。
    """
    # 提取股票代號
    stock_id = extract_stock_id(user_input)
    
    if stock_id:
        # 查詢股票資訊
        stock_info = get_stock_info(stock_id)
        # 傳遞股票資訊給 GPT 分析
        return chat_with_gpt(f"使用者輸入：{user_input}。以下是股票 {stock_id} 的資訊：\n{stock_info}\n。請先按照格式輸出資訊，再提供專業的分析或建議，並回答使用者問題。")
    else:
        # 若未偵測到股票代號，直接詢問 GPT
        return chat_with_gpt(user_input)

def chat_with_gpt(prompt: str) -> str:
    """
    與 GPT 互動，生成回應。
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個使用繁體中文的聊天機器人，會回答股票相關的問題。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        return f"GPT API 錯誤: {e}"
    except Exception as e:
        return f"未知錯誤: {e}"