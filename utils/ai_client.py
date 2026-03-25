"""
つなぐラボ デモサーバーBot - Gemini API呼び出し
google-genai SDK を使用して自習サポートAI応答を生成する
"""

import json
import logging
import os

from google import genai
from google.genai import types

from config import ENV_GEMINI_API_KEY

logger = logging.getLogger("tsunagu-bot.ai_client")

SYSTEM_PROMPT = """あなたは「つなぐラボ」の自習サポートAIです。
小学生から高校生までの学習をサポートします。

【絶対ルール】
- 答えそのものは絶対に教えない
- 「考え方のヒント」「解き方の手順」を段階的に示す
- 1回の返答は200文字以内に収める
- 敬語は使うが、堅すぎない優しい口調で
- 学習と関係ない質問には「ここは自習の部屋だよ！学習に関係する質問をしてね」と返す
- 危険な内容・個人情報には一切応答しない

【対応教科】
算数/数学、英語、理科、社会、国語（小学校高学年〜高校）

【応答フォーマット】
必ず以下のJSON形式で返してください。他の形式では返さないでください。
{"subject": "教科名（算数/数学/英語/理科/社会/国語/その他）", "response": "ここに応答テキスト"}

【応答テキストの例】
💡 ヒント：
この問題は「〇〇」の考え方を使うよ。
まず△△してみて、そこから□□を考えてみよう！

わからなかったら、もう少し詳しく聞いてね 🙌"""

MODEL_NAME = "gemini-3.1-flash-lite"


def _get_client():
    """Gemini APIクライアントを取得する"""
    api_key = os.environ.get(ENV_GEMINI_API_KEY)
    if not api_key:
        raise RuntimeError(f"{ENV_GEMINI_API_KEY} is not set")
    return genai.Client(api_key=api_key)


async def generate_study_response(question, history=None):
    """
    自習サポートAI応答を生成する。

    Args:
        question: ユーザーの質問文
        history: 直近の会話履歴リスト [{"role": "user"/"model", "text": "..."}]

    Returns:
        dict: {"subject": "教科名", "response": "応答テキスト"}
    """
    client = _get_client()

    # 会話履歴を組み立てる
    contents = []

    if history:
        for entry in history:
            role = entry.get("role", "user")
            text = entry.get("text", "")
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=text)],
                )
            )

    # 今回の質問を追加
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=question)],
        )
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=300,
        temperature=0.7,
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=config,
        )

        raw_text = response.text.strip()
        logger.debug(f"AI raw response: {raw_text}")

        # JSON解析を試みる
        # コードブロックで囲まれている場合を考慮
        json_text = raw_text
        if json_text.startswith("```"):
            lines = json_text.split("\n")
            # 最初と最後の```行を除去
            lines = [l for l in lines if not l.strip().startswith("```")]
            json_text = "\n".join(lines)

        result = json.loads(json_text)
        subject = result.get("subject", "その他")
        response_text = result.get("response", raw_text)

        return {"subject": subject, "response": response_text}

    except json.JSONDecodeError:
        # JSONパースに失敗した場合、テキストをそのまま返す
        logger.warning(f"Failed to parse AI response as JSON: {raw_text}")
        return {"subject": "その他", "response": raw_text}

    except Exception as e:
        logger.error(f"AI API error: {e}", exc_info=True)
        return {
            "subject": "エラー",
            "response": "ごめんね、ちょっと調子が悪いみたい。もう一度試してみてね",
        }
