from pathlib import Path
import math
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
FFMPEG = WORK / "vendor/imageio_ffmpeg/binaries/ffmpeg-macos-x86_64-v7.1"
SOURCE = WORK / "narration.txt"
SEGMENTS = WORK / "voice_segments"
OUTPUT_AUDIO = WORK / "voiceover.wav"
OUTPUT_SRT = WORK / "voiceover.srt"

def timestamp(seconds):
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def subtitle_chunks(sentence, limit=18):
    chunks = []
    remaining = sentence.strip()
    while len(remaining) > limit:
        parts_left = math.ceil(len(remaining) / limit)
        balanced = math.ceil(len(remaining) / parts_left)
        start = max(6, balanced - 4)
        end = min(len(remaining), balanced + 5)
        window = remaining[start:end]
        offsets = [window.find(mark) for mark in "，、；："]
        offsets = [offset for offset in offsets if offset >= 0]
        cut = start + min(offsets) + 1 if offsets else balanced
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks

def audio_duration(path):
    result = subprocess.run(
        [str(FFMPEG), "-i", str(path), "-f", "null", "-"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Cannot read duration: {path}")
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))

def main():
    text = SOURCE.read_text(encoding="utf-8")
    sentences = [item.strip() for item in re.split(r"(?<=[。！？])", text) if item.strip()]
    SEGMENTS.mkdir(parents=True, exist_ok=True)

    segment_paths = []
    subtitle_rows = []
    cursor = 0.0
    for index, sentence in enumerate(sentences, start=1):
        aiff = SEGMENTS / f"{index:03}.aiff"
        wav = SEGMENTS / f"{index:03}.wav"
        subprocess.run(["say", "-v", "Tingting", "-r", "168", "-o", str(aiff), sentence], check=True)
        subprocess.run([
            str(FFMPEG), "-y", "-i", str(aiff), "-ar", "48000", "-ac", "2",
            "-af", "highpass=f=70,lowpass=f=12000,loudnorm=I=-16:TP=-1.5:LRA=8",
            str(wav),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        duration = audio_duration(wav)
        chunks = subtitle_chunks(sentence)
        total_chars = sum(len(chunk) for chunk in chunks)
        chunk_start = cursor
        for chunk in chunks:
            share = duration * len(chunk) / total_chars
            subtitle_rows.append((chunk_start, chunk_start + share, chunk))
            chunk_start += share
        cursor += duration
        segment_paths.append(wav)

    concat = SEGMENTS / "concat.txt"
    concat.write_text("\n".join(f"file '{path.as_posix()}'" for path in segment_paths) + "\n", encoding="utf-8")
    subprocess.run([
        str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:a", "pcm_s16le", str(OUTPUT_AUDIO),
    ], check=True)

    blocks = []
    for index, (start, end, sentence) in enumerate(subtitle_rows, start=1):
        blocks.append(f"{index}\n{timestamp(start)} --> {timestamp(end)}\n{sentence}\n")
    OUTPUT_SRT.write_text("\n".join(blocks), encoding="utf-8")
    print(f"Created {OUTPUT_AUDIO} and {OUTPUT_SRT}; duration {cursor:.2f}s")

if __name__ == "__main__":
    main()
