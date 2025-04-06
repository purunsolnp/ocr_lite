# translator.py - 번역 기능 (DeepL, LibreTranslate만 지원)
import requests
from config import get_setting, update_setting

# DeepL 번역 함수
def deepl_translate(text):
    """DeepL API를 사용하여 텍스트 번역"""
    if not text:
        return ""
    
    # API 키 로드
    try:
        with open("deepl.txt", "r", encoding="utf-8") as f:
            api_key = f.read().strip()
    except Exception as e:
        print(f"[⚠️ DeepL API 키 로드 실패]: {e}")
        return "(DeepL API 키가 설정되지 않았습니다)"
    
    # 언어 설정
    auto_detect = get_setting("AUTO_DETECT_LANG", True)
    source_lang = None if auto_detect else get_setting("SOURCE_LANG", "en")
    target_lang = get_setting("TARGET_LANG", "ko")
    
    # DeepL API 언어 코드 매핑
    DEEPL_LANGS = {
        "ko": "KO", "en": "EN", "ja": "JA", "zh-CN": "ZH", "zh": "ZH",
        "ru": "RU", "fr": "FR", "es": "ES", "de": "DE", "pt": "PT",
        "it": "IT", "nl": "NL", "pl": "PL"
    }
    
    # 언어 코드 변환
    deepl_target = DEEPL_LANGS.get(target_lang, "EN")
    deepl_source = None if source_lang is None else DEEPL_LANGS.get(source_lang, "EN")
    
    # 같은 언어면 번역 스킵
    if deepl_source and deepl_source == deepl_target:
        return text
    
    # API 요청
    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "text": [text],
        "target_lang": deepl_target
    }
    
    if deepl_source:
        data["source_lang"] = deepl_source
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            return f"(DeepL 번역 실패: HTTP {response.status_code})"
        
        result = response.json()
        translations = result.get("translations", [])
        
        if translations:
            return translations[0].get("text", "")
        else:
            return "(DeepL 번역 결과 없음)"
    except Exception as e:
        return f"(DeepL 번역 실패: {str(e)})"

# LibreTranslate 번역 함수
def libre_translate(text):
    """LibreTranslate API를 사용하여 텍스트 번역"""
    if not text:
        return ""
    
    # 설정 로드
    try:
        with open("libretranslate.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
            parts = content.split("|")
            api_url = parts[0]
            api_key = parts[1] if len(parts) > 1 else ""
    except:
        api_url = get_setting("LIBRE_API_URL", "http://localhost:5001/translate")
        api_key = get_setting("LIBRE_API_KEY", "")
    
    # 언어 설정
    auto_detect = get_setting("AUTO_DETECT_LANG", True)
    source_lang = "auto" if auto_detect else get_setting("SOURCE_LANG", "en")
    target_lang = get_setting("TARGET_LANG", "ko")
    
    # 언어 코드 매핑
    LANG_MAP = {
        "en": "en", "ko": "ko", "ja": "ja", "zh": "zh", "zh-CN": "zh",
        "es": "es", "de": "de", "ru": "ru", "fr": "fr", "it": "it",
        "pt": "pt", "auto": "auto"
    }
    
    source = LANG_MAP.get(source_lang, "en")
    target = LANG_MAP.get(target_lang, "ko")
    
    # 소스와 타겟 언어가 같으면 번역 필요 없음
    if source != "auto" and source == target:
        return text
    
    # API 요청 데이터
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }
    
    if api_key:
        payload["api_key"] = api_key
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("translatedText", "")
    except requests.exceptions.HTTPError as e:
        return f"(LibreTranslate 번역 실패: HTTP {e.response.status_code})"
    except requests.exceptions.ConnectionError:
        return "(LibreTranslate 연결 실패 - 서버에 접속할 수 없습니다)"
    except Exception as e:
        return f"(LibreTranslate 번역 실패: {str(e)})"

# 번역 디스패치 함수
def translate_text(text):
    """선택된 번역 엔진으로 텍스트 번역"""
    if not text:
        return ""
    
    engine = get_setting("ENGINE", "deepl")
    
    if engine == "deepl":
        return deepl_translate(text)
    elif engine == "libretranslate":
        return libre_translate(text)
    else:
        return f"(지원되지 않는 번역 엔진: {engine})"