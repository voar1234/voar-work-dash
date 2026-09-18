# -*- coding: utf-8 -*-
"""보아르 아가노트 카드 v3 — 경쟁 계정 실물을 보고 다시 설계.

바꾼 것 (v2의 문제 → v3)
  · 화면 절반을 덮던 컬러 헤더 삭제 → 크림 단색 배경
  · 좌측정렬 흰 글씨 → 중앙정렬 진한 글씨, 핵심 키워드만 컬러
  · 꽉 찬 레이아웃 → 위아래 여백 크게
  · 구석에 서 있던 노티 → 정보 옆에서 반응하는 작은 크기
  · 상단 중앙에 브랜드 마크 (경쟁 계정 공통)
"""
import os
from PIL import Image, ImageDraw, ImageFont
import picto

FD = r'C:\Users\OA\claude-test\폰트'
HEAVY = os.path.join(FD, 'NanumSquareNeo-eHv.ttf')
BOLD  = os.path.join(FD, 'NanumSquareNeo-cBd.ttf')
REG   = os.path.join(FD, 'NanumSquareNeo-bRg.ttf')
LIGHT = os.path.join(FD, 'NanumSquareNeo-aLt.ttf')

BG    = (253, 251, 246)
INK   = (44, 38, 32)
SUB   = (140, 130, 118)
LINE  = (228, 221, 210)
WHITE = (255, 255, 255)

ACC = {
    'coral': ((240, 106,  78), (255, 233, 226)),
    'mint':  (( 42, 176, 148), (219, 243, 237)),
    'sky':   (( 68, 145, 208), (223, 238, 250)),
    'gold':  ((228, 160,  30), (255, 240, 208)),
    'rose':  ((228, 106, 138), (255, 228, 236)),
    'sage':  ((114, 172,  92), (228, 242, 220)),
    'lilac': ((136, 112, 202), (233, 227, 249)),
}

W, H, M = 1080, 1350, 100
P = 'noti_hi'
def f(p, s): return ImageFont.truetype(p, s)
def noti(name, h):
    im = Image.open(f'{P}/{name}.png').convert('RGBA')
    s = h / im.height
    return im.resize((max(1, int(im.width*s)), h), Image.LANCZOS)

def canvas(acc=None, deco=True, seed=0):
    """크림 바탕에 은은한 색 얼룩 + 모서리 색종이.
    v3 가 단조롭다는 지적을 받아, 정보를 가리지 않는 선에서만 색을 깐다."""
    im = Image.new('RGB', (W, H), BG)
    if deco:
        lay = Image.new('RGB', (W, H), BG)
        ld = ImageDraw.Draw(lay)
        keys = [acc] if acc else []
        keys += [k for k in ['gold', 'mint', 'coral', 'sky', 'lilac'] if k != acc]
        # 큰 원 두 개를 흐리게 깔아 배경에 온기를 준다
        for i, (fx, fy, r) in enumerate([(-0.10, 0.06, 0.42), (1.08, 0.72, 0.46)]):
            ld.ellipse((W*fx-W*r, H*fy-W*r, W*fx+W*r, H*fy+W*r),
                       fill=ACC[keys[i % len(keys)]][1])
        from PIL import ImageFilter
        im = Image.blend(im, lay.filter(ImageFilter.GaussianBlur(70)), 0.55)
    d = ImageDraw.Draw(im)
    if deco:
        pal = [ACC[k][0] for k in ['coral', 'gold', 'mint', 'sky', 'lilac', 'rose']]
        picto.confetti(d, W, H, [tint(c, 0.62) for c in pal], seed)
    return im, d


def tint(c, amt):
    """흰색 쪽으로 amt 만큼 당긴다 (0=원색, 1=흰색)"""
    return tuple(int(v + (255 - v) * amt) for v in c)

def brandmark(d, y=72):
    """상단 중앙 브랜드 — 경쟁 계정들이 공통으로 쓰는 요소"""
    fnt = f(BOLD, 27)
    t = '보아르 아가노트'
    tw = d.textlength(t, font=fnt)
    d.text(((W-tw)/2, y), t, font=fnt, fill=(196, 176, 152))

def center(d, y, text, fnt, fill):
    tw = d.textlength(text, font=fnt)
    d.text(((W-tw)/2, y), text, font=fnt, fill=fill)
    return y + fnt.size + 18

