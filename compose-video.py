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

PIPER_MODEL = "/app/models/en_US-lessac-medium.onnx"

def run(cmd, desc=""):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if r.returncode != 0 and desc:
        print(f"  WARN ({desc}): {r.stderr[:200]}")
    return r

def probe_dur(path):
    r = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'json', path],
        capture_output=True, text=True
    )
    return float(json.loads(r.stdout)['format']['duration'])

# ─── Step 1: Generate narration with Piper TTS ───
narration = [
    ("intro", "Arrow Puzzle. Tap arrows to escape them off the board."),
    ("gameplay", "Find the clear path. Tap, and watch them fly."),
    ("progress", "Over two hundred hand crafted levels across six tiers of increasing challenge."),
    ("cta", "Free, offline, and works on any device. Try it today."),
]

print("=== Generating narration ===")
for name, text in narration:
    out = f"{ASSETS}/audio/{name}.wav"
    run(f'echo "{text}" | piper --model {PIPER_MODEL} --output_file {out}', name)
    if os.path.exists(out) and os.path.getsize(out) > 0:
        print(f"  {name}: {probe_dur(out):.2f}s")
    else:
        print(f"  {name}: FAILED - creating silence")
        run(f'ffmpeg -y -f lavfi -i anullsrc=r=22050:cl=mono -t 3 {out}')

# ─── Step 2: Convert gameplay webm to mp4 ───
print("\n=== Converting gameplay video ===")
run(['ffmpeg', '-y', '-i', f'{ASSETS}/video/gameplay-raw.webm',
     '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-vf', 'fps=30',
     '-pix_fmt', 'yuv420p', f'{ASSETS}/video/gameplay.mp4'])
gameplay_dur = probe_dur(f'{ASSETS}/video/gameplay.mp4')
print(f"  Duration: {gameplay_dur:.1f}s")

# ─── Step 3: Create text overlay images ───
print("\n=== Creating overlay cards ===")

# Title card
run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=0x06070F:s=780x1688:d=1',
     '-vf', (
         "drawtext=text='Arrow':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
         "fontsize=120:fontcolor=0x7B6FFF:x=(w-text_w)/2:y=h/2-180,"
         "drawtext=text='Puzzle':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
         "fontsize=120:fontcolor=0x54C5FF:x=(w-text_w)/2:y=h/2-40,"
         "drawtext=text='Tap Away Game':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
         "fontsize=48:fontcolor=0x585A78:x=(w-text_w)/2:y=h/2+120"
     ), '-frames:v', '1', f'{ASSETS}/images/title-card.png'])
print("  Title card")

# Features card
run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=0x06070F:s=780x1688:d=1',
     '-vf', (
         "drawtext=text='220+ Levels':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
         "fontsize=68:fontcolor=0x7B6FFF:x=(w-text_w)/2:y=h/2-260,"
         "drawtext=text='6 Difficulty Tiers':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
         "fontsize=68:fontcolor=0x54C5FF:x=(w-text_w)/2:y=h/2-120,"
         "drawtext=text='Daily Challenges':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
         "fontsize=68:fontcolor=0x4DDBA6:x=(w-text_w)/2:y=h/2+20,"
         "drawtext=text='Works Offline':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
         "fontsize=68:fontcolor=0xFFD060:x=(w-text_w)/2:y=h/2+160,"
         "drawtext=text='100%% Free':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
         "fontsize=68:fontcolor=0xFF7A5C:x=(w-text_w)/2:y=h/2+300"
     ), '-frames:v', '1', f'{ASSETS}/images/features-card.png'])
print("  Features card")

# CTA card
run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=0x06070F:s=780x1688:d=1',
     '-vf', (
         "drawtext=text='Play Now':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
         "fontsize=100:fontcolor=0x7B6FFF:x=(w-text_w)/2:y=h/2-60,"
         "drawtext=text='arrow-puzzle.app':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
         "fontsize=40:fontcolor=0x585A78:x=(w-text_w)/2:y=h/2+80"
     ), '-frames:v', '1', f'{ASSETS}/images/cta-card.png'])
