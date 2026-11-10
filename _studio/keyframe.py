# -*- coding: utf-8 -*-
"""키프레임 정렬 — 보간용 그림을 같은 자리에 세운다.

AI 로 뽑으면 장마다 캐릭터 크기와 위치가 조금씩 다르다.
그대로 이어 붙이면 사이를 채울 때 캐릭터가 커졌다 작아졌다 출렁인다.

그래서 내보내기 전에 두 가지를 맞춘다.
  · 크기  — 몸통(노란 덩어리) 높이를 기준으로 정규화
  · 위치  — 발끝을 같은 바닥선에, 몸통 중심을 같은 가로 위치에

'몸통 높이'를 기준으로 삼는 이유: 전체 윤곽은 아기노티가 옆에 붙거나
팔이 뻗으면 같이 커져서 기준이 못 된다. 큰 노티의 노란 몸통만 잰다.
"""
import colorsys
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.dirname(HERE)
MADE = os.path.join(DASH, '_noti_made')

W, H = 1080, 1920
BASELINE = 1270          # 발끝이 놓일 높이
# 1570 이었는데 300 올렸다. 릴스는 화면 아래 420px 쯤을 계정명·캡션·버튼이
# 덮어서, 발끝이 1570 이면 다리가 그 UI 뒤로 들어간다. 안전 영역은 위 130 ~ 아래 1500.
BODY_H = 700             # 큰 노티 몸통이 이 높이가 되도록 맞춘다
# 바닥선을 올리고 나니 아래가 휑해 캐릭터가 작아 보였다. 안전 영역(130~1500)을
# 채우도록 620 에서 키웠다. 더 키우면 머리가 효과음 자리를 침범한다.
BG = (255, 250, 240)     # 크림색
TOP_SAFE = 130           # 이 위로는 릴스 상단 UI·제목 띠가 덮는다
FIT_H = BASELINE - TOP_SAFE      # 그림 전체가 이 높이 안에 들어와야 안 잘린다


def _solid(im, thr=40):
    return im.getchannel('A').point(lambda a: 255 if a > thr else 0)


def body_box(im):
    """큰 노티의 노란 몸통만 찾는다.

    먼저 '가장 넓은 세로 띠'를 잡아 큰 노티의 x 범위를 정하고,
    그 띠 안에서만 높이를 잰다. 이렇게 하지 않으면 옆에 앉은 아기노티까지
    범위에 들어와 높이가 부풀고, 그만큼 캐릭터가 작게 축소된다
    (2026-11-05 '발 내딛음' 장면이 혼자 작게 나온 원인).
    """
    step = 4
    sm = im.convert('RGBA').resize((im.width // step, im.height // step), Image.NEAREST)
    px = sm.load()
    cols = [0] * sm.width
    mask = [[False] * sm.width for _ in range(sm.height)]
    for y in range(sm.height):
        for x in range(sm.width):
            r, g, b, a = px[x, y]
            if a < 200:
                continue
            h, sat, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if 0.07 <= h <= 0.14 and sat >= 0.45 and v >= 0.75:
                cols[x] += 1
                mask[y][x] = True
    if not any(cols):
        return None

    # 가장 두꺼운 열에서 좌우로 번져나가며 큰 노티의 띠를 잡는다
    peak = max(cols)
    c = cols.index(peak)
    lo = hi = c
    while lo > 0 and cols[lo - 1] >= peak * 0.45:
        lo -= 1
    while hi < sm.width - 1 and cols[hi + 1] >= peak * 0.45:
        hi += 1

    # 띠 안에서 노란 행을 찾되, '가장 긴 연속 덩어리' 만 쓴다.
    # min~max 로 재면 멀리 떨어진 노란 점 하나에 높이가 부푼다.
    # (c1_dish_e: 몸통 464 + 바닥의 16px 점 → 720 으로 뛰었다. 그만큼 덜 확대돼
    #  같은 묶음의 c3 와 캐릭터 크기가 어긋났다.)
    rows = [sum(mask[y][lo:hi + 1]) for y in range(sm.height)]
    nz = [y for y, v in enumerate(rows) if v]
    if not nz:
        return None
    runs, s0 = [], nz[0]
    for a, b in zip(nz, nz[1:]):
        if b - a > 1:
            runs.append((s0, a))
            s0 = b
    runs.append((s0, nz[-1]))
    y0, y1 = max(runs, key=lambda r: r[1] - r[0])
    return (lo * step, y0 * step, (hi + 1) * step, (y1 + 1) * step)


def place(src, out, flip=False):
    """한 장을 1080×1920 크림 배경 위에 규격대로 올린다."""
    im = Image.open(src).convert('RGBA')
    box = _solid(im).getbbox()
    if box:
        im = im.crop(box)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)

    bb = body_box(im)
    scale = BODY_H / (bb[3] - bb[1]) if bb else 1.0
    scale = max(0.2, min(3.0, scale))
    im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))),
                   Image.LANCZOS)
    bb = body_box(im)

    canvas = Image.new('RGB', (W, H), BG)
    # 가로: 몸통 중심을 화면 가운데로 / 세로: 그림 아래끝을 바닥선에
    cx = ((bb[0] + bb[2]) // 2) if bb else im.width // 2
    x = W // 2 - cx
    y = BASELINE - im.height
    canvas.paste(im, (x, y), im)
    canvas.save(out, quality=95)
    return out


SEQ = ['kf1_sit', 'kf2_stand', 'kf3_step', 'kf4_grab', 'kf5_look']

if __name__ == '__main__':
    dst = os.path.join(HERE, 'for_video')
    os.makedirs(dst, exist_ok=True)
    for i, n in enumerate(SEQ, 1):
        p = os.path.join(MADE, n + '.png')
        if not os.path.exists(p):
            print('  없음:', n)
            continue
        # 뒤집지 않는다. 뒤집으면 아기노티가 반대쪽으로 가서 흐름이 더 끊긴다.
        out = place(p, os.path.join(dst, f'kf_{i}_{n[4:]}.jpg'))
        print('  ', os.path.basename(out))
    print('→', dst)
