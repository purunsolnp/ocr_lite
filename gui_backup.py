# gui.py - 간소화된 GUI
import tkinter as tk
import os
import webbrowser
import keyboard
import threading
import time
import traceback
from tkinter import simpledialog, messagebox, StringVar, BooleanVar
from config import get_setting, update_setting, save_settings
from ocr import start_ocr_thread, stop_ocr, reinit_ocr_reader

def create_overlay_window():
    """오버레이 윈도우 생성 (크기 조절 가능)"""
    overlay = tk.Toplevel()
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)
    overlay.attributes("-alpha", 0.8)
    
    x, y = get_setting("OUTPUT_POSITION", (600, 850))
    width = get_setting("OVERLAY_WIDTH", 800)
    height = get_setting("OVERLAY_HEIGHT", 120)
    overlay.geometry(f"{width}x{height}+{x}+{y}")
    
    # 창 테두리 프레임 (크기 조절 시각화)
    border_frame = tk.Frame(overlay, bg="gray")
    border_frame.pack(fill="both", expand=True, padx=1, pady=1)
    
    # 내부 컨텐츠 프레임
    content_frame = tk.Frame(border_frame, bg="black")
    content_frame.pack(fill="both", expand=True)
    
    # 텍스트 레이블
    label = tk.Label(
        content_frame,
        text="",
        font=("Malgun Gothic", 16),
        fg="white",
        bg="black",
        justify="left",
        wraplength=width-20,
        anchor="nw",
        padx=5,
        pady=5
    )
    label.pack(fill="both", expand=True)
    
    # 드래그 이벤트 처리 (창 이동)
    def start_move(event):
        overlay.x = event.x
        overlay.y = event.y

    def on_move(event):
        deltax = event.x - overlay.x
        deltay = event.y - overlay.y
        x = overlay.winfo_x() + deltax
        y = overlay.winfo_y() + deltay
        overlay.geometry(f"+{x}+{y}")
        
        # 위치 설정 업데이트
        update_setting("OUTPUT_POSITION", (x, y))
    
    # 상단 드래그 바
    drag_bar = tk.Frame(overlay, height=8, bg="gray", cursor="fleur")
    drag_bar.place(relx=0, rely=0, relwidth=1, height=8)
    drag_bar.bind("<Button-1>", start_move)
    drag_bar.bind("<B1-Motion>", on_move)
    
    # 크기 조절 핸들 생성 함수
    def create_resize_handle():
        # 우측 하단 크기 조절 핸들
        handle_size = 16
        resize_handle = tk.Frame(overlay, width=handle_size, height=handle_size, bg="gray", cursor="sizing")
        resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        
        def start_resize(event):
            overlay.start_x = overlay.winfo_pointerx()
            overlay.start_y = overlay.winfo_pointery()
            overlay.start_width = overlay.winfo_width()
            overlay.start_height = overlay.winfo_height()
        
        def on_resize(event):
            # 현재 마우스 위치
            current_x = overlay.winfo_pointerx()
            current_y = overlay.winfo_pointery()
            
            # 마우스 이동 거리 계산
            delta_x = current_x - overlay.start_x
            delta_y = current_y - overlay.start_y
            
            # 새 크기 계산 (최소 크기 제한)
            new_width = max(300, overlay.start_width + delta_x)
            new_height = max(100, overlay.start_height + delta_y)
            
            # 창 크기 변경
            overlay.geometry(f"{new_width}x{new_height}")
            
            # wraplength 업데이트
            label.config(wraplength=new_width-20)
            
            # 설정 저장
            update_setting("OVERLAY_WIDTH", new_width)
            update_setting("OVERLAY_HEIGHT", new_height)
        
        # 이벤트 바인딩
        resize_handle.bind("<Button-1>", start_resize)
        resize_handle.bind("<B1-Motion>", on_resize)
        
        return resize_handle
    
    # 크기 조절 핸들 생성
    resize_handle = create_resize_handle()
    
    # 오버레이 설정 업데이트 함수
    def update_overlay_position():
        x, y = get_setting("OUTPUT_POSITION", (600, 850))
        width = get_setting("OVERLAY_WIDTH", 800)
        height = get_setting("OVERLAY_HEIGHT", 120)
        overlay.geometry(f"{width}x{height}+{x}+{y}")
        label.config(wraplength=width-20)
    
    # 오버레이 객체에 업데이트 함수 추가
    overlay.update_position = update_overlay_position
    
    return overlay, label

