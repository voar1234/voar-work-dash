# -*- coding: utf-8 -*-
"""픽토그램 — PIL 도형으로 직접 그린다.

AI 이미지나 외부 아이콘 폰트를 쓰지 않는 이유:
  · 저작권이 깨끗해야 함 (전부 우리가 그린 도형)
  · 색을 팔레트에 맞춰 자유롭게 바꿀 수 있어야 함

규약: 몸통은 c(진한 색), 파낸 부분·디테일은 c2(흰색).
     56px 정도로 줄여도 형태가 남도록 디테일은 최소로 한다.
"""


def _r(d, box, r, fill):
    d.rounded_rectangle(box, radius=max(1, r), fill=fill)


def money(d, cx, cy, s, c, c2):
    """지폐"""
    w, h = s*0.86, s*0.56
    _r(d, (cx-w/2, cy-h/2, cx+w/2, cy+h/2), s*0.10, c)
    r = s*0.16
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=c2)
    d.rectangle((cx-w/2+s*0.07, cy-s*0.04, cx-w/2+s*0.13, cy+s*0.04), fill=c2)
    d.rectangle((cx+w/2-s*0.13, cy-s*0.04, cx+w/2-s*0.07, cy+s*0.04), fill=c2)


def calendar(d, cx, cy, s, c, c2):
    w, h = s*0.76, s*0.74
    _r(d, (cx-w/2, cy-h/2, cx+w/2, cy+h/2), s*0.11, c)
    d.rectangle((cx-w/2, cy-h/2+s*0.22, cx+w/2, cy-h/2+s*0.27), fill=c2)
    for i in range(2):
        for j in range(3):
            x = cx-w/2+s*0.14+j*s*0.22
            y = cy-h/2+s*0.36+i*s*0.19
            d.ellipse((x, y, x+s*0.10, y+s*0.10), fill=c2)


def pin(d, cx, cy, s, c, c2):
    r = s*0.30
    top = cy - s*0.20
    d.ellipse((cx-r, top-r, cx+r, top+r), fill=c)
    d.polygon([(cx-r*0.70, top+r*0.60), (cx+r*0.70, top+r*0.60), (cx, cy+s*0.42)], fill=c)
    rr = r*0.40
    d.ellipse((cx-rr, top-rr, cx+rr, top+rr), fill=c2)


def clock(d, cx, cy, s, c, c2):
    r = s*0.42
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=c)
    w = max(3, int(s*0.075))
    d.line((cx, cy, cx, cy-r*0.56), fill=c2, width=w)
    d.line((cx, cy, cx+r*0.42, cy+r*0.14), fill=c2, width=w)


def card(d, cx, cy, s, c, c2):
    """카드"""
    w, h = s*0.86, s*0.58
    _r(d, (cx-w/2, cy-h/2, cx+w/2, cy+h/2), s*0.10, c)
    d.rectangle((cx-w/2, cy-h/2+s*0.11, cx+w/2, cy-h/2+s*0.21), fill=c2)
    _r(d, (cx-w/2+s*0.09, cy+s*0.10, cx-w/2+s*0.34, cy+s*0.19), s*0.04, c2)


def baby(d, cx, cy, s, c, c2):
    """아기 얼굴"""
    r = s*0.40
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=c)
    # 머리카락 한 가닥
    d.line((cx, cy-r*0.98, cx+s*0.10, cy-r*1.30), fill=c, width=max(3, int(s*0.06)))
    e = s*0.055
    d.ellipse((cx-s*0.17-e, cy-s*0.06-e, cx-s*0.17+e, cy-s*0.06+e), fill=c2)
    d.ellipse((cx+s*0.17-e, cy-s*0.06-e, cx+s*0.17+e, cy-s*0.06+e), fill=c2)
    d.arc((cx-s*0.15, cy-s*0.02, cx+s*0.15, cy+s*0.22), 20, 160,
          fill=c2, width=max(3, int(s*0.055)))


def bottle(d, cx, cy, s, c, c2):
    """젖병"""
    w = s*0.44
    _r(d, (cx-w/2, cy-s*0.20, cx+w/2, cy+s*0.42), s*0.11, c)
    _r(d, (cx-w*0.30, cy-s*0.44, cx+w*0.30, cy-s*0.20), s*0.06, c)
    for i in range(2):
        yy = cy - s*0.02 + i*s*0.16
        d.rectangle((cx-w/2+s*0.06, yy, cx-w/2+s*0.17, yy+s*0.04), fill=c2)


