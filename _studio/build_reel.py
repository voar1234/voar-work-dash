# -*- coding: utf-8 -*-
"""컷 → 릴스 영상.

각 컷을 조금씩 확대하며(느린 줌) 보여주고 짧게 교차 페이드한다.
정지 이미지를 그냥 이어붙이면 슬라이드쇼처럼 보여서 릴스에서 안 먹힌다.
소리는 무음(요청) — 다만 인스타가 오디오 트랙 없는 영상을 싫어해서
무음 AAC 트랙을 넣는다.
"""
import io, os, subprocess, sys
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

W, H, FPS = 1080, 1920, 30
CUTS = [
    ('rl1.jpg', 3.2),
    ('rl2.jpg', 2.8),
    ('rl3.jpg', 2.8),
    ('rl4.jpg', 2.8),
    ('rl5.jpg', 3.0),
    ('rl6.jpg', 3.6),
    ('rl7.jpg', 3.4),
    ('rl8.jpg', 3.6),
]
FADE = 0.35
OUT_DIR = 'reel_frames'


def ken_burns(src, sec, idx):
    """느린 줌 — 홀수 컷은 당기고 짝수 컷은 민다"""
    im = Image.open(src).convert('RGB')
    n = int(sec * FPS)
    zin = idx % 2 == 0
    for i in range(n):
        t = i / max(1, n - 1)
        z = 1.0 + 0.045 * (t if zin else (1 - t))
        cw, ch = int(W / z), int(H / z)
        x, y = (W - cw) // 2, (H - ch) // 2
        fr = im.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
        fr.save(os.path.join(OUT_DIR, f'{idx:02d}_{i:04d}.jpg'), quality=92)
    return n


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for fn in os.listdir(OUT_DIR):
        os.remove(os.path.join(OUT_DIR, fn))

    total = 0
    for i, (src, sec) in enumerate(CUTS):
        total += ken_burns(src, sec, i)
    dur = total / FPS
    print(f'프레임 {total}장 · {dur:.1f}초')

    # 컷 사이 교차 페이드는 xfade 로 이어붙인다
    parts = []
    for i, (src, sec) in enumerate(CUTS):
        p = f'part{i}.mp4'
        subprocess.run([
            'ffmpeg', '-y', '-loglevel', 'error',
            '-framerate', str(FPS),
            '-i', os.path.join(OUT_DIR, f'{i:02d}_%04d.jpg'),   # 이 빌드는 glob 미지원
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', p], check=True)
        parts.append((p, sec))

    cur = parts[0][0]
    acc = parts[0][1]
    for i, (p, sec) in enumerate(parts[1:], 1):
        nxt = f'mix{i}.mp4'
        off = max(0.1, acc - FADE)
        subprocess.run([
            'ffmpeg', '-y', '-loglevel', 'error', '-i', cur, '-i', p,
            '-filter_complex',
            f'[0][1]xfade=transition=fade:duration={FADE}:offset={off:.2f},format=yuv420p',
            '-c:v', 'libx264', '-crf', '18', nxt], check=True)
        cur = nxt
        acc = acc - FADE + sec

    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error', '-i', cur,
        '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20',
        '-profile:v', 'high', '-level', '4.0', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
        'reel_clingy.mp4'], check=True)

    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                          'format=duration,size:stream=width,height,codec_name',
                          '-of', 'default=nw=1', 'reel_clingy.mp4'],
                         capture_output=True, text=True)
    print(out.stdout)
    for f in os.listdir('.'):
        if f.startswith(('part', 'mix')) and f.endswith('.mp4'):
            os.remove(f)


if __name__ == '__main__':
    main()
