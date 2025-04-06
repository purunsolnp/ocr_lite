# config.py - 간소화된 설정 관리
import json
import os

# 기본 설정
DEFAULT_SETTINGS = {
    "OCR_REGION": (200, 800, 1700, 1000),
    "OUTPUT_POSITION": [600, 850],
    "HOTKEY": "f8",
    "GLOBAL_HOTKEY": True,
    "ENGINE": "deepl",  # 'deepl' 또는 'libretranslate'
    "USE_GPU": False,
    "OCR_INTERVAL": 1.0,
    "SOURCE_LANG": "en",
    "TARGET_LANG": "ko",
    "AUTO_DETECT_LANG": True
}

# 현재 설정
_settings = DEFAULT_SETTINGS.copy()

def save_settings():
    """설정을 JSON 파일로 저장"""
    try:
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(_settings, f, indent=2, ensure_ascii=False)
        print(f"[✅ 설정 저장 완료]")
        return True
    except Exception as e:
        print(f"[⚠️ 설정 저장 실패]: {e}")
        return False

def load_settings():
    """JSON 파일에서 설정 로드"""
    global _settings
    try:
        if os.path.exists("settings.json"):
            with open("settings.json", "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # 기존 설정에 로드된 설정 병합
                _settings.update(loaded)
            print(f"[✅ 설정 로드 완료]")
    except Exception as e:
        print(f"[⚠️ 설정 로드 실패]: {e}")
    return _settings

def get_setting(key, default=None):
    """설정 값 가져오기"""
    return _settings.get(key, default)

def update_setting(key, value):
    """설정 값 업데이트"""
    if key in _settings or key in DEFAULT_SETTINGS:
        _settings[key] = value
        return True
    return False

def get_dpi_scale():
    """화면 DPI 배율 가져오기"""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        try:
            # Windows 8.1 이상
            user32.SetProcessDPIAware()
        except AttributeError:
            try:
                # Windows 10 이상
                user32.SetProcessDpiAwareness(1)
            except AttributeError:
                pass
        
        # DPI 배율 계산
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            
            # 실제 물리적 화면 해상도 가져오기
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # Windows API로 실제 픽셀 수 가져오기
            try:
                actual_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
                actual_height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
                
                scale_x = actual_width / screen_width
                scale_y = actual_height / screen_height
                
                # 두 값의 평균으로 배율 계산 (대체로 동일함)
                scale = (scale_x + scale_y) / 2
                
                print(f"[🔍 DPI 배율 감지] 배율: {scale:.2f} (화면: {screen_width}x{screen_height}, 실제: {actual_width}x{actual_height})")
                
                root.destroy()
                return scale
            except:
                root.destroy()
                return 1.0
        except:
            return 1.0
    except:
        return 1.0

# 프로그램 시작시 설정 로드
load_settings()
# 설정에 DPI 배율 저장
update_setting("DPI_SCALE", get_dpi_scale())