# GitHub Notebook 與 Pipeline 變更檢視

繁體中文 1080p 教學影片，說明如何從 GitHub 的 commit、pull request 與 changed files 判讀 notebook、pipeline 及 CI 變更。

## 成品

- `outputs/github_notebook_pipeline_zh_tw.mp4`：3 分 55 秒成片，H.264 / AAC，已燒錄繁體中文字幕。
- `outputs/subtitles_zh_tw.srt`：可另行上傳到 YouTube 的字幕檔。
- `outputs/thumbnail.png`：1920 × 1080 縮圖。
- `outputs/narration_zh_tw.md`：完整旁白稿。
- `outputs/reedit_plan.md`：內容結構與後製規格。

## 內容章節

1. GitHub 變更總覽
2. Notebook 三個檢查點
3. Notebook diff 的判讀方式
4. Pipeline 的影響範圍
5. 自動化流程與 CI 結果
6. 四步判讀法

## 重新建置

需要 macOS、Python 3、Pillow，以及可執行的 ffmpeg。

```bash
PYTHONPATH=work/vendor python3 work/make_local_voice.py
PYTHONPATH=work/vendor python3 work/render_video.py work/voiceover.wav work/voiceover.srt
```

旁白使用系統中文語音重新製作，不包含原始影片音軌，也不模仿特定真人聲紋。
