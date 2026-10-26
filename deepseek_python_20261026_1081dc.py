import os
import sys
import asyncio
import threading
import win32api
import win32con
import customtkinter as ctk
from pynput import keyboard
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
)

# --- Пути к ресурсам (работает и в .py, и в собранном .exe) ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- Медиа-логика ---
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3


def press_media_key(vk_code):
    win32api.keybd_event(vk_code, 0, 0, 0)
    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)


async def _get_track_info():
    try:
        sessions = await MediaManager.request_async()
        session = sessions.get_current_session()
        if session:
            info = await session.try_get_media_properties_async()
            return {
                "title": info.title or "Неизвестно",
                "artist": info.artist or "Неизвестен",
            }
    except Exception:
        pass
    return {"title": "Ничего не играет", "artist": ""}


# --- GUI ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Загружаем свою тему
        ctk.set_default_color_theme(resource_path("ds.json"))
        ctk.set_appearance_mode("dark")

        self.title("Media Controller")
        self.geometry("420x260")
        self.resizable(False, False)
        self.attributes("-alpha", 0.96)  # лёгкая прозрачность окна

        # Иконка окна с задержкой, чтобы перебить стандартную от CustomTkinter
        icon_path = resource_path("my_icon.ico")
        self.after(200, lambda: self.iconbitmap(icon_path))

        # Цвета (под вашу фиолетовую тему)
        BG_CARD = "#241640"
        ACCENT = "#8b5cf6"
        ACCENT_HOVER = "#a78bfa"
        TEXT_MAIN = "#ede9fe"
        TEXT_SUB = "#a78bfa"

        # --- Карточка с треком ---
        card = ctk.CTkFrame(
            self, corner_radius=18, fg_color=BG_CARD, border_width=1,
            border_color="#4a2f80"
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Акцентная полоска сверху карточки
        accent_bar = ctk.CTkFrame(card, height=4, corner_radius=2, fg_color=ACCENT)
        accent_bar.pack(fill="x", padx=20, pady=(18, 14))

        # Название трека
        self.title_label = ctk.CTkLabel(
            card, text="Загрузка...",
            font=("Segoe UI Black", 20),
            text_color=TEXT_MAIN,
            wraplength=340,
            justify="center",
        )
        self.title_label.pack(padx=20, pady=(4, 2))

        # Исполнитель
        self.artist_label = ctk.CTkLabel(
            card, text="",
            font=("Segoe UI Light", 13),
            text_color=TEXT_SUB,
            wraplength=340,
            justify="center",
        )
        self.artist_label.pack(padx=20, pady=(0, 18))

        # --- Кнопки управления ---
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=(0, 12))

        self.prev_btn = ctk.CTkButton(
            btn_frame, text="⏮", width=52, height=40,
            corner_radius=12,
            fg_color="transparent",
            hover_color="#3b2a66",
            text_color=TEXT_MAIN,
            font=("Segoe UI", 22),
            command=self.prev_track,
        )
        self.prev_btn.pack(side="left", padx=6)

        self.play_btn = ctk.CTkButton(
            btn_frame, text="⏯", width=64, height=44,
            corner_radius=14,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#f5f3ff",
            font=("Segoe UI", 24),
            command=self.play_pause,
        )
        self.play_btn.pack(side="left", padx=6)

        self.next_btn = ctk.CTkButton(
            btn_frame, text="⏭", width=52, height=40,
            corner_radius=12,
            fg_color="transparent",
            hover_color="#3b2a66",
            text_color=TEXT_MAIN,
            font=("Segoe UI", 22),
            command=self.next_track,
        )
        self.next_btn.pack(side="left", padx=6)

        # --- Старт обновления и горячих клавиш ---
        self.update_track_info()
        self.start_hotkeys()

    def update_track_info(self):
        try:
            info = asyncio.run(_get_track_info())
            self.title_label.configure(text=info["title"])
            self.artist_label.configure(text=info["artist"])
        except Exception:
            pass
        self.after(2000, self.update_track_info)

    def prev_track(self):
        press_media_key(VK_MEDIA_PREV_TRACK)
        self.after(300, self.update_track_info)

    def next_track(self):
        press_media_key(VK_MEDIA_NEXT_TRACK)
        self.after(300, self.update_track_info)

    def play_pause(self):
        press_media_key(VK_MEDIA_PLAY_PAUSE)
        self.after(300, self.update_track_info)

    def start_hotkeys(self):
        def listener():
            def on_press(key):
                try:
                    if key == keyboard.Key.f2:
                        self.after(0, self.prev_track)
                    elif key == keyboard.Key.f3:
                        self.after(0, self.next_track)
                    elif key == keyboard.Key.f4:
                        self.after(0, self.play_pause)
                except Exception:
                    pass

            with keyboard.Listener(on_press=on_press) as l:
                l.join()

        t = threading.Thread(target=listener, daemon=True)
        t.start()


if __name__ == "__main__":
    app = App()
    app.mainloop()