def check(d, cx, cy, s, c, c2):
    r = s*0.42
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=c)
    w = max(4, int(s*0.11))
    d.line((cx-r*0.44, cy+r*0.02, cx-r*0.10, cy+r*0.36), fill=c2, width=w)
    d.line((cx-r*0.10, cy+r*0.36, cx+r*0.46, cy-r*0.34), fill=c2, width=w)


def alert(d, cx, cy, s, c, c2):
    r = s*0.44
    d.polygon([(cx, cy-r*1.02), (cx+r*0.96, cy+r*0.62), (cx-r*0.96, cy+r*0.62)], fill=c)
    _r(d, (cx-s*0.045, cy-s*0.18, cx+s*0.045, cy+s*0.10), s*0.045, c2)
    d.ellipse((cx-s*0.05, cy+s*0.16, cx+s*0.05, cy+s*0.26), fill=c2)


def heart(d, cx, cy, s, c, c2):
    r = s*0.25
    d.ellipse((cx-r*1.5, cy-r*1.1, cx-r*0.1, cy+r*0.3), fill=c)
    d.ellipse((cx+r*0.1, cy-r*1.1, cx+r*1.5, cy+r*0.3), fill=c)
    d.polygon([(cx-r*1.44, cy-r*0.22), (cx+r*1.44, cy-r*0.22), (cx, cy+r*1.36)], fill=c)


def gift(d, cx, cy, s, c, c2):
    """선물상자"""
    w, h = s*0.74, s*0.56
    _r(d, (cx-w/2, cy-h/2+s*0.09, cx+w/2, cy+h/2+s*0.09), s*0.08, c)
    _r(d, (cx-w/2-s*0.05, cy-h/2-s*0.03, cx+w/2+s*0.05, cy-h/2+s*0.13), s*0.05, c)
    d.rectangle((cx-s*0.05, cy-h/2-s*0.03, cx+s*0.05, cy+h/2+s*0.09), fill=c2)
    # 리본 고리
    for sx in (-1, 1):
        d.ellipse((cx+sx*s*0.20-s*0.13, cy-h/2-s*0.20,
                   cx+sx*s*0.20+s*0.13, cy-h/2+s*0.02), fill=c)


def house(d, cx, cy, s, c, c2):
    d.polygon([(cx, cy-s*0.42), (cx+s*0.46, cy+s*0.00), (cx-s*0.46, cy+s*0.00)], fill=c)
    _r(d, (cx-s*0.32, cy-s*0.04, cx+s*0.32, cy+s*0.40), s*0.06, c)
    _r(d, (cx-s*0.10, cy+s*0.12, cx+s*0.10, cy+s*0.40), s*0.03, c2)


ICONS = {
    'money': money, 'calendar': calendar, 'pin': pin, 'clock': clock,
    'card': card, 'baby': baby, 'bottle': bottle, 'check': check,
    'alert': alert, 'heart': heart, 'gift': gift, 'house': house,
}


def draw(d, name, cx, cy, size, c, c2):
    fn = ICONS.get(name)
    if fn:
        fn(d, cx, cy, size, c, c2)


def badge(d, cx, cy, r, name, c, light, _unused=None):
    """연한 원 위에 진한 픽토그램"""
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=light)
    draw(d, name, cx, cy, r*1.30, c, (255, 255, 255))


def confetti(d, W, H, colors, seed=0):
    """모서리 장식 — 글자와 겹치지 않는 자리에만 둔다.
    (하단 중앙은 푸터, 우하단은 쪽수가 들어가므로 비운다)"""
    spots = [(0.055, 0.115, 13), (0.945, 0.085, 10), (0.088, 0.905, 11),
             (0.930, 0.930, 9), (0.042, 0.520, 7), (0.960, 0.460, 8),
             (0.150, 0.048, 6), (0.862, 0.760, 6), (0.048, 0.700, 5)]
    for i, (fx, fy, rr) in enumerate(spots):
        c = colors[(i + seed) % len(colors)]
        x, y = W*fx, H*fy
        d.ellipse((x-rr, y-rr, x+rr, y+rr), fill=c)