print("  CTA card")

# ─── Step 4: Build segments with uniform audio ───
# All segments: 780x1688, 30fps, with audio track (even if silent)
print("\n=== Building segments ===")

def make_segment(name, video_input, audio_input, duration, vfilter="", is_image=False):
    """Create a segment with consistent format."""
    cmd = ['ffmpeg', '-y']
    if is_image:
        cmd += ['-loop', '1']
    cmd += ['-i', video_input, '-i', audio_input]

    vf = f'scale=780:1688:force_original_aspect_ratio=decrease,pad=780:1688:(ow-iw)/2:(oh-ih)/2:color=0x06070F,fps=30'
    if vfilter:
        vf += f',{vfilter}'

    cmd += [
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-ac', '1',
        '-t', str(duration),
        '-vf', vf,
        '-pix_fmt', 'yuv420p',
        f'{RENDERS}/{name}.mp4'
    ]
    run(cmd, name)
    if os.path.exists(f'{RENDERS}/{name}.mp4'):
        d = probe_dur(f'{RENDERS}/{name}.mp4')
        print(f"  {name}: {d:.1f}s")
    else:
        print(f"  {name}: FAILED")

# Seg1: Title card (4s)
make_segment('seg1', f'{ASSETS}/images/title-card.png', f'{ASSETS}/audio/intro.wav',
             4.5, 'fade=in:0:15,fade=out:st=3.8:d=0.7', is_image=True)

# Seg2: Gameplay video (13s) — speed up to compress gameplay into ~13s
speed = gameplay_dur / 13.0
pts = 1.0 / speed
make_segment('seg2', f'{ASSETS}/video/gameplay.mp4', f'{ASSETS}/audio/gameplay.wav',
             13, f'setpts={pts:.4f}*PTS,fade=in:0:10,fade=out:st=12.3:d=0.7')

# Seg3: Level select + features narration (5s)
make_segment('seg3', f'{ASSETS}/images/11-levels-screen.png', f'{ASSETS}/audio/progress.wav',
             5.5, 'fade=in:0:10,fade=out:st=4.8:d=0.7', is_image=True)

# Seg4: Features card (4.5s)
make_segment('seg4', f'{ASSETS}/images/features-card.png', f'{ASSETS}/audio/progress.wav',
             4.5, 'fade=in:0:10,fade=out:st=3.8:d=0.7', is_image=True)

# Seg5: CTA / closing (3s)
make_segment('seg5', f'{ASSETS}/images/cta-card.png', f'{ASSETS}/audio/cta.wav',
             3, 'fade=in:0:10,fade=out:st=2.3:d=0.7', is_image=True)

# ─── Step 5: Concatenate ───
print("\n=== Final concatenation ===")
concat_file = f"{RENDERS}/concat.txt"
with open(concat_file, 'w') as f:
    for seg in ['seg1', 'seg2', 'seg3', 'seg4', 'seg5']:
        path = f"{RENDERS}/{seg}.mp4"
        if os.path.exists(path):
            f.write(f"file '{path}'\n")

result = run(['ffmpeg', '-y',
    '-f', 'concat', '-safe', '0', '-i', concat_file,
    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
    '-c:a', 'aac', '-b:a', '128k',
    '-movflags', '+faststart',
    f'{RENDERS}/arrow-puzzle-showcase.mp4'], 'concat')

final = f'{RENDERS}/arrow-puzzle-showcase.mp4'
if os.path.exists(final):
    dur = probe_dur(final)
    size = os.path.getsize(final) / (1024*1024)
    print(f"\n{'='*40}")
    print(f"  FINAL: arrow-puzzle-showcase.mp4")
    print(f"  Duration: {dur:.1f}s")
    print(f"  Size: {size:.1f} MB")
    print(f"  Path: {final}")
    print(f"{'='*40}")
else:
    print(f"\nFAILED: {result.stderr[:500] if result else 'unknown'}")
