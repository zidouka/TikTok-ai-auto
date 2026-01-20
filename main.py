import os
import gspread
import google.auth
import requests
import time

def main():
    print("--- 🚀 プログラム実行開始 (2026 最終修正版) ---")
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ エラー: GEMINI_API_KEY が設定されていません。")
        return

    # 1. Google Cloud 認証
    print("🔐 Google Cloud 認証を試行中...")
    try:
        creds, _ = google.auth.default(
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        gc = gspread.authorize(creds)
        print("✅ 認証成功")
    except Exception as e:
        print(f"❌ 認証失敗: {e}")
        return

    # 2. スプレッドシートを開く
    print("📅 スプレッドシート『TikTok管理シートAI』を開いています...")
    try:
        sh = gc.open("TikTok管理シートAI").sheet1
        print("✅ シート接続成功")
    except Exception as e:
        print(f"❌ シートが見つかりません: {e}")
        return

    # 3. 未処理行の探索
    print("🔍 『未処理』と書かれた行を探しています...")
    try:
        cell = sh.find("未処理")
        row_num = cell.row
        print(f"📌 行番号 {row_num} に未処理データを発見しました。")
    except:
        print("✅ 処理待ちの行（『未処理』）は見つかりませんでした。")
        return

    topic = sh.cell(row_num, 1).value 
    print(f"📝 テーマ: {topic}")

    # 4. Gemini API 実行
    print("🧠 Gemini 1.5 Flash に依頼中...")
    
    # 【最重要修正】URLの models/ 部分を確実に正しく連結します
    base_url = "https://generativelanguage.googleapis.com/v1"
    model_path = "models/gemini-1.5-flash"
    gen_url = f"{base_url}/{model_path}:generateContent?key={gemini_key}"
    
    prompt = (
        f"テーマ「{topic}」について、TikTok用の30秒程度の面白い台本を作成してください。"
        f"また、その内容に最適な動画を生成するための詳細な英語プロンプトも作成してください。"
        f"出力形式は必ず『台本 ### 英語プロンプト』としてください。"
    )
    
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(gen_url, json=payload)
        
        # エラー時のログ出力を強化
        if res.status_code != 200:
            print(f"❌ APIエラー詳細 (Status: {res.status_code}): {res.text}")
            # もし404が出るならURLを微調整してリトライ
            if res.status_code == 404:
                print("🔄 URL形式を変更してリトライします...")
                gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={gemini_key}"
                res = requests.post(gen_url, json=payload)

        res.raise_for_status()
        data = res.json()
        full_text = data['candidates'][0]['content']['parts'][0]['text']
        
        if "###" in full_text:
            script, video_prompt = full_text.split("###")
        else:
            script, video_prompt = full_text, "A high quality cinematic video of " + topic
            
        script = script.strip()
        video_prompt = video_prompt.strip()

        # 5. スプレッドシートへ書き込み
        print("💾 スプレッドシートに結果を書き込み中...")
        sh.update_cell(row_num, 2, "プロンプト完了")
        sh.update_cell(row_num, 3, script)
        sh.update_cell(row_num, 4, video_prompt)
        
        print(f"✨ 全ての処理が正常に完了しました！ (行: {row_num})")

    except Exception as e:
        print(f"❌ 処理エラー: {e}")
        sh.update_cell(row_num, 2, "APIエラー")

if __name__ == "__main__":
    main()
