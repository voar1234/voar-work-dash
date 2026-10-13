# -*- coding: utf-8 -*-
"""릴스 — 24개월 엄마껌딱지.

공감 릴스라 정보 카드와 레이아웃이 다르다.
  · 노티를 크게 세운다 (스치듯 보는 매체라 작으면 안 읽힌다)
  · 글은 짧게, 위쪽에 한두 줄
  · 상단 250 · 하단 430 은 인스타 UI 가 덮으므로 비워둔다

영상은 ffmpeg 로 느린 줌 + 교차 페이드. 정지 이미지를 그냥 이어붙이면
슬라이드쇼로 보여서 릴스에서 안 먹힌다.

나중에 Veo 가 열리면 각 컷의 정지 그림을 움직이는 클립으로 갈아끼우면 된다.
자막과 구성은 그대로 쓴다.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import card_v3
card_v3.H = 1920                      # 세로로
from card_v3 import (BG, INK, SUB, ACC, REG, BOLD, HEAVY, f, canvas, paste)
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.dirname(HERE)
MADE = os.path.join(DASH, '_noti_made')
W, H = 1080, 1920
SAFE_TOP, SAFE_BOT = 250, 430
FPS, FADE = 30, 0.35

# (자막 줄들, 노티 파일, 강조색, 컷 길이)
CUTS = [
    (['18개월이', '끝인 줄 알았어요'],      'tired_big',  'lilac', 3.0),
    (['24개월,', '더 심해졌습니다'],        'cling_leg',  'coral', 2.6),
    (['화장실 문을', '못 닫아요'],          'door_wait',  'sky',   2.6),
    (['물 한 잔 뜨러 가는', '세 걸음도'],    'cling_leg',  'mint',  2.6),
    (['아빠가 안으면', '울어요'],           'door_wait',  'gold',  2.6),
    (['재채기만 해도', '쳐다봅니다'],       'tired_big',  'rose',  2.6),
    (['엄마랑 내가', '다른 사람인 걸',
      '이제 완전히 알아서예요'],            'hug_baby',   'mint',  3.6),
    (['애착이 잘 된 아이일수록', '더 그렇대요',
      '', '세 돌 즈음 옅어집니다'],         'hug_baby',   'sage',  4.2),
]


def noti(name, h):
    """만들어둔 노티를 불러 높이를 맞춘다 (반투명 점은 빼고 자른다)."""
    im = Image.open(os.path.join(MADE, name + '.png')).convert('RGBA')
    box = im.getchannel('A').point(lambda a: 255 if a > 40 else 0).getbbox()
    if box:
        im = im.crop(box)
    a = im.getchannel('A').point(lambda v: 0 if v < 16 else v)
    im.putalpha(a)
    s = h / im.height
    return im.resize((max(1, int(im.width * s)), h), Image.LANCZOS)


def center(d, y, text, fnt, fill):
    d.text(((W - d.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=fill)


def cut(lines, pose, tone, out):
    im, d = canvas(tone, seed=abs(hash(pose + tone)) % 97)
    acc = ACC[tone][0]

    # 글 — 마지막 줄만 강조색, 나머지는 먹색
    y = SAFE_TOP + 40
    big = f(HEAVY, 74)
    small = f(BOLD, 52)
    real = [t for t in lines if t]
    for i, t in enumerate(lines):
        if not t:
            y += 26
            continue
        last = (t == real[-1])
        fnt = big if len(real) <= 2 else small
        center(d, y, t, fnt, acc if last and len(real) <= 2 else INK)
        y += (fnt.size + 16)

    g = noti(pose, 820)
    paste(im, g, W / 2, H - SAFE_BOT - 40)

    fnt = f(REG, 30)
    center(d, H - SAFE_BOT + 40, '@voar_baby', fnt, (198, 186, 170))
    im.save(out, quality=95)
    return out


def build(tag='clingy24'):
    files, secs = [], []
    for i, (lines, pose, tone, sec) in enumerate(CUTS, 1):
        p = os.path.join(HERE, f'{tag}_{i}.jpg')
        cut(lines, pose, tone, p)
        files.append(p)
        secs.append(sec)
    return files, secs


def to_mp4(files, secs, out):
    """느린 줌 + 교차 페이드. 무음이라도 오디오 트랙은 넣는다(인스타가 싫어함).

    zoompan 은 쓰지 않는다 — 입력 프레임마다 d 프레임을 뱉어 길이가 불어난다.
    scale 의 eval=frame 으로 매 프레임 키운 뒤 가운데를 도로 잘라낸다.
    """
    ins, fl = [], []
    for i, p in enumerate(files):
        ins += ['-loop', '1', '-framerate', str(FPS), '-t', f'{secs[i]:.2f}', '-i', p]
        D, Z = secs[i], 0.05
        sc = f'(1+{Z}*t/{D})' if i % 2 == 0 else f'({1 + Z}-{Z}*t/{D})'
        fl.append(f"[{i}:v]scale=w='floor({W}*{sc}/2)*2':h='floor({H}*{sc}/2)*2':"
                  f"eval=frame:flags=bicubic,crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/2',"
                  f"fps={FPS},setsar=1[v{i}]")
    cur, acc = 'v0', secs[0]
    for i in range(1, len(files)):
        nxt = f'x{i}'
        fl.append(f"[{cur}][v{i}]xfade=transition=fade:duration={FADE}:"
                  f"offset={acc - FADE:.2f}[{nxt}]")
        acc += secs[i] - FADE
        cur = nxt
    cmd = (['ffmpeg', '-y'] + ins +
           ['-f', 'lavfi', '-t', f'{acc + 4:.2f}', '-i', 'anullsrc=r=44100:cl=stereo',
            '-filter_complex', ';'.join(fl), '-map', f'[{cur}]', '-map', f'{len(files)}:a',
            '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
            '-r', str(FPS), '-b:v', '6M', '-c:a', 'aac', '-b:a', '96k',
            '-shortest', '-movflags', '+faststart', out])
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        raise SystemExit(r.stderr.decode('utf-8', 'replace')[-2000:])
    return out, acc


if __name__ == '__main__':
    files, secs = build()
    out, dur = to_mp4(files, secs, os.path.join(HERE, 'clingy24.mp4'))
    print(f'{len(files)}컷 · 예상 {dur:.1f}초 · {os.path.getsize(out):,}바이트')
