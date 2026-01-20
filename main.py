import os
import gspread
import google.auth
import requests
import time

def get_best_model(api_key):
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        res = requests.get(url).json()
        models = [m['name'] for m in res.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        # あなたの希望通り、性能の高い順（2.5 -> 2.0 -> 1.5）で検索します
        for version in ['2.5-flash', '2.0-flash', '1.5-flash']:
            found = next((m for m in models if version in m), None)
            if found: return found
        return models[0] if models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-2.5-flash"

def main():
    print("--- 🚀 プログラム実行開始 (最新モデル・リトライ機能付き) ---")
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

    # 4. Gemini API 実行 (リトライロジック)
    gen_url = f"https://generativelanguage.googleapis.com/v1/{full_model_name}:generateContent?key={gemini_key}"
    prompt = (
        f"テーマ「{topic}」について、TikTok用の30秒程度の面白い台本を作成してください。"
        f"また、その動画を生成するための英語プロンプトも作成してください。"
        f"\n\n出力は必ず以下の形式を守ってください：\n台本の内容\n###\n英語プロンプト"
    )

    max_retries = 3
    retry_delay = 15 # 15秒待機

    for i in range(max_retries):
        try:
            print(f"🧠 AIに依頼中... (試行 {i+1}/{max_retries})")
            res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]})
            
            # 503 (混雑) または 429 (制限) の場合
            if res.status_code in [503, 429]:
                print(f"⚠️ サーバー混雑中 (Error {res.status_code})。{retry_delay}秒待機します...")
                time.sleep(retry_delay)
                continue
            
            res.raise_for_status()
            full_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            
            # 5. 分割と書き込み
            if "###" in full_text:
                parts = full_text.split("###")
                script = parts[0].strip()
                video_prompt = parts[1].strip()
            else:
                script = full_text.strip()
                video_prompt = f"A cinematic video about {topic}"
            
            print("💾 スプレッドシートに書き込み中...")
            sh.update_cell(row_num, 2, "完了")
            sh.update_cell(row_num, 3, script)
            sh.update_cell(row_num, 4, video_prompt)
            print("✨ 処理が正常に完了しました！")
            return # 成功したのでループを抜ける

        except Exception as e:
            print(f"❌ 試行 {i+1} でエラーが発生しました: {e}")
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                sh.update_cell(row_num, 2, "エラー停止")

if __name__ == "__main__":
    main()