def center_mixed(d, y, parts, size, gap=16):
    """[(글자, 색), ...] 을 한 줄로 가운데 정렬 — 키워드만 색을 넣기 위해"""
    fnt = f(HEAVY, size)
    total = sum(d.textlength(t, font=fnt) for t, _ in parts)
    x = (W - total) / 2
    for t, c in parts:
        d.text((x, y), t, font=fnt, fill=c)
        x += d.textlength(t, font=fnt)
    return y + size + gap

def eyebrow(d, y, text, acc):
    """제목 위 작은 라벨 — 얇은 알약"""
    c, lt = ACC[acc]
    fnt = f(BOLD, 28)
    tw = d.textlength(text, font=fnt)
    x0 = (W - tw - 52) / 2
    d.rounded_rectangle((x0, y, x0+tw+52, y+56), radius=28, fill=lt)
    d.text((x0+26, y+12), text, font=fnt, fill=c)
    return y + 56 + 34

def rule(d, y, w=90, acc='coral'):
    c, _ = ACC[acc]
    d.rounded_rectangle(((W-w)/2, y, (W+w)/2, y+7), radius=4, fill=c)
    return y + 7 + 40

def footer(d, page=None, save_hint=True):
    y = H - 118
    if save_hint:
        fnt = f(BOLD, 28)
        t = '저장해두고 필요할 때 꺼내보세요'
        tw = d.textlength(t, font=fnt)
        d.text(((W-tw)/2, y), t, font=fnt, fill=(186, 172, 154))
        y += 46
    fnt = f(REG, 24)
    t = '@voar_baby'
    tw = d.textlength(t, font=fnt)
    d.text(((W-tw)/2, y), t, font=fnt, fill=(206, 194, 178))
    if page:
        pf = f(REG, 24)
        d.text((W-M-d.textlength(page, font=pf), y), page, font=pf, fill=(212, 200, 184))

def paste(im, g, cx, bottom):
    im.paste(g, (int(cx-g.width/2), int(bottom-g.height)), g)

# ── 정보 블록 ──
def stat_box(d, y, rows, acc='coral', h_row=124):
    """금액·수치 카드. 항목마다 픽토그램 배지를 달고 색을 다르게 준다.

    rows = [(이름, 값, 설명)] 또는 [(이름, 값, 설명, 아이콘, 색키)]
    """
    top = y
    box_h = h_row*len(rows) + 44
    d.rounded_rectangle((M, y, W-M, y+box_h), radius=32, fill=WHITE,
                        outline=LINE, width=2)
    yy = y + 22
    for i, r in enumerate(rows):
        name, val, note = r[0], r[1], r[2]
        ic = r[3] if len(r) > 3 else None
        ak = r[4] if len(r) > 4 else acc
        c, lt = ACC[ak]
        if i:
            d.line((M+40, yy, W-M-40, yy), fill=(242, 237, 229), width=2)
        cy = yy + h_row/2
        tx = M + 42
        if ic:
            picto.badge(d, M+82, cy, 42, ic, c, lt)
            tx = M + 148
        d.text((tx, cy-40), name, font=f(BOLD, 39), fill=INK)
        if note:
            d.text((tx, cy+10), note, font=f(REG, 26), fill=SUB)
        if val.startswith('@'):          # '@check' → 글자 대신 픽토그램
            picto.badge(d, W-M-84, cy, 34, val[1:], c, lt)
        else:
            vf = f(HEAVY, 46)
            vw = d.textlength(val, font=vf)
            d.rounded_rectangle((W-M-62-vw-22, cy-36, W-M-40, cy+36), radius=20, fill=lt)
            d.text((W-M-62-vw, cy-30), val, font=vf, fill=c)
        yy += h_row
    return top + box_h + 36

def icon_row(d, y, items, size=104):
    """하단 아이콘 4개 — 경쟁 계정이 쓰는 요약 띠"""
    n = len(items)
    gap = (W - M*2 - size*n) / (n-1) if n > 1 else 0
    x = M
    for it in items:
        label, acc = it[0], it[1]
        ic = it[2] if len(it) > 2 else 'check'
        c, lt = ACC[acc]
        picto.badge(d, x+size/2, y+size/2, size/2, ic, c, lt)
        fnt = f(BOLD, 25)
        tw = d.textlength(label, font=fnt)
        d.text((x+size/2-tw/2, y+size+16), label, font=fnt, fill=SUB)
        x += size + gap
    return y + size + 60
