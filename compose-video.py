#!/usr/bin/env python3
"""Compose the Arrow Puzzle showcase video using FFmpeg."""
import subprocess
import os
import json

PROJECT = "/app/projects/arrow-puzzle-showcase"
ASSETS = f"{PROJECT}/assets"
RENDERS = f"{PROJECT}/renders"
os.makedirs(RENDERS, exist_ok=True)
os.makedirs(f"{ASSETS}/audio", exist_ok=True)

# ─── Step 1: Generate narration with Piper TTS ───
narration_segments = [
    ("intro", "Arrow Puzzle. Tap arrows to escape them off the board."),
    ("gameplay", "Find the clear path. Tap, and watch them fly."),
    ("progress", "Over two hundred hand crafted levels. Six tiers of increasing challenge."),
    ("cta", "Free, offline, and works on any device. Try it today."),
]

print("=== Generating narration ===")
for name, text in narration_segments:
    out_path = f"{ASSETS}/audio/{name}.wav"
    # Use piper TTS
    cmd = f'echo "{text}" | piper --model en_US-lessac-medium --output_file {out_path}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if os.path.exists(out_path):
        # Get duration
        probe = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'json', out_path],
            capture_output=True, text=True
        )
        dur = json.loads(probe.stdout)['format']['duration']
        print(f"  {name}: {text[:50]}... ({dur}s)")
    else:
        print(f"  FAILED: {name} - {result.stderr[:200]}")

# ─── Step 2: Convert gameplay webm to mp4 ───
print("\n=== Converting gameplay video ===")
subprocess.run([
    'ffmpeg', '-y', '-i', f'{ASSETS}/video/gameplay-raw.webm',
    '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
    '-vf', 'fps=30',
    f'{ASSETS}/video/gameplay.mp4'
], capture_output=True)
print("  Converted to mp4")

# Get gameplay video duration
probe = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'json',
     f'{ASSETS}/video/gameplay.mp4'],
    capture_output=True, text=True
)
gameplay_dur = float(json.loads(probe.stdout)['format']['duration'])
print(f"  Gameplay duration: {gameplay_dur:.1f}s")

# ─── Step 3: Create title card image with FFmpeg ───
print("\n=== Creating title card ===")
# Dark background with gradient text effect
subprocess.run([
    'ffmpeg', '-y',
    '-f', 'lavfi', '-i', f'color=c=0x06070F:s=780x1688:d=1',
    '-vf', (
        "drawtext=text='Arrow':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "fontsize=120:fontcolor=0x7B6FFF:x=(w-text_w)/2:y=h/2-180,"
        "drawtext=text='Puzzle':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "fontsize=120:fontcolor=0x54C5FF:x=(w-text_w)/2:y=h/2-40,"
        "drawtext=text='Tap Away Game':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "fontsize=48:fontcolor=0x585A78:x=(w-text_w)/2:y=h/2+120"
    ),
    '-frames:v', '1',
    f'{ASSETS}/images/title-card.png'
], capture_output=True)
print("  Title card created")

# ─── Step 4: Create feature card ───
subprocess.run([
    'ffmpeg', '-y',
    '-f', 'lavfi', '-i', f'color=c=0x06070F:s=780x1688:d=1',
    '-vf', (
        "drawtext=text='220+ Levels':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "fontsize=72:fontcolor=0x7B6FFF:x=(w-text_w)/2:y=h/2-260,"
        "drawtext=text='6 Difficulty Tiers':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "fontsize=72:fontcolor=0x54C5FF:x=(w-text_w)/2:y=h/2-120,"
        "drawtext=text='Daily Challenges':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "fontsize=72:fontcolor=0x4DDBA6:x=(w-text_w)/2:y=h/2+20,"
        "drawtext=text='Works Offline':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "fontsize=72:fontcolor=0xFFD060:x=(w-text_w)/2:y=h/2+160,"
        "drawtext=text='100%% Free':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "fontsize=72:fontcolor=0xFF7A5C:x=(w-text_w)/2:y=h/2+300"
    ),
    '-frames:v', '1',
    f'{ASSETS}/images/features-card.png'
], capture_output=True)
print("  Features card created")

# ─── Step 5: Compose final 30-second video ───
print("\n=== Composing final video ===")

# Build the concat approach:
# 0-4s:   Title card with fade in (over narration intro)
# 4-18s:  Gameplay footage (speed adjusted to fit)
# 18-25s: More gameplay / level clear moments
# 25-29s: Features card
# 29-30s: Home screen / closing

# First, create segments as individual clips

