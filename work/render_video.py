from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUTPUTS = ROOT / "outputs"
SCENES = WORK / "scenes"
FONT = "/System/Library/Fonts/PingFang.ttc"
FFMPEG = WORK / "vendor/imageio_ffmpeg/binaries/ffmpeg-macos-x86_64-v7.1"

W, H = 1920, 1080
BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#f0f6fc"
MUTED = "#8b949e"
GREEN = "#3fb950"
BLUE = "#58a6ff"
YELLOW = "#d29922"
RED = "#f85149"

SCENE_DATA = [
    ("01", "GitHub 變更檢視", "Notebook × Pipeline", "先建立全局，再深入每一個變更", "overview"),
    ("02", "先看變更總覽", "Commit · Pull Request · Changed files", "掌握檔案範圍、資料夾與改動類型", "diff"),
    ("03", "Notebook 三個檢查點", "資料來源 · 處理邏輯 · 輸出結果", "不要只看紅綠行數，要理解 cell 之間的關係", "notebook"),
    ("04", "讀懂 Notebook Diff", "Code · Output · Metadata", "回到輸入、運算與下游影響", "cells"),
    ("05", "Pipeline 影響更廣", "Trigger · Runtime · Dependency · Deploy", "幾行 YAML 也可能改變整條交付流程", "pipeline"),
    ("06", "檢查自動化流程", "何時觸發？在哪執行？輸出到哪？", "確認每一步的輸入與輸出完整銜接", "workflow"),
    ("07", "CI 結果怎麼看", "通過不等於正確，失敗要回到 Log", "區分依賴、權限、資料與邏輯問題", "ci"),
    ("08", "四步判讀法", "檔案 → 邏輯 → 流程 → CI", "讓變更可追蹤、可重現、可靠落地", "summary"),
]

def font(size, index=0):
    return ImageFont.truetype(FONT, size, index=index)

