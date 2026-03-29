import logging

import requests

logger = logging.getLogger(__name__)


def _deepl_endpoint(api_key: str) -> str:
    """APIキーの末尾が :fx なら Free エンドポイント、それ以外は Pro エンドポイントを返す"""
    if api_key.endswith(":fx"):
        return "https://api-free.deepl.com/v2/translate"
    return "https://api.deepl.com/v2/translate"


def translate_deepl(text: str, api_key: str, max_chars: int = 1500) -> str:
    """DeepL APIで翻訳（文字数制限あり）"""
    if not text or not text.strip():
        return ""
    text = text[:max_chars]
    try:
        resp = requests.post(
            _deepl_endpoint(api_key),
            headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
            json={
                "text": [text],
                "target_lang": "JA",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["translations"][0]["text"]
    except Exception as e:
        logger.warning(f"翻訳失敗: {e}")
        return text  # 失敗時は原文を返す
