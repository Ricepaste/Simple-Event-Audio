# Simple-Event-Audio
[![GitHub license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Ricepaste/Simple-Event-Audio/blob/v1.0/LICENSE)

## 介紹
因為 Windows Media Player 太爛，我在頒獎典禮前 24 小時內寫出了這個支援自動 Crossfade 和零延遲的音控小軟體
<br>
\#better than Windows Media Player

## 用法
開啟程式後，選取所有預計撥放會使用的音檔使其載入記憶體。雙擊音樂檔案即可切歌或撥放。除了"播放/暫停"鈕之外，其他按鈕都有淡入/淡出的音效效果。

## 特性
- 自動 Crossfade
- 零延遲
- 自動重播 (無法調整，預設單曲循環)
- 音量可調整
- 暫無法調整與查看撥放進度
- 多執行緒

## 下載 & 匯出為exe
```bash
pyinstaller --onefile --noconsole --name AwardPlayer main.py
```

release中也有提供最新的打包檔供下載