def select_area(callback):
    """마우스로 드래그해서 영역 선택 (다중 모니터 지원)"""
    import tkinter as tk
    
    # 전체 가상 화면 크기 가져오기
    try:
        root = tk.Tk()
        root.withdraw()
        
        # 모든 모니터를 포함하는 가상 화면 크기 계산
        virtual_width = root.winfo_screenwidth()
        virtual_height = root.winfo_screenheight()
        
        # 다중 모니터 지원을 위한 추가 계산
        try:
            # Windows에서 다중 모니터 정보 가져오기
            import ctypes
            user32 = ctypes.windll.user32
            monitors = []
            
            def callback_enum_monitor(monitor, dc, rect, data):
                rct = rect.contents
                monitors.append({
                    'left': rct.left,
                    'top': rct.top,
                    'right': rct.right,
                    'bottom': rct.bottom,
                    'width': rct.right - rct.left,
                    'height': rct.bottom - rct.top
                })
                return 1
            
            callback_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, 
                                              ctypes.POINTER(ctypes.wintypes.RECT), ctypes.c_double)
            enum_proc = callback_type(callback_enum_monitor)
            user32.EnumDisplayMonitors(None, None, enum_proc, 0)
            
            # 모든 모니터를 포함하는 경계 계산
            if monitors:
                min_left = min(m['left'] for m in monitors)
                min_top = min(m['top'] for m in monitors)
                max_right = max(m['right'] for m in monitors)
                max_bottom = max(m['bottom'] for m in monitors)
                
                virtual_width = max_right - min_left
                virtual_height = max_bottom - min_top
                
                print(f"[📏 다중 모니터 감지] 가상 화면 크기: {virtual_width}x{virtual_height}")
            
        except Exception as e:
            # 다중 모니터 정보를 가져오지 못한 경우 기본값 사용
            print(f"[⚠️ 다중 모니터 정보 가져오기 실패]: {e}")
        
        root.destroy()
    except:
        # 기본 화면 크기 사용
        virtual_width = 1920
        virtual_height = 1080
    
    # 전체 화면을 덮는 창 생성
    temp = tk.Toplevel()
    temp.attributes("-fullscreen", True)
    temp.geometry(f"{virtual_width}x{virtual_height}+0+0")  # 전체 가상 화면 크기로 설정
    temp.attributes("-alpha", 0.3)
    temp.attributes("-topmost", True)
    temp.configure(bg="black")
    temp.overrideredirect(True)
    
    # 화면 크기를 초과하는 캔버스 생성
    canvas = tk.Canvas(temp, bg="black", width=virtual_width, height=virtual_height)
    canvas.pack(fill="both", expand=True)
    
    rect = None
    start_x = start_y = 0
    
    def on_mouse_down(event):
        nonlocal start_x, start_y, rect
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2)
    
    def on_mouse_move(event):
        if rect:
            canvas.coords(rect, start_x, start_y, event.x, event.y)
    
