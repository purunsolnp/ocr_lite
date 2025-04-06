# main.py - 프로그램 시작점 (아이콘 제거, 블로그 자동 열기 추가)
import tkinter as tk
import traceback
import time
import os
import sys
import webbrowser

# 로그 기록 함수 정의
def write_log(message):
    try:
        with open("debug_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"{message}\n")
        print(message)  # 콘솔에도 출력
    except Exception as e:
        print(f"로그 기록 실패: {e}")

# 초기 로그 파일 생성
try:
    with open("debug_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"프로그램 시작: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    write_log("로그 파일 생성 완료")
except Exception as e:
    print(f"로그 파일 생성 실패: {e}")

# 전역 변수
root = None
main_window = None
overlay = None
overlay_label = None
toggle_button = None
register_hotkey_func = None

def main():
    global root, main_window, overlay, overlay_label, toggle_button, register_hotkey_func
    
    try:
        write_log("[main 함수 시작]")
        
        # 블로그 자동 열기
        try:
            webbrowser.open("https://sonagi-psy.tistory.com/15")
            write_log("[🔗 광고 후원 블로그 자동 오픈됨]")
        except Exception as e:
            write_log(f"[⚠️ 블로그 열기 실패]: {e}")
        
        # 기본 모듈 임포트
        try:
            from config import load_settings
            from gui import create_main_window
            
            write_log("[✅ 기본 모듈 임포트 완료]")
        except Exception as e:
            write_log(f"[⚠️ 모듈 임포트 오류]: {e}")
            write_log(traceback.format_exc())
            raise
        
        # GUI 메인 루트 생성
        root = tk.Tk()
        root.withdraw()  # 메인 루트 숨기기
        write_log("[✅ Tkinter 루트 초기화 완료]")
        
        # 설정 로드
        load_settings()
        write_log("[✅ 설정 로드 완료]")
        
        # 메인 창 생성
        main_window, overlay, overlay_label, toggle_button, register_hotkey_func = create_main_window()
        write_log("[✅ 메인 창 생성 완료]")
        
        # GUI 루프 실행
        write_log("[✅ GUI 메인 루프 시작]")
        root.mainloop()
        
    except Exception as e:
        write_log(f"[⚠️ main 함수 실행 중 오류 발생]: {e}")
        write_log(traceback.format_exc())
        
        try:
            from tkinter import messagebox
            if root is None:
                root = tk.Tk()
                root.withdraw()
            messagebox.showerror("프로그램 오류", f"프로그램에 오류가 발생했습니다:\n{e}\n\n자세한 내용은 debug_log.txt 파일을 확인하세요.")
        except:
            pass
    finally:
        write_log("[종료됨]")
        write_log(f"[로그 종료] {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        write_log("[프로그램 진입점 실행]")
        main()
    except Exception as e:
        write_log(f"[⚠️ 예상치 못한 오류 발생]: {e}")
        write_log(traceback.format_exc())
        
        try:
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("프로그램 오류", f"프로그램에 오류가 발생했습니다:\n{e}\n\n자세한 내용은 debug_log.txt 파일을 확인하세요.")
        except:
            pass