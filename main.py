import os
import gspread
import google.auth
import requests

def main():
    # 1. 認証 (Workload Identity)
    creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    gc = gspread.authorize(creds)
    sh = gc.open("TikTok動画生成管理シート").sheet1

    # 2. 未処理行の取得
    try:
        cell = sh.find("未処理")
        row_num = cell.row
    except:
        print("未処理なし")
        return

    topic = sh.cell(row_num, 1).value # A列: ネタ
    
    # 3. Geminiへの「プロンプト職人」としての命令
    gemini_key = os.environ.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    
    prompt = f"""
    Topic: {topic}
    Task: Create a 60s Japanese TikTok script AND a detailed English video generation prompt.
    
    The Video Prompt must be for AI Video models (like Kling/Luma).
    Include: 
    - Subject (e.g., A fluffy cat wearing a kimono)
    - Action (e.g., dancing gracefully in a shower of cherry blossoms)
    - Style (e.g., Photorealistic, 8k, Unreal Engine 5 render, cinematic lighting)
    - Camera (e.g., Slow motion, orbital shot)
    
    Format: [Script] ### [Video Prompt]
    """

    res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    
    if res.status_code == 200:
        full_text = res.json()['candidates'][0]['content']['parts'][0]['text']
        script, video_prompt = full_text.split("###") if "###" in full_text else (full_text, "")
        
        # 4. シートの更新
        sh.update_cell(row_num, 3, script.strip())       # C列: 台本
        sh.update_cell(row_num, 4, video_prompt.strip()) # D列: 生成用英語プロンプト
        sh.update_cell(row_num, 2, "プロンプト完了")
        print(f"✅ 行 {row_num} のプロンプトを生成しました。")

if __name__ == "__main__":
    main()