# gui.py의 on_mouse_up 함수 수정 (select_area 함수 내부)
    def on_mouse_up(event):
        end_x, end_y = event.x, event.y
        x1, y1 = min(start_x, end_x), min(start_y, end_y)
        x2, y2 = max(start_x, end_x), max(start_y, end_y)
        
        # DPI 배율 적용
        dpi_scale = get_setting("DPI_SCALE", 1.0)
        if dpi_scale != 1.0:
            # 실제 화면 좌표로 변환
            x1 = int(x1 * dpi_scale)
            y1 = int(y1 * dpi_scale)
            x2 = int(x2 * dpi_scale)
            y2 = int(y2 * dpi_scale)
            print(f"[🔍 DPI 배율 적용] 원본: ({x1/dpi_scale}, {y1/dpi_scale}) - ({x2/dpi_scale}, {y2/dpi_scale}), 변환: ({x1}, {y1}) - ({x2}, {y2})")
        
        temp.destroy()
        callback((x1, y1, x2, y2))
        
    # 현재 OCR 영역 표시 (이미 설정된 경우)
    current_region = get_setting("OCR_REGION")
    if current_region:
        x1, y1, x2, y2 = current_region
        canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=2, dash=(5, 5))
        canvas.create_text((x1+x2)/2, (y1+y2)/2, text="현재 OCR 영역", fill="white")
    
    # 안내 텍스트 표시
    canvas.create_text(virtual_width/2, 50, text="OCR 영역을 드래그하여 선택하세요", 
                      fill="white", font=("Arial", 20))
    canvas.create_text(virtual_width/2, 80, text="ESC 키를 누르면 취소됩니다", 
                      fill="white", font=("Arial", 14))
    
    canvas.bind("<Button-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    
    # ESC 키로 취소
    def on_escape(event):
        temp.destroy()
    
    temp.bind("<Escape>", on_escape)

def open_settings_window(parent, overlay_label):
    """설정 창 열기"""
    win = tk.Toplevel(parent)
    win.title("설정")
    win.geometry("400x350")
    win.resizable(False, False)
    
    # 단축키 설정
    tk.Label(win, text="단축키 (예: f8)").grid(row=0, column=0, sticky="e", pady=4)
    hotkey_entry = tk.Entry(win)
    hotkey_entry.insert(0, get_setting("HOTKEY"))
    hotkey_entry.grid(row=0, column=1, sticky="w", pady=4)
    
    # 글로벌 핫키 옵션
    global_hotkey_var = BooleanVar(value=get_setting("GLOBAL_HOTKEY", True))
    tk.Checkbutton(win, text="글로벌 핫키 사용 (다른 창에서도 작동)", 
                   variable=global_hotkey_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)
    
    # GPU 사용 옵션
    gpu_var = BooleanVar(value=get_setting("USE_GPU"))
    tk.Checkbutton(win, text="GPU 사용 (속도 향상)", 
                   variable=gpu_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=4)
    
    # OCR 주기 설정
    tk.Label(win, text="OCR 주기 (초)").grid(row=3, column=0, sticky="e", pady=4)
    interval_spin = tk.Spinbox(win, from_=0.1, to=10.0, increment=0.1, format="%.1f")
    interval_spin.delete(0, "end")
    interval_spin.insert(0, get_setting("OCR_INTERVAL"))
    interval_spin.grid(row=3, column=1, sticky="w", pady=4)
    
    # 번역 엔진 선택 부분 제거 (메인 화면에서 이미 선택 가능)
    
    # 언어 자동 감지 옵션
    auto_detect_var = BooleanVar(value=get_setting("AUTO_DETECT_LANG", True))
    tk.Checkbutton(win, text="원본 언어 자동 감지 (권장)", 
                variable=auto_detect_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)
    
    # 언어 설정
    tk.Label(win, text="원본 언어 (번역할 텍스트 언어)").grid(row=5, column=0, sticky="e", pady=4)
    source_var = StringVar(value=get_setting("SOURCE_LANG"))
    source_menu = tk.OptionMenu(win, source_var, "en", "ja", "ko", "zh-CN", "es", "fr", "de", "ru")
    source_menu.grid(row=5, column=1, sticky="w", pady=4)

    tk.Label(win, text="목표 언어 (번역 결과 언어)").grid(row=6, column=0, sticky="e", pady=4)
    target_var = StringVar(value=get_setting("TARGET_LANG"))
    target_menu = tk.OptionMenu(win, target_var, "en", "ja", "ko", "zh-CN", "es", "fr", "de", "ru")
    target_menu.grid(row=6, column=1, sticky="w", pady=4)
    
    # 자동 감지 시 원본 언어 비활성화
    def update_source_menu(*args):
        source_menu.config(state="disabled" if auto_detect_var.get() else "normal")
    
    auto_detect_var.trace_add("write", update_source_menu)
    update_source_menu()  # 초기 상태 적용
    
    # 저장 버튼
    def save_and_close():
        update_setting("HOTKEY", hotkey_entry.get().strip())
        update_setting("GLOBAL_HOTKEY", global_hotkey_var.get())
        update_setting("USE_GPU", gpu_var.get())
        update_setting("OCR_INTERVAL", float(interval_spin.get()))
        # "ENGINE" 설정 저장 부분 제거
        update_setting("AUTO_DETECT_LANG", auto_detect_var.get())
        update_setting("SOURCE_LANG", source_var.get())
        update_setting("TARGET_LANG", target_var.get())
        
        # 설정 저장
        save_settings()
        
        # 필요시 OCR 리더 재초기화
        reinit_ocr_reader()
        
        win.destroy()
    
    tk.Button(win, text="저장", command=save_and_close).grid(row=7, column=0, columnspan=2, pady=10)

def setup_api_key(engine):
    """API 키 설정"""
    if engine == "deepl":
        key = simpledialog.askstring("DeepL API Key", "DeepL API Key를 입력하세요:")
        if key:
            try:
                with open("deepl.txt", "w", encoding="utf-8") as f:
                    f.write(key)
                messagebox.showinfo("완료", "deepl.txt 파일이 생성되었습니다!")
            except:
                messagebox.showerror("오류", "파일 생성에 실패했습니다.")
    
    elif engine == "libretranslate":
        api_url = simpledialog.askstring(
            "LibreTranslate API URL", 
            "LibreTranslate API URL을 입력하세요:\n(로컬 서버 기본값: http://localhost:5001/translate)",
            initialvalue=get_setting("LIBRE_API_URL") or "http://localhost:5001/translate"
        )
        
        if api_url:
            update_setting("LIBRE_API_URL", api_url)
            
            api_key = simpledialog.askstring(
                "LibreTranslate API Key (선택사항)", 
                "API 키가 있다면 입력하세요:\n(로컬 서버는 비워두세요)",
                initialvalue=get_setting("LIBRE_API_KEY") or ""
            )
            
            if api_key is not None:  # 취소가 아니면
                update_setting("LIBRE_API_KEY", api_key)
                
                try:
                    with open("libretranslate.txt", "w", encoding="utf-8") as f:
                        f.write(f"{api_url}|{api_key}")
                    messagebox.showinfo("완료", "LibreTranslate 설정이 저장되었습니다!")
                except:
                    messagebox.showerror("오류", "설정 파일 생성에 실패했습니다.")

def create_main_window():
    """메인 창 생성"""
    translating = False
    overlay, overlay_label = create_overlay_window()
    overlay.withdraw()  # 초기에는 숨김
    
    win = tk.Toplevel()
    win.title("간소화된 OCR 번역기")
    win.geometry("300x400")
    win.resizable(False, False)
    
    status = tk.Label(win, text="⚫ 번역 미사용", bg="#888888", fg="white", padx=10, pady=5)
    status.pack(fill="x")
    
    engine_var = StringVar(value=get_setting("ENGINE"))
    engine_dropdown = tk.OptionMenu(win, engine_var, "deepl", "libretranslate")
    engine_dropdown.config(width=20)
    engine_dropdown.pack(pady=10)
    
    # 번역 토글 버튼
    toggle_btn = tk.Button(win, text="▶️ 번역 시작", width=20)
    toggle_btn.pack(pady=5)
    
    def update_status(running):
        engine = get_setting("ENGINE").upper()
        status.config(
            text=f"🟢 번역 켜 ({engine})" if running else "⚫ 번역 미사용",
            bg="#3cb043" if running else "#888888"
        )
        toggle_btn.config(text="⏸️ 번역 중단" if running else "▶️ 번역 시작")
    
    def toggle_translate():
        nonlocal translating
        
        try:
            if translating:
                translating = False
                stop_ocr()
                overlay.withdraw()
                update_status(False)
            else:
                if not get_setting("OCR_REGION"):
                    messagebox.showerror("오류", "OCR 영역이 설정되지 않았습니다. OCR 위치 재설정을 먼저 해주세요.")
                    return
                
                translating = True
                engine = engine_var.get()
                update_setting("ENGINE", engine)
                
                start_ocr_thread(overlay_label)
                overlay.deiconify()
                x, y = get_setting("OUTPUT_POSITION")
                overlay.geometry(f"800x120+{x}+{y}")
                
                update_status(True)
        except Exception as e:
            messagebox.showerror("오류", f"번역 시작 중 오류가 발생했습니다: {str(e)}")
    
    toggle_btn.config(command=toggle_translate)
    
    # OCR 위치 설정 버튼
    def ocr_reset():
        def on_area_selected(box):
            update_setting("OCR_REGION", box)
            save_settings()
            messagebox.showinfo("완료", "OCR 영역이 설정되었습니다.")
        
        select_area(on_area_selected)
    
    # 오버레이 위치 설정 버튼
    def overlay_reset():
        select_area(lambda pos: (
            update_setting("OUTPUT_POSITION", (pos[0], pos[1])),
            save_settings()
        ))
        messagebox.showinfo("완료", "오버레이 위치가 설정되었습니다.")
    
    # 기본 위치로 리셋 버튼
    def reset_to_default():
        update_setting("OCR_REGION", (200, 800, 1700, 1000))
        update_setting("OUTPUT_POSITION", (600, 850))
        save_settings()
        messagebox.showinfo("초기화 완료", "기본 위치로 초기화되었습니다.")
    
    # 핫키 등록
    # gui.py (계속)
    # 버튼 추가
    tk.Button(win, text="📐 OCR 위치 재설정", command=ocr_reset, width=20).pack(pady=5)
    tk.Button(win, text="🖼️ 오버레이 위치 재설정", command=overlay_reset, width=20).pack(pady=5)
    tk.Button(win, text="🧹 위치 초기화", command=reset_to_default, width=20).pack(pady=5)
    
    # API 키 설정 버튼
    tk.Button(win, text="🔑 DeepL API 설정", command=lambda: setup_api_key("deepl"), width=20).pack(pady=5)
    tk.Button(win, text="🌍 LibreTranslate 설정", command=lambda: setup_api_key("libretranslate"), width=20).pack(pady=5)
    
    # 설정 버튼
    tk.Button(win, text="⚙️ 설정", command=lambda: open_settings_window(win, overlay_label), width=20).pack(pady=5)
    
    # 종료 버튼
    def quit_program():
        stop_ocr()
        win.destroy()
        overlay.destroy()
        os._exit(0)
    
    tk.Button(win, text="❌ 프로그램 종료", command=quit_program, width=20).pack(pady=5)
    
    # 프로그램 정보 레이블
    blog = tk.Label(win, text="🔗 제작자 블로그", fg="blue", cursor="hand2")
    blog.pack(pady=5)
    blog.bind("<Button-1>", lambda e: webbrowser.open("https://sonagi-psy.tistory.com/8"))
    
    # 종료 시 정리
    win.protocol("WM_DELETE_WINDOW", quit_program)
    
    def register_hotkey():
        try:
            # 기존 단축키 제거
            try:
                keyboard.unhook_all_hotkeys()
                print("[✅ 기존 단축키 제거됨]")
            except Exception as e:
                print(f"[⚠️ 기존 단축키 제거 실패] {e}")
            
            # 새 단축키 등록
            hotkey = get_setting("HOTKEY", "f8")
            print(f"[🔍 단축키 등록 시도] 키: {hotkey}")
            
            # 직접 함수 참조로 변경 (toggle_btn.invoke 대신)
            keyboard.add_hotkey(hotkey, toggle_translate)
            print(f"[✅ 단축키 '{hotkey}' 등록됨]")
            
            # 테스트용 추가 코드 - 잘 작동하는지 확인하기 위한 임시 코드
            keyboard.add_hotkey('ctrl+shift+t', lambda: print("테스트 핫키 작동 확인!"))
            
        except Exception as e:
            print(f"[⚠️ 단축키 등록 실패] {e}")
            print(traceback.format_exc())  # 전체 오류 스택 표시
    
    # 초기 단축키 등록
    register_hotkey()
    
    return win, overlay, overlay_label, toggle_btn, register_hotkey