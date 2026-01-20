import os
import gspread
import google.auth
import requests

def get_best_model(api_key):
    """利用可能な最新のGeminiモデルを取得する"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        res = requests.get(url).json()
        models = [m['name'] for m in res.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        return next((m for m in models if '1.5-flash' in m), "models/gemini-1.5-flash")
    except:
        return "models/gemini-1.5-flash"

def main():
    print("--- 🚀 プログラム実行開始 ---")
    
    # 1. 環境変数の確認
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ エラー: GEMINI_API_KEY が設定されていません。")
        return

    # 2. Google Cloud 認証 (Workload Identity 連携)
    print("🔐 Google Cloud 認証を試行中...")
    try:
        creds, _ = google.auth.default(
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        gc = gspread.authorize(creds)
        print("✅ 認証成功")
    except Exception as e:
        print(f"❌ 認証失敗: {e}")
        return

    # 3. スプレッドシートを開く
    print("📅 スプレッドシート『TikTok管理シートAI』を開いています...")
    try:
        sh = gc.open("TikTok管理シートAI").sheet1
        print("✅ シート接続成功")
    except Exception as e:
        print(f"❌ シートが見つかりません。共有設定や名前を確認してください: {e}")
        return

    # 4. 未処理行の探索 (B列の「未処理」を検索)
    print("🔍 『未処理』と書かれた行を探しています...")
    try:
        # シート全体から「未処理」という文字列を検索
        cell = sh.find("未処理")
        row_num = cell.row
        print(f"📌 行番号 {row_num} に未処理データを発見しました。")
    except Exception as e:
        print("✅ 処理待ちの行（『未処理』セル）が見つかりませんでした。")
        return

    # A列からネタを取得
    topic = sh.cell(row_num, 1).value 
    if not topic:
        print(f"⚠️ 行 {row_num} のA列（ネタ）が空っぽです。")
        sh.update_cell(row_num, 2, "エラー: ネタなし")
        return

    print(f"📝 テーマ: {topic}")

    # 5. Gemini API で台本と動画プロンプトを生成
    print("🧠 Gemini に台本とプロンプトを依頼中...")
    model_name = get_best_model(gemini_key)
    gen_url = f"https://generativelanguage.googleapis.com/v1/{model_name}:generateContent?key={gemini_key}"
    
    prompt = (
        f"テーマ「{topic}」について、TikTok用の30秒程度の面白い台本を作成してください。"
        f"また、その内容に最適な動画を生成するための詳細な英語プロンプトも作成してください。"
        f"出力形式は必ず『台本 ### 英語プロンプト』としてください。"
    )
    
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(gen_url, json=payload)
        res.raise_for_status()
