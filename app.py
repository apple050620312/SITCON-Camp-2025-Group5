# app.py
import os
import pprint
import requests
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
        data = request.json
        user_prompt = data.get('prompt', '').strip()
        if not user_prompt:
            return jsonify({"error": "請提供 prompt", "images": [], "item_name": ""}), 400

        ai_prompt = (
            f"根據使用者需求從卡通「哆拉A夢」中找出符合條件的一個道具名稱，\n"
            f"使用繁體中文進行回應，開頭統一格式：「道具名稱：<道具名稱>」，換行兩行之後下面使用 100 字描述道具的特性和用途，必須確保道具的真實性，要有相關的考據來源但不用輸出，禁止憑空生成不存在的道具，\n\n"
            f"以下是使用者需求：{user_prompt}"
        )
        response = model.generate_content(ai_prompt)
        ai_text = response.text.strip()
        item_name = ai_text.split('道具名稱：')[-1].split('\n')[0].strip()
        print("AI 原始回覆：", ai_text)
        print("解析出道具名稱：", repr(item_name))

        # 圖片搜尋
        params = {
            'q': item_name,
            'searchType': 'image',
            'num': 5,
            'imgSize': 'medium',
            'key': CSE_API_KEY,
            'cx': CSE_ID
        }
        img_resp = requests.get(SEARCH_URL, params=params)
        print("圖片搜尋請求網址：", img_resp.url)

        img_resp.raise_for_status()
        result_json = img_resp.json()
        pprint.pprint(result_json)

        image_urls = [item['link'] for item in result_json.get('items', [])]
        print("找到的圖片連結：", image_urls)

        return jsonify({
            "item_name": item_name,
            "full_response": ai_text,
            "images": image_urls
        })

    except requests.exceptions.HTTPError as e:
        print("HTTP 錯誤：", str(e), img_resp.text)
        return jsonify({"error": "圖片 API 回傳錯誤", "images": [], "item_name": item_name}), 500
    except Exception as e:
        print("其他錯誤：", str(e))
        return jsonify({"error": "後端錯誤：" + str(e), "images": [], "item_name": item_name}), 500

if __name__ == "__main__":
    app.run(debug=True)
