# -*- coding: utf-8 -*-
"""육아 공감툰 엔진 — 릴스용 세로 컷 (1080x1920).

게시물은 정보, 릴스는 공감.
장면마다 노티(엄마)와 작은 노티(아기)를 세워두고 말풍선을 얹는다.

배경·소품은 전부 직접 그린다. 남의 그림은 쓰지 않는다.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import noti_studio as ns

FD = r'C:\Users\OA\claude-test\폰트'
HEAVY = os.path.join(FD, 'NanumSquareNeo-eHv.ttf')
BOLD = os.path.join(FD, 'NanumSquareNeo-cBd.ttf')
REG = os.path.join(FD, 'NanumSquareNeo-bRg.ttf')

W, H = 1080, 1920
INK = (44, 38, 32)
SUB = (128, 118, 106)
WHITE = (255, 255, 255)

ROOM = {
    'wall':  (250, 240, 226),
    'floor': (226, 206, 182),
    'line':  (206, 184, 158),
    'door':  (238, 222, 200),
    'night': (58, 62, 92),
    'nfloor': (44, 48, 74),
}


def f(p, s):
    return ImageFont.truetype(p, s)


def room(night=False):
    """방 한 칸 — 벽과 바닥만. 배경이 시끄러우면 캐릭터가 안 보인다."""
    wall = ROOM['night'] if night else ROOM['wall']
    floor = ROOM['nfloor'] if night else ROOM['floor']
    im = Image.new('RGB', (W, H), wall)
    d = ImageDraw.Draw(im)
    fy = int(H * 0.74)
    d.rectangle((0, fy, W, H), fill=floor)
    d.line((0, fy, W, fy), fill=ROOM['line'] if not night else (70, 74, 106), width=4)
    return im, d


def doorway(d, cx, top=0.20, bot=0.76, w=0.34, open_=True):
    """문틀 — 열린 화장실 문"""
    x0, x1 = int(W * (cx - w / 2)), int(W * (cx + w / 2))
    y0, y1 = int(H * top), int(H * bot)
    d.rectangle((x0, y0, x1, y1), fill=(214, 196, 172))
    d.rectangle((x0 + 18, y0 + 18, x1 - 18, y1), fill=(196, 176, 150))
    if open_:
        d.polygon([(x1, y0), (x1 + 90, y0 + 40), (x1 + 90, y1 - 20), (x1, y1)],
                  fill=ROOM['door'])
        d.ellipse((x1 + 22, (y0 + y1) // 2 - 12, x1 + 46, (y0 + y1) // 2 + 12),
                  fill=(180, 158, 130))
    d.rectangle((x0 - 12, y0 - 12, x1 + 12, y0 + 12), fill=(226, 208, 184))


def bed(d, cx=0.5, y=0.60, w=0.72):
    x0, x1 = int(W * (cx - w / 2)), int(W * (cx + w / 2))
    y0 = int(H * y)
    d.rounded_rectangle((x0, y0, x1, y0 + 300), radius=34, fill=(236, 226, 212))
    d.rounded_rectangle((x0, y0 - 90, x0 + 210, y0 + 40), radius=28, fill=(248, 242, 232))
    d.rounded_rectangle((x0 + 40, y0 + 90, x1 - 30, y0 + 300), radius=26, fill=(198, 214, 232))


def bubble(d, x, y, lines, size=46, tail='left', pad=34, fill=WHITE, ink=INK, max_w=None):
    """말풍선. 글자 폭을 재서 크기를 맞춘다."""
    fnt = f(BOLD, size)
    ws = [d.textlength(t, font=fnt) for t in lines]
    bw = max(ws) + pad * 2
    lh = size + 16
    bh = lh * len(lines) + pad * 1.4
    if max_w and bw > max_w:
        bw = max_w
    x0, y0 = x - bw / 2, y
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=bh * 0.32, fill=fill)
    ty = y0 + pad * 0.7
    for t, tw in zip(lines, ws):
        d.text((x0 + (bw - tw) / 2, ty), t, font=fnt, fill=ink)
        ty += lh
    tx = x0 + bw * (0.28 if tail == 'left' else 0.72)
    d.polygon([(tx - 26, y0 + bh - 4), (tx + 26, y0 + bh - 4), (tx - 6, y0 + bh + 44)], fill=fill)
    return y0 + bh + 50


def caption(d, y, lines, size=52, color=INK, font=BOLD):
    fnt = f(font, size)
    for t in lines:
        tw = d.textlength(t, font=fnt)
        d.text(((W - tw) / 2, y), t, font=fnt, fill=color)
        y += size + 18
    return y


def brand(d, night=False):
    fnt = f(BOLD, 30)
    t = '보아르 아가노트'
    tw = d.textlength(t, font=fnt)
    d.text(((W - tw) / 2, 62), t, font=fnt,
           fill=(146, 158, 196) if night else (196, 176, 152))


def put(im, g, cx, bottom):
    im.paste(g, (int(cx - g.width / 2), int(bottom - g.height)), g)


def mom(h=560, poseName='hello', flip=False):
    return ns.pose(poseName, h, flip)


def baby(h=300, poseName='love', flip=False):
    """작은 노티 = 아기. 같은 캐릭터를 작게 써서 계정 톤을 안 깬다."""
    return ns.pose(poseName, h, flip)


def cling(im, mom_g, baby_g, cx=0.5, base=0.90, off=0.16):
    """아기가 엄마 다리에 붙어 있는 배치"""
    bx = int(W * cx)
    by = int(H * base)
    put(im, mom_g, bx, by)
    put(im, baby_g, bx + int(mom_g.width * off), by)


def sweatmark(im, x, y, h=70):
    g = ns.sweat(h)
    im.paste(g, (int(x), int(y)), g)


def zzzmark(im, x, y, h=140):
    g = ns.zzz(h, (170, 178, 214))
    im.paste(g, (int(x), int(y)), g)