# Segment 1: Title card (4s) with narration
subprocess.run([
    'ffmpeg', '-y',
    '-loop', '1', '-i', f'{ASSETS}/images/title-card.png',
    '-i', f'{ASSETS}/audio/intro.wav',
    '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
    '-t', '4.5',
    '-vf', 'fps=30,fade=in:0:15,fade=out:st=3.8:d=0.7',
    '-af', 'afade=in:d=0.3',
    '-pix_fmt', 'yuv420p', '-shortest',
    f'{RENDERS}/seg1-title.mp4'
], capture_output=True)
print("  Segment 1: Title card (4.5s)")

# Segment 2: Gameplay - first portion sped up to show action (12s)
# Speed up the gameplay to fit exciting moments into 12 seconds
speed_factor = gameplay_dur / 12.0
pts_factor = 1.0 / speed_factor
subprocess.run([
    'ffmpeg', '-y',
    '-i', f'{ASSETS}/video/gameplay.mp4',
    '-i', f'{ASSETS}/audio/gameplay.wav',
    '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
    '-t', '12',
    '-vf', f'setpts={pts_factor:.4f}*PTS,fps=30,fade=in:0:10,fade=out:st=11.3:d=0.7',
    '-af', 'afade=in:d=0.3,afade=out:d=0.5',
    '-pix_fmt', 'yuv420p', '-shortest',
    f'{RENDERS}/seg2-gameplay.mp4'
], capture_output=True)
print("  Segment 2: Gameplay (12s)")

# Segment 3: Level select screenshot as video (3s) with narration
subprocess.run([
    'ffmpeg', '-y',
    '-loop', '1', '-i', f'{ASSETS}/images/11-levels-screen.png',
    '-i', f'{ASSETS}/audio/progress.wav',
    '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
    '-t', '5',
    '-vf', 'fps=30,fade=in:0:10,fade=out:st=4.3:d=0.7',
    '-af', 'afade=in:d=0.2',
    '-pix_fmt', 'yuv420p', '-shortest',
    f'{RENDERS}/seg3-levels.mp4'
], capture_output=True)
print("  Segment 3: Levels (5s)")

# Segment 4: Features card (5s) with narration
subprocess.run([
    'ffmpeg', '-y',
    '-loop', '1', '-i', f'{ASSETS}/images/features-card.png',
    '-i', f'{ASSETS}/audio/progress.wav',
    '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
    '-t', '5',
    '-vf', 'fps=30,fade=in:0:10,fade=out:st=4.3:d=0.7',
    '-af', 'afade=in:d=0.2,afade=out:d=0.4',
    '-pix_fmt', 'yuv420p', '-shortest',
    f'{RENDERS}/seg4-features.mp4'
], capture_output=True)
print("  Segment 4: Features (5s)")

# Segment 5: Closing - home screen (3.5s)
subprocess.run([
    'ffmpeg', '-y',
    '-loop', '1', '-i', f'{ASSETS}/images/12-home-final.png',
    '-i', f'{ASSETS}/audio/cta.wav',
    '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
    '-t', '3.5',
    '-vf', 'fps=30,fade=in:0:10,fade=out:st=2.8:d=0.7',
    '-af', 'afade=in:d=0.2,afade=out:d=0.5',
    '-pix_fmt', 'yuv420p', '-shortest',
    f'{RENDERS}/seg5-close.mp4'
], capture_output=True)
print("  Segment 5: Closing (3.5s)")

# ─── Step 6: Concatenate all segments ───
print("\n=== Final concatenation ===")
concat_list = f"{RENDERS}/concat.txt"
with open(concat_list, 'w') as f:
    for seg in ['seg1-title.mp4', 'seg2-gameplay.mp4', 'seg3-levels.mp4', 'seg4-features.mp4', 'seg5-close.mp4']:
        f.write(f"file '{RENDERS}/{seg}'\n")

subprocess.run([
    'ffmpeg', '-y',
    '-f', 'concat', '-safe', '0', '-i', concat_list,
    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
    '-c:a', 'aac', '-b:a', '128k',
    '-movflags', '+faststart',
    f'{RENDERS}/arrow-puzzle-showcase.mp4'
], capture_output=True)

# Verify
probe = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration,size', '-of', 'json',
     f'{RENDERS}/arrow-puzzle-showcase.mp4'],
    capture_output=True, text=True
)
info = json.loads(probe.stdout)['format']
dur = float(info['duration'])
size_mb = int(info['size']) / (1024*1024)

print(f"\n{'='*40}")
print(f"  FINAL VIDEO: arrow-puzzle-showcase.mp4")
print(f"  Duration: {dur:.1f}s")
print(f"  Size: {size_mb:.1f} MB")
print(f"  Path: {RENDERS}/arrow-puzzle-showcase.mp4")
print(f"{'='*40}")
