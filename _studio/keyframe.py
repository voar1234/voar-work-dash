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
BASELINE = 1570          # 발끝이 놓일 높이
BODY_H = 620             # 큰 노티 몸통이 이 높이가 되도록 맞춘다
BG = (255, 250, 240)     # 크림색


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

    ys = [y for y in range(sm.height) if any(mask[y][lo:hi + 1])]
    if not ys:
        return None
    return (lo * step, min(ys) * step, (hi + 1) * step, (max(ys) + 1) * step)


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
