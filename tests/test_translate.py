import pytest

from news_feeder.translate import translate_deepl


def test_translate_empty_string():
    assert translate_deepl("", api_key="dummy") == ""


def test_translate_whitespace_only():
    assert translate_deepl("   ", api_key="dummy") == ""


def test_translate_truncates_to_max_chars(mocker):
    mock_post = mocker.patch("news_feeder.translate.requests.post")
    mock_post.return_value.json.return_value = {"translations": [{"text": "翻訳結果"}]}
    mock_post.return_value.raise_for_status = lambda: None

    long_text = "a" * 2000
    translate_deepl(long_text, api_key="dummy", max_chars=100)

    sent_text = mock_post.call_args[1]["data"]["text"]
    assert len(sent_text) == 100


def test_translate_returns_original_on_api_error(mocker):
    mocker.patch("news_feeder.translate.requests.post", side_effect=Exception("network error"))
    result = translate_deepl("Hello", api_key="dummy")
    assert result == "Hello"


def test_translate_success(mocker):
    mock_post = mocker.patch("news_feeder.translate.requests.post")
    mock_post.return_value.json.return_value = {"translations": [{"text": "こんにちは"}]}
    mock_post.return_value.raise_for_status = lambda: None

    result = translate_deepl("Hello", api_key="test_key")
    assert result == "こんにちは"
    mock_post.assert_called_once()
