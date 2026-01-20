import os
import gspread
import google.auth
import requests

def get_best_model(api_key):
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        res = requests.get(url).json()
        models = [m['name'] for m in res.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        # 2.5, 2.0, 1.5 の順で優先的に検索
        for version in ['2.5-flash', '2.0-flash', '1.5-flash']:
            found = next((m for m in models if version in m), None)
            if found: return found
        return models[0] if models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

def main():
    print("--- 🚀 プログラム実行開始 (エラー耐性強化版) ---")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    # 1. Google Cloud 認証
    creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    gc = gspread.authorize(creds)

    # 2. スプレッドシート操作
    try:
        sh = gc.open("TikTok管理シートAI").sheet1
        cell = sh.find("未処理")
        row_num = cell.row
        topic = sh.cell(row_num, 1).value
        print(f"📌 行番号 {row_num} 処理開始: {topic}")
    except:
        print("✅ 未処理の行がありません。")
        return

    # 3. モデル名の取得
    full_model_name = get_best_model(gemini_key)
    print(f"🤖 使用モデル: {full_model_name}")

    # 4. Gemini API 実行
    gen_url = f"https://generativelanguage.googleapis.com/v1/{full_model_name}:generateContent?key={gemini_key}"
    
    # AIに出力を厳格に守らせるためのプロンプト
    prompt = (
        f"テーマ「{topic}」について、TikTok用の30秒程度の面白い台本を作成してください。"
        f"また、その動画を生成するための英語プロンプトも作成してください。"
        f"\n\n出力は必ず以下の形式を守ってください：\n台本の内容\n###\n英語プロンプト"
    )

    try:
        res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]})
        if res.status_code == 200:
            full_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            
            # 安全な分割処理
            if "###" in full_text:
                parts = full_text.split("###")
                script = parts[0].strip()
                video_prompt = parts[1].strip()
            else:
                # 分割できない場合は全体を台本にし、プロンプトはテーマから生成
                script = full_text.strip()
                video_prompt = f"A cinematic video about {topic}"
            
            # 5. 書き込み
            sh.update_cell(row_num, 2, "完了")
            sh.update_cell(row_num, 3, script)
            sh.update_cell(row_num, 4, video_prompt)
            print("✨ スプレッドシートを更新しました！")
        else:
            print(f"❌ APIエラー: {res.status_code}\n{res.text}")
            sh.update_cell(row_num, 2, "APIエラー")
            
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        sh.update_cell(row_num, 2, f"エラー: {str(e)[:20]}")

if __name__ == "__main__":
    main()
