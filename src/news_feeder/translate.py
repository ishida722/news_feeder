import logging

import requests

logger = logging.getLogger(__name__)


def translate_deepl(text: str, api_key: str, max_chars: int = 1500) -> str:
    """DeepL Free APIで翻訳（文字数制限あり）"""
    if not text or not text.strip():
        return ""
    text = text[:max_chars]
    try:
        resp = requests.post(
            "https://api-free.deepl.com/v2/translate",
            data={
                "auth_key": api_key,
                "text": text,
                "target_lang": "JA",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["translations"][0]["text"]
    except Exception as e:
        logger.warning(f"翻訳失敗: {e}")
        return text  # 失敗時は原文を返す
