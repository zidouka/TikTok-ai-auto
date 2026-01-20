import os
import gspread
import google.auth
import requests
import time

def main():
    print("--- 🚀 プログラム実行開始 (2026 最終解決版) ---")
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ エラー: GEMINI_API_KEY が設定されていません。")
        return

    # 1. Google Cloud 認証
    try:
        creds, _ = google.auth.default(
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        gc = gspread.authorize(creds)
        print("✅ Google Cloud 認証成功")
    except Exception as e:
        print(f"❌ 認証失敗: {e}")
        return

    # 2. スプレッドシートを開く
    try:
        sh = gc.open("TikTok管理シートAI").sheet1
        print("✅ シート接続成功")
    except Exception as e:
        print(f"❌ シート接続失敗: {e}")
        return

    # 3. 未処理行の探索
    try:
        cell = sh.find("未処理")
        row_num = cell.row
        topic = sh.cell(row_num, 1).value 
        print(f"📌 行番号 {row_num} を処理します。テーマ: {topic}")
    except:
        print("✅ 処理待ちの『未処理』行はありません。")
        return

    # 4. Gemini API 実行
    print("🧠 Gemini 1.5 Flash (latest) に依頼中...")
    
    # 【ここを2026年最新仕様に修正】
    # モデル名に -latest を付与し、APIバージョンは現在の主流である v1beta を使用します
    model_name = "gemini-1.5-flash-latest"
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
    
    prompt = (
        f"テーマ「{topic}」について、TikTok用の30秒程度の面白い台本を作成してください。"
        f"また、その内容に最適な動画を生成するための詳細な英語プロンプトも作成してください。"
        f"出力形式は必ず『台本 ### 英語プロンプト』としてください。"
    )
    
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(gen_url, json=payload)
        
        if res.status_code != 200:
            print(f"❌ APIエラー詳細: {res.text}")
            # もし -latest でもダメな場合の予備策
            if "not found" in res.text.lower():
                print("🔄 モデル名を変更して再試行...")
                gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                res = requests.post(gen_url, json=payload)

        res.raise_for_status()
        data = res.json()
        full_text = data['candidates'][0]['content']['parts'][0]['text']
        
        if "###" in full_text:
            script, video_prompt = full_text.split("###")
        else:
            script, video_prompt = full_text, "High quality cinematic video of " + topic
            
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
