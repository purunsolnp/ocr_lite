# ocr.py - OCR 기능 (OBS 제외)
import time
import pyautogui
import numpy as np
import threading
import traceback
from config import get_setting
from translator import translate_text

# 전역 변수
ocr_thread = None
ocr_running = False
ocr_reader = None
last_text = ""
last_translated = ""
repeat_count = 0
MAX_REPEAT = 3

def get_lang(lang_code):
    """언어 코드에 따른 OCR 언어 목록 반환"""
    if lang_code.startswith("ja"):
        return ["ja", "en"]
    elif lang_code.startswith("zh"):
        return ["ch_sim", "en"]
    elif lang_code.startswith("ko"):
        return ["ko", "en"]
    else:
        return ["en"]

def init_ocr_reader():
    """OCR 리더 초기화"""
    try:
        import easyocr
        lang_list = get_lang(get_setting("SOURCE_LANG"))
        use_gpu = get_setting("USE_GPU")
        print(f"[🔍 OCR 리더 초기화] 언어: {lang_list}, GPU: {use_gpu}")
        return easyocr.Reader(lang_list, gpu=use_gpu)
    except Exception as e:
        print(f"[⚠️ OCR 리더 초기화 오류]: {str(e)}")
        print(traceback.format_exc())
        return None

def reinit_ocr_reader():
    """OCR 리더 재초기화"""
    global ocr_reader
    ocr_reader = init_ocr_reader()

def ocr_loop(overlay_label):
    """OCR 및 번역 메인 루프"""
    global ocr_running, last_text, last_translated, repeat_count, ocr_reader
    
    # OCR 리더가 없으면 초기화
    if ocr_reader is None:
        ocr_reader = init_ocr_reader()
        if ocr_reader is None:
            print("[⚠️ OCR 리더 초기화 실패로 OCR 루프 종료]")
            ocr_running = False
            return
    
    print("[✅ OCR 루프 시작]")
    
    while ocr_running:
        try:
            # OCR 영역 가져오기
            region = get_setting("OCR_REGION")
            if not region:
                print("[⚠️ OCR 영역이 설정되지 않음]")
                time.sleep(1)
                continue
            
            # 스크린샷 촬영
            x1, y1, x2, y2 = region
            try:
                img = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
                print(f"[📸 스크린샷 촬영 성공] 영역: {region}")
            except Exception as e:
                print(f"[⚠️ 스크린샷 실패] {str(e)}")
                time.sleep(1)
                continue
            
            # OCR 텍스트 인식
            try:
                result = ocr_reader.readtext(np.array(img), detail=0)
                text = "\n".join(result).strip()
                print(f"[🧾 OCR 텍스트 인식 완료] 길이: {len(text)}")
            except Exception as e:
                print(f"[⚠️ OCR 텍스트 인식 실패] {str(e)}")
                time.sleep(1)
                continue
            
            # 텍스트가 없으면 건너뜀
            if not text:
                print("[⚠️ 인식된 텍스트 없음, 건너뜀]")
                time.sleep(get_setting("OCR_INTERVAL"))
                continue
            
            print(f"[🧾 OCR 원본 텍스트]: {text}")
            
            # 이전 텍스트와 동일한지 확인
            if text == last_text:
                repeat_count += 1
                print(f"[🔄 동일 텍스트 감지] 반복 횟수: {repeat_count}/{MAX_REPEAT}")
                
                # 최대 반복 횟수 이상이면 이전 번역 결과 재사용
                if repeat_count >= MAX_REPEAT:
                    print(f"[⏩ 번역 스킵] 이전 번역 결과 재사용")
                    translated = last_translated
                else:
                    # 최대 반복 횟수 미만이면 새로 번역
                    translated = translate_text(text)
                    last_translated = translated
            else:
                # 새로운 텍스트면 초기화 후 번역
                last_text = text
                repeat_count = 0
                try:
                    translated = translate_text(text)
                    last_translated = translated
                    print(f"[🌐 번역 성공]")
                except Exception as e:
                    print(f"[⚠️ 번역 실패] {str(e)}")
                    time.sleep(1)
                    continue
            
            print(f"[🌐 번역 결과]: {translated[:50]}..." if len(translated) > 50 else f"[🌐 번역 결과]: {translated}")
            
            # 오버레이 업데이트
            try:
                overlay_label.config(text=translated)
                print("[✅ 오버레이 텍스트 업데이트 완료]")
            except Exception as e:
                print(f"[⚠️ 오버레이 업데이트 실패] {str(e)}")
            
        except Exception as e:
            print(f"[⚠️ OCR 루프 오류] {str(e)}")
            print(traceback.format_exc())
        
        time.sleep(get_setting("OCR_INTERVAL"))
    
    print("[🛑 OCR 루프 종료됨]")

def start_ocr_thread(overlay_label):
    """OCR 스레드 시작"""
    global ocr_thread, ocr_running, last_text, last_translated, repeat_count
    
    if ocr_thread and ocr_thread.is_alive():
        print("[⚠️ OCR 스레드 이미 실행 중]")
        return
    
    # 중복 감지 변수 초기화
    last_text = ""
    last_translated = ""
    repeat_count = 0
    
    ocr_running = True
    print("[OCR 스레드 시작]")
    ocr_thread = threading.Thread(target=ocr_loop, args=(overlay_label,), daemon=True)
    ocr_thread.start()
    print("[✅ OCR 스레드 시작됨]")

def stop_ocr():
    """OCR 스레드 중지"""
    global ocr_running
    print("[🛑 OCR 중지 요청됨]")
    ocr_running = False