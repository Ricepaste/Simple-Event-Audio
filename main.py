import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pygame
import os
import threading
import time

class UltimateAudioController:
    def __init__(self, root):
        self.root = root
        self.root.title("頒獎典禮音控系統 (開發：家榕)")
        self.root.geometry("850x550")
        
        # 初始化 Pygame
        # buffer 設小一點可以減少播放延遲，但太小可能會破音，2048 是安全值
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.mixer.set_num_channels(8)
        
        # 核心變數
        self.playlist_paths = [] # 儲存路徑順序
        self.fade_ms = 2000      # 淡入淡出 2秒
        
        # 雙聲道系統
        self.channel_a = pygame.mixer.Channel(0)
        self.channel_b = pygame.mixer.Channel(1)
        self.current_channel = None
        
        self.current_playing_index = None
        self.is_paused = False
        
        # 音效快取 (預載入的核心)
        self.sound_cache = {} 
        self.is_loading = False # 避免重複載入衝突

        # --- UI 介面 ---
        
        # 狀態顯示 (頂部)
        self.lbl_status = tk.Label(root, text="請加入音樂檔案", fg="#333", font=("微軟正黑體", 12, "bold"))
        self.lbl_status.pack(pady=5)

        # 進度條 (載入時顯示)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        # 預設隱藏進度條，載入時才 pack
        
        # 檔案操作區
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        self.btn_add = tk.Button(btn_frame, text="📂 加入音樂 (自動預載)", command=self.add_files_thread, width=20, bg="#e1f5fe")
        self.btn_add.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = tk.Button(btn_frame, text="🗑 清空清單", command=self.clear_playlist, width=15)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        # 清單顯示
        self.listbox = tk.Listbox(root, selectmode=tk.SINGLE, width=80, height=12, font=("Consolas", 12))
        self.listbox.pack(pady=5)
        self.listbox.bind('<Double-1>', self.on_double_click)

        # 控制區
        ctrl_frame = tk.LabelFrame(root, text="播放控制", padx=10, pady=10)
        ctrl_frame.pack(pady=10)

        self.btn_play_pause = tk.Button(ctrl_frame, text="▶ 播放", bg="#90EE90", width=12, height=2, command=self.toggle_play_pause)
        self.btn_play_pause.pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="🔄 重播 (Replay)", bg="orange", width=12, height=2, command=self.replay_current).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl_frame, text="⏹ 停止 (Fade Out)", bg="#FFB6C1", width=12, height=2, command=self.stop_all).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl_frame, text="⏭ 下一首", width=10, height=2, command=self.play_next).pack(side=tk.LEFT, padx=5)

        # 音量
        vol_frame = tk.Frame(root)
        vol_frame.pack(pady=5)
        tk.Label(vol_frame, text="音量: ").pack(side=tk.LEFT)
        self.vol_slider = tk.Scale(vol_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400, command=self.update_volume)
        self.vol_slider.set(80)
        self.vol_slider.pack(side=tk.LEFT)

    def add_files_thread(self):
        """啟動背景執行緒來載入檔案，避免介面卡死"""
        if self.is_loading:
            return
        files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.wma")])
        if not files:
            return

        # 顯示進度條
        self.progress_bar.pack(pady=5, fill=tk.X, padx=20)
        self.btn_add.config(state=tk.DISABLED, text="正在解碼載入中...")
        self.is_loading = True
        
        # 開啟執行緒
        threading.Thread(target=self.load_files_task, args=(files,), daemon=True).start()

    def load_files_task(self, files):
        """背景載入任務"""
        total = len(files)
        success_count = 0
        
        for idx, file_path in enumerate(files):
            try:
                # 這裡最花時間：解碼並載入記憶體
                if file_path not in self.sound_cache:
                    sound = pygame.mixer.Sound(file_path)
                    self.sound_cache[file_path] = sound
                
                # 因為 Listbox 不是 Thread-safe，需用 root.after 回到主線程更新 UI
                self.root.after(0, self.update_listbox, file_path)
                success_count += 1
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
            
            # 更新進度條
            progress = ((idx + 1) / total) * 100
            self.root.after(0, self.update_progress, progress, file_path)

        self.root.after(0, self.finish_loading)

    def update_listbox(self, file_path):
        self.playlist_paths.append(file_path)
        self.listbox.insert(tk.END, os.path.basename(file_path))

    def update_progress(self, value, current_file):
        self.progress_var.set(value)
        self.lbl_status.config(text=f"正在預載入: {os.path.basename(current_file)}...", fg="blue")

    def finish_loading(self):
        self.is_loading = False
        self.btn_add.config(state=tk.NORMAL, text="📂 加入音樂 (自動預載)")
        self.progress_bar.pack_forget() # 隱藏進度條
        self.lbl_status.config(text="就緒 - 所有音樂已載入記憶體", fg="green")
        messagebox.showinfo("完成", "音樂載入完成！現在播放將不會有延遲。")

    def clear_playlist(self):
        self.stop_all()
        self.playlist_paths = []
        self.listbox.delete(0, tk.END)
        # 注意：我們不一定要清空 self.sound_cache，保留著下次加回來不用重新解碼
        # 但如果怕記憶體爆炸，可以清空: self.sound_cache.clear()
        self.lbl_status.config(text="清單已清空")

    def crossfade_to(self, index):
        if index < 0 or index >= len(self.playlist_paths):
            return

        file_path = self.playlist_paths[index]
        
        # 直接從 Cache 拿，理論上這裡一定要有，因為加入時已經載過了
        sound = self.sound_cache.get(file_path)
        
        if not sound:
            # 萬一真的沒有 (極端情況)，才現場載入
            try:
                sound = pygame.mixer.Sound(file_path)
                self.sound_cache[file_path] = sound
            except:
                return

        # 決定聲道
        target_channel = self.channel_a
        old_channel = self.channel_b
        if self.current_channel == self.channel_a:
            target_channel = self.channel_b
            old_channel = self.channel_a
        
        # 執行 Crossfade
        if old_channel.get_busy():
            old_channel.fadeout(self.fade_ms)
        
        target_channel.set_volume(self.vol_slider.get() / 100)
        target_channel.play(sound, loops=-1, fade_ms=self.fade_ms)
        
        self.current_channel = target_channel
        self.current_playing_index = index
        self.is_paused = False
        
        self.lbl_status.config(text=f"正在播放: {os.path.basename(file_path)}", fg="black")
        self.btn_play_pause.config(text="⏸ 暫停")
        
        # 列表跟隨
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)

    def on_double_click(self, event):
        selection = self.listbox.curselection()
        if selection:
            self.crossfade_to(selection[0])

    def toggle_play_pause(self):
        if self.current_channel is None or not self.current_channel.get_busy():
            if self.is_paused and self.current_channel:
                 self.current_channel.unpause()
                 self.is_paused = False
                 self.btn_play_pause.config(text="⏸ 暫停")
                 self.lbl_status.config(text="繼續播放", fg="black")
            else:
                selection = self.listbox.curselection()
                if selection:
                    self.crossfade_to(selection[0])
                elif self.playlist_paths:
                    self.crossfade_to(0)
            return

        if not self.is_paused:
            self.current_channel.pause()
            self.is_paused = True
            self.btn_play_pause.config(text="▶ 播放")
            self.lbl_status.config(text="已暫停 (待機中)", fg="red")
        else:
            self.current_channel.unpause()
            self.is_paused = False
            self.btn_play_pause.config(text="⏸ 暫停")
            self.lbl_status.config(text="繼續播放", fg="black")

    def replay_current(self):
        if self.current_playing_index is not None:
            self.crossfade_to(self.current_playing_index)

    def play_next(self):
        if self.current_playing_index is not None:
            next_idx = self.current_playing_index + 1
            if next_idx < len(self.playlist_paths):
                self.crossfade_to(next_idx)

    def stop_all(self):
        if self.channel_a.get_busy():
            self.channel_a.fadeout(self.fade_ms)
        if self.channel_b.get_busy():
            self.channel_b.fadeout(self.fade_ms)
        self.is_paused = False
        self.btn_play_pause.config(text="▶ 播放")
        self.lbl_status.config(text="已停止", fg="red")

    def update_volume(self, val):
        vol = int(val) / 100
        self.channel_a.set_volume(vol)
        self.channel_b.set_volume(vol)

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateAudioController(root)
    root.mainloop()