def rounded(draw, box, fill, outline=None, radius=16, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def text(draw, xy, value, size, color=TEXT, anchor="la"):
    draw.text(xy, value, font=font(size), fill=color, anchor=anchor)

def pill(draw, x, y, label, color):
    f = font(26)
    box = draw.textbbox((0, 0), label, font=f)
    width = box[2] - box[0] + 42
    rounded(draw, (x, y, x + width, y + 46), PANEL, color, 8, 2)
    draw.text((x + 21, y + 23), label, font=f, fill=color, anchor="lm")
    return x + width + 14

def draw_header(draw, number):
    text(draw, (90, 65), "GITHUB CHANGE REVIEW", 25, BLUE)
    text(draw, (1830, 65), f"{number} / 08", 25, MUTED, "ra")
    draw.line((90, 104, 1830, 104), fill=BORDER, width=2)

def fake_window(draw, kind):
    x1, y1, x2, y2 = 90, 390, 1830, 940
    rounded(draw, (x1, y1, x2, y2), PANEL, BORDER, 12, 2)
    draw.rectangle((x1, y1, x2, y1 + 62), fill="#21262d")
    for i, c in enumerate((RED, YELLOW, GREEN)):
        draw.ellipse((x1 + 28 + i * 34, y1 + 22, x1 + 44 + i * 34, y1 + 38), fill=c)
    text(draw, (x1 + 155, y1 + 32), "project / changes", 23, MUTED, "lm")

    if kind in ("overview", "diff"):
        paths = ["notebooks/analysis.ipynb", ".github/workflows/pipeline.yml", "src/transform.py"]
        for i, path in enumerate(paths):
            yy = 500 + i * 112
            text(draw, (145, yy), path, 28)
            text(draw, (1410, yy), f"+{12 + i * 7}", 27, GREEN)
            text(draw, (1530, yy), f"-{3 + i}", 27, RED)
            draw.line((145, yy + 48, 1770, yy + 48), fill=BORDER, width=1)
        text(draw, (145, 860), "3 files changed", 28, MUTED)
    elif kind in ("notebook", "cells"):
        for i, (label, accent) in enumerate((("[1]  載入資料", BLUE), ("[2]  清理與計算", YELLOW), ("[3]  圖表與結論", GREEN))):
            yy = 490 + i * 130
            rounded(draw, (140, yy, 1775, yy + 92), "#0d1117", BORDER, 8, 1)
            draw.rectangle((140, yy, 148, yy + 92), fill=accent)
            text(draw, (180, yy + 46), label, 29, TEXT, "lm")
            for j in range(3):
                draw.rectangle((720 + j * 265, yy + 29, 920 + j * 265, yy + 41), fill="#30363d")
        text(draw, (140, 885), "INPUT  →  TRANSFORM  →  OUTPUT", 27, MUTED)
    elif kind in ("pipeline", "workflow"):
        labels = [("PUSH", BLUE), ("TEST", YELLOW), ("BUILD", GREEN), ("DEPLOY", "#a371f7")]
        for i, (label, color) in enumerate(labels):
            xx = 140 + i * 405
            rounded(draw, (xx, 570, xx + 300, 700), "#0d1117", color, 12, 3)
            text(draw, (xx + 150, 635), label, 31, color, "mm")
            if i < len(labels) - 1:
                draw.line((xx + 300, 635, xx + 390, 635), fill=MUTED, width=4)
                draw.polygon(((xx + 390, 635), (xx + 370, 622), (xx + 370, 648)), fill=MUTED)
        text(draw, (140, 835), "trigger   runtime   dependencies   artifacts", 28, MUTED)
    elif kind == "ci":
        rows = [("Unit tests", "PASS", GREEN), ("Notebook smoke test", "PASS", GREEN), ("Deploy preview", "CHECK LOG", YELLOW)]
        for i, (name, status, color) in enumerate(rows):
            yy = 500 + i * 112
            text(draw, (150, yy), name, 29)
            rounded(draw, (1390, yy - 24, 1725, yy + 28), "#0d1117", color, 8, 2)
            text(draw, (1557, yy + 2), status, 24, color, "mm")
            draw.line((150, yy + 50, 1740, yy + 50), fill=BORDER, width=1)
    else:
        labels = [("FILES", BLUE), ("LOGIC", YELLOW), ("FLOW", "#a371f7"), ("CI", GREEN)]
        for i, (label, color) in enumerate(labels):
            xx = 150 + i * 405
            draw.ellipse((xx, 555, xx + 145, 700), fill="#0d1117", outline=color, width=5)
            text(draw, (xx + 72, 628), str(i + 1), 44, color, "mm")
            text(draw, (xx + 72, 760), label, 27, TEXT, "mm")

def render_scene(item):
    number, title, kicker, subtitle, kind = item
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    draw_header(draw, number)
    text(draw, (90, 165), title, 66)
    text(draw, (90, 260), kicker, 34, BLUE)
    text(draw, (90, 325), subtitle, 28, MUTED)
    fake_window(draw, kind)
    x = 90
    for label, color in (("NOTEBOOK", BLUE), ("PIPELINE", "#a371f7"), ("CI", GREEN)):
        x = pill(draw, x, 980, label, color)
    image.save(SCENES / f"scene_{number}.png", quality=95)

def duration(path):
    result = subprocess.run([
        str(FFMPEG), "-i", str(path), "-f", "null", "-"
    ], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            value = line.split("Duration:", 1)[1].split(",", 1)[0].strip()
            h, m, s = value.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError("Could not read audio duration")

def build_video(audio, subtitles):
    total = duration(audio)
    per_scene = total / len(SCENE_DATA)
    concat = WORK / "scenes.txt"
    lines = []
    for item in SCENE_DATA:
        lines.append(f"file '{(SCENES / ('scene_' + item[0] + '.png')).as_posix()}'")
        lines.append(f"duration {per_scene:.3f}")
    lines.append(f"file '{(SCENES / 'scene_08.png').as_posix()}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")

    output = OUTPUTS / "github_notebook_pipeline_zh_tw.mp4"
    style = "FontName=PingFang TC,FontSize=16,PrimaryColour=&H00FFFFFF,BackColour=&H99000000,OutlineColour=&HCC000000,BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginV=54"
    subprocess.run([
        str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-i", str(audio), "-vf",
        f"fps=30,scale=1920:1080,subtitles={subtitles}:force_style='{style}',fade=t=in:st=0:d=0.5,fade=t=out:st={max(total-0.6,0):.2f}:d=0.5",
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "medium",
        "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", str(output)
    ], check=True)
    print(json.dumps({"output": str(output), "duration": total}, ensure_ascii=False))

def main():
    SCENES.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    for item in SCENE_DATA:
        render_scene(item)
    if len(sys.argv) == 3:
        build_video(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
    else:
        print("Rendered scene images. Pass audio and subtitle paths to build video.")

if __name__ == "__main__":
    main()
