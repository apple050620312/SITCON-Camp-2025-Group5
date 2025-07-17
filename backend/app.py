# app.py
import os
import pprint
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# 設定 Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')

# Google Custom Search 設定
CSE_API_KEY = os.getenv("CSE_API_KEY")
CSE_ID = os.getenv("CSE_ID")
SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

@app.route('/get_item', methods=['POST'])
def get_item():
    try:
        # 載入 tool.json
        with open('tool.json', 'r', encoding='utf-8') as f:
            tool_data = json.load(f)
        tool_names = list(tool_data.keys())
        tool_names_str = '、'.join(tool_names)

        data = request.json
        user_prompt = data.get('prompt', '').strip()
        if not user_prompt:
            return jsonify({"error": "請提供 prompt", "images": [], "item_name": "", "image_url": ""}), 400

        ai_prompt = (
            f"根據使用者需求，僅能從以下道具中選擇一個最符合條件的道具名稱：{tool_names_str}。使用繁體中文回應，開頭統一格式：「道具名稱：<道具名稱>」。之後下面使用 100 字描述道具的特性和用途。必須確保道具的真實性，禁止憑空生成不存在及資料庫不存在的道具。模仿「哆拉A夢」這個角色的語氣及口頭禪回應使用者，例如「真拿你沒辦法！」或「誰說我沒有的！」等。以下是使用者的需求：{user_prompt}，請開始回覆。"
        )
        response = model.generate_content(ai_prompt)
        ai_text = response.text.strip()
        item_name = ai_text.split('道具名稱：')[-1].split('\n')[0].strip()
        print("使用者要求：", user_prompt)
        print("AI 原始回覆：", ai_text)
        # print("解析出道具名稱：", repr(item_name))

        # 取得圖片連結
        image_url = tool_data.get(item_name, {}).get('圖片連結', '')

        return jsonify({
            "item_name": item_name,
            "full_response": ai_text,
            "images": [],
            "image_url": image_url
        })

    except requests.exceptions.HTTPError as e:
        # print("HTTP 錯誤：", str(e), img_resp.text)  # 已無 img_resp，註解避免錯誤
        print("HTTP 錯誤：", str(e))
        return jsonify({"error": "圖片 API 回傳錯誤", "images": [], "item_name": item_name}), 500
    except Exception as e:
        print("其他錯誤：", str(e))
        return jsonify({"error": "後端錯誤：" + str(e), "images": [], "item_name": item_name}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=50618)
