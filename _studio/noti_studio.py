# -*- coding: utf-8 -*-
"""노티 변주 스튜디오.

디자인팀이 준 12장은 '재료'다. 그대로 돌려쓰면 계정이 금세 단조로워지므로
여기서 소품·효과를 붙이고 포즈를 조합해 주제마다 다른 노티를 만든다.

원칙
  · 원본 캐릭터의 형태·비율은 건드리지 않는다 (브랜드 일관성)
  · 소품은 전부 직접 그린다 — 클레이 질감을 흉내내려 부드러운 하이라이트를 얹는다
  · 남의 저작물은 일절 쓰지 않는다
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter
import clay

# 임시 폴더에 두면 세션이 바뀔 때 사라진다(두 번 겪음). 영구 폴더에서 읽는다.
SRC = os.environ.get('NOTI_DIR') or os.path.join(
    'C:' + os.sep, 'Users', 'OA', 'claude-test', '온라인영업', '대시보드', '_noti_work')
PAL = {
    'body':   (247, 190, 84),
    'deep':   (214, 150, 52),
    'arm':    (176, 118, 68),
    'sprout': (92, 92, 92),
    'cream':  (255, 246, 228),
    'white':  (255, 255, 255),
    'red':    (226, 74, 62),
    'blue':   (86, 156, 220),
    'mint':   (72, 190, 162),
    'pink':   (244, 150, 168),
    'glass':  (206, 228, 246),
}


def pose(name, h, flip=False):
    im = Image.open(os.path.join(SRC, name + '.png')).convert('RGBA')
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    s = h / im.height
    return im.resize((max(1, int(im.width * s)), h), Image.LANCZOS)


# ─────────── 주문제작 노티 ───────────
# 받은 14장으로는 "분유 든 노티" 같은 걸 만들 수 없었다.
# 원본을 참조로 넣고 새 동작을 만들어 파일로 남긴다.
# 한 번 만든 포즈는 그 파일을 쓰므로 같은 그림에 두 번 돈이 나가지 않는다.
#
# 변형 방지 (담당자 조건: "노티에 변형만 없다면 괜찮다")
#   만들 때마다 원본과 수치로 비교해서, 어긋나면 참조를 늘려 다시 뽑는다.
#   세 번 다 어긋나면 원본 포즈로 대신하고, 다음부터는 다시 만들지 않는다.
#   → 변형된 노티가 게시물에 올라가는 일은 없다.
import colorsys
import shutil

DASH = os.path.dirname(SRC)
GEN = os.environ.get('NOTI_GEN') or os.path.join(DASH, '_noti_made')
REJECT = os.path.join(GEN, '_reject')          # 걸러진 것 — 나중에 판정 기준을 손볼 때 본다

# 원본 4종과 모델 비교(2026-09-18)로 잡은 기준.
#   원본: 노랑 0.41~0.79, 새싹 0.018~0.027, 가로/세로 0.67~0.82
#   걸러야 했던 것: 새싹이 잘린 image-1(0.006), 다리가 잘린 1-mini(여백 0)
CHECK = dict(margin=0.003, sprout=0.012, body=0.35, aspect=(0.45, 1.05))


def _solid_box(im, thr=40):
    """반투명 점은 빼고 캐릭터가 실제로 있는 영역만 잡는다.

    생성본은 캔버스 가장자리까지 거의 안 보이는 점이 깔려 있어서
    getbbox() 를 그대로 쓰면 캔버스를 통째로 잡는다. 그러면 여백째로
    축소돼 카드에서 노티가 실제보다 작게 들어간다.
    """
    return im.getchannel('A').point(lambda a: 255 if a > thr else 0).getbbox()


def inspect(path):
    """원본 노티와 같은 캐릭터로 보이는지 수치로 본다. (통과 여부, 이유, 수치)"""
    im = Image.open(path).convert('RGBA')
    W, H = im.size
    box = _solid_box(im)
    if not box:
        return False, '빈 그림', {}
    x0, y0, x1, y1 = box
    m = dict(margin=min(x0, y0, W - x1, H - y1) / max(W, H),
             aspect=(x1 - x0) / max(1, (y1 - y0)))
    small = im.crop(box)
    small = small.resize((200, max(1, int(200 * small.height / small.width))), Image.NEAREST)
    sw, sh = small.size
    sp = small.load()
    opaque = body = sprout = 0
    for y in range(sh):
        for x in range(sw):
            r, g, b, a = sp[x, y]
            if a < 200:
                continue
            opaque += 1
            hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if 0.07 <= hh <= 0.14 and ss >= 0.45 and vv >= 0.75:
                body += 1                      # 몸통 노랑
            if y < sh * 0.16 and vv < 0.5 and ss < 0.25:
                sprout += 1                    # 머리 위 새싹
    m['body'] = body / max(1, opaque)
    m['sprout'] = sprout / max(1, opaque)

    if m['margin'] < CHECK['margin']:
        return False, '가장자리에 닿음 (어딘가 잘림)', m
    if m['sprout'] < CHECK['sprout']:
        return False, '머리 위 새싹이 없거나 잘림', m
    if m['body'] < CHECK['body']:
        return False, '몸통 색이 원본과 다름', m
    lo, hi = CHECK['aspect']
    if not lo <= m['aspect'] <= hi:
        return False, '몸 비율이 원본과 다름', m
    return True, '통과', m


def _load(path, h, flip):
    im = Image.open(path).convert('RGBA')
    box = _solid_box(im)
    if box:
        im = im.crop(box)
    # 잘라낸 안쪽에 남은 희미한 점도 지운다 (카드 위에서 뿌옇게 보이지 않게)
    a = im.getchannel('A').point(lambda v: 0 if v < 16 else v)
    im.putalpha(a)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    s = h / im.height
    return im.resize((max(1, int(im.width * s)), h), Image.LANCZOS)


def made(name, prompt, base='hello', h=380, flip=False, log=print):
    """주문제작 노티. name 으로 캐시를 찾고, 없으면 만들어 저장한다.

    name   저장 이름 (bottle_hug, carseat_sit …)
    prompt 어떤 동작·소품인지
    base   참조할 원본 포즈 (hello, curious, worry, sleepy, love …)
    """
    path = os.path.join(GEN, name + '.png')
    fail = os.path.join(GEN, name + '.fail')
    if os.path.exists(path):
        return _load(path, h, flip)
    if os.path.exists(fail):                   # 전에 세 번 다 어긋났던 포즈 — 다시 돈 쓰지 않는다
        return pose(base, h, flip)

    os.makedirs(GEN, exist_ok=True)
    if DASH not in sys.path:
        sys.path.insert(0, DASH)
    import _gpt_img

    # 어긋날수록 보여주는 원본을 늘린다 (정면 → +측면 → +3/4)
    extra = [[],
             [os.path.join(SRC, 'side.png')],
             [os.path.join(SRC, 'side.png'), os.path.join(SRC, 'q34r.png')]]
    for i, refs in enumerate(extra, 1):
        refs = [r for r in refs if os.path.exists(r) and not r.endswith(base + '.png')]
        tmp = os.path.join(GEN, f'{name}.try{i}.png')
        try:
            _gpt_img.noti(base, prompt, out_path=tmp, refs=refs)
        except SystemExit as e:
            log(f'  노티 {name} {i}차 생성 실패: {e}')
            continue
        ok, why, m = inspect(tmp)
        if ok:
            os.replace(tmp, path)
            log(f'  노티 {name} — {i}차에 통과')
            return _load(path, h, flip)
        os.makedirs(REJECT, exist_ok=True)
        shutil.move(tmp, os.path.join(REJECT, f'{name}.try{i}.png'))
        log(f'  노티 {name} {i}차 걸러짐 — {why}')

    open(fail, 'w', encoding='utf-8').write(prompt)
    log(f'  노티 {name} — 세 번 다 어긋나 원본({base})으로 대신합니다')
    return pose(base, h, flip)


# ─────────── 클레이 질감 ───────────
def _clay(size):
    return Image.new('RGBA', size, (0, 0, 0, 0))


def shade(layer, strength=1.0, dark=None):
    """평면 도형 → 점토 덩어리.

    예전에는 위/아래 그라데이션만 얹었는데, 3D 렌더된 노티 옆에 두면
    납작한 스티커로 보였다. 지금은 clay 가 두께 맵으로 부피를 만든다.
    (dark 는 예전 호출부 호환용으로만 남겨둔다)
    """
    return clay.render(layer, strength=strength)


def drop(layer, blur=9, off=(0, 7), op=52):
    """바닥 그림자 — 도형 실루엣이 아니라 눌린 타원이라야 자연스럽다."""
    return clay.finish(layer, shadow=True)


# ─────────── 소품 ───────────
def bottle(h=200):
    """젖병"""
    w = int(h * 0.46)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, h*0.20, w, h), radius=w*0.30, fill=PAL['glass'])
    d.rounded_rectangle((w*0.10, h*0.46, w*0.90, h*0.94), radius=w*0.22, fill=PAL['cream'])
    d.rounded_rectangle((w*0.22, h*0.10, w*0.78, h*0.30), radius=w*0.16, fill=PAL['body'])
    d.ellipse((w*0.34, 0, w*0.66, h*0.16), fill=PAL['deep'])
    for i in range(3):
        yy = h*0.56 + i*h*0.11
        d.rounded_rectangle((w*0.16, yy, w*0.34, yy+h*0.022), radius=h*0.011, fill=PAL['white'])
    return drop(shade(im))


def thermo(h=210):
    """체온계"""
    w = int(h * 0.30)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((w*0.28, 0, w*0.72, h*0.82), radius=w*0.22, fill=PAL['white'])
    d.rounded_rectangle((w*0.40, h*0.10, w*0.60, h*0.74), radius=w*0.10, fill=(235, 232, 226))
    d.rounded_rectangle((w*0.40, h*0.44, w*0.60, h*0.74), radius=w*0.10, fill=PAL['red'])
    d.ellipse((0, h*0.70, w, h), fill=PAL['red'])
    return drop(shade(im))


def suitcase(h=190):
    """캐리어"""
    w = int(h * 1.02)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((w*0.30, 0, w*0.70, h*0.22), radius=w*0.10, outline=PAL['arm'], width=int(w*0.07))
    d.rounded_rectangle((0, h*0.18, w, h), radius=w*0.14, fill=PAL['mint'])
    d.rounded_rectangle((w*0.10, h*0.30, w*0.90, h*0.88), radius=w*0.09, fill=PAL['cream'])
    d.rounded_rectangle((w*0.38, h*0.16, w*0.62, h*1.0), radius=w*0.05, fill=PAL['white'])
    return drop(shade(im))


def spoon_bowl(h=170):
    """이유식 그릇 + 숟가락"""
    w = int(h * 1.35)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    d.pieslice((0, h*0.20, w*0.78, h*1.14), 0, 180, fill=PAL['mint'])
    d.ellipse((0, h*0.10, w*0.78, h*0.44), fill=PAL['cream'])
    d.ellipse((w*0.08, h*0.16, w*0.70, h*0.38), fill=(246, 214, 150))
    d.rounded_rectangle((w*0.74, h*0.16, w*0.86, h*0.92), radius=w*0.05, fill=PAL['white'])
    d.ellipse((w*0.68, 0, w*0.94, h*0.26), fill=PAL['white'])
    return drop(shade(im))


def hat(h=120):
    """외출 모자"""
    w = int(h * 1.85)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    d.ellipse((0, h*0.52, w, h), fill=PAL['blue'])
    d.pieslice((w*0.22, h*0.02, w*0.78, h*1.02), 180, 360, fill=PAL['blue'])
    d.rounded_rectangle((w*0.22, h*0.52, w*0.78, h*0.66), radius=h*0.07, fill=PAL['cream'])
    return drop(shade(im))


def belt(w=250):
    """카시트 안전벨트 — 대각선 두 줄"""
    h = int(w * 1.05)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    d.line((w*0.16, 0, w*0.52, h*0.72), fill=PAL['arm'], width=int(w*0.13))
    d.line((w*0.84, 0, w*0.48, h*0.72), fill=PAL['arm'], width=int(w*0.13))
    d.rounded_rectangle((w*0.36, h*0.64, w*0.64, h*0.94), radius=w*0.06, fill=PAL['red'])
    d.rounded_rectangle((w*0.44, h*0.72, w*0.56, h*0.86), radius=w*0.03, fill=PAL['cream'])
    return shade(im, 0.35)


def cloth(h=90):
    """이마 물수건"""
    w = int(h * 2.3)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w, h), radius=h*0.34, fill=PAL['glass'])
    d.rounded_rectangle((w*0.08, h*0.22, w*0.92, h*0.50), radius=h*0.14, fill=PAL['white'])
    return shade(im, 0.4)


def cash(h=150):
    """지폐 뭉치 — 지원금 주제용"""
    w = int(h * 1.55)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    for i, c in enumerate([(126, 196, 142), (150, 214, 164), (176, 228, 186)]):
        o = i * h * 0.13
        d.rounded_rectangle((o*0.5, o, w - o*0.5, h*0.66 + o), radius=h*0.12, fill=c)
    r = h * 0.17
    cx, cy = w/2, h*0.56
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=PAL['cream'])
    return drop(shade(im))


def stroller(h=190):
    """유모차 — 캐노피 · 좌석 · 손잡이 · 바퀴"""
    w = int(h * 1.25)
    im = _clay((w, h)); d = ImageDraw.Draw(im)
    seat = (250, 214, 150)
    # 캐노피
    d.pieslice((w*0.06, h*0.04, w*0.72, h*0.70), 180, 360, fill=PAL['blue'])
    # 좌석
    d.polygon([(w*0.10, h*0.38), (w*0.66, h*0.38), (w*0.58, h*0.70), (w*0.20, h*0.70)], fill=seat)
    d.rounded_rectangle((w*0.08, h*0.36, w*0.68, h*0.48), radius=h*0.06, fill=PAL['cream'])
    # 손잡이
    d.line((w*0.68, h*0.16, w*0.94, h*0.44), fill=PAL['arm'], width=int(h*0.09))
    d.line((w*0.20, h*0.66, w*0.76, h*0.78), fill=PAL['arm'], width=int(h*0.07))
    # 바퀴
    for cx in (w*0.24, w*0.66):
        d.ellipse((cx-h*0.13, h*0.72, cx+h*0.13, h*0.98), fill=(86, 82, 78))
        d.ellipse((cx-h*0.05, h*0.805, cx+h*0.05, h*0.905), fill=PAL['cream'])
    return drop(shade(im))


def car(h=200):
    """자동차 — carlib 이 점토 렌더링까지 마쳐서 돌려준다."""
    import carlib
    return carlib.car(h)


# ─────────── 효과 ───────────
def zzz(h=150, color=(150, 160, 200)):
    im = _clay((int(h*0.95), h)); d = ImageDraw.Draw(im)
    w = im.width
    for i, (x, y, s) in enumerate([(w*0.50, h*0.60, 0.34), (w*0.24, h*0.28, 0.26), (w*0.04, h*0.04, 0.19)]):
        u = h * s
        t = max(3, int(u * 0.17))
        d.line((x, y, x+u, y), fill=color, width=t)
        d.line((x+u, y, x, y+u), fill=color, width=t)
        d.line((x, y+u, x+u, y+u), fill=color, width=t)
    return im


def sparkle(h=110, color=(255, 206, 92)):
    im = _clay((h, h)); d = ImageDraw.Draw(im)
    c = h/2
    for r, a in ((h*0.48, 0.16), (h*0.30, 0.24)):
        d.polygon([(c, c-r), (c+r*a, c-r*a), (c+r, c), (c+r*a, c+r*a),
                   (c, c+r), (c-r*a, c+r*a), (c-r, c), (c-r*a, c-r*a)], fill=color)
        color = tuple(min(255, v+18) for v in color)
    return im


def heart_pop(h=90):
    """작은 하트 — 마무리 장면 장식"""
    im = _clay((int(h*1.1), h)); d = ImageDraw.Draw(im)
    w = im.width; r = h*0.30
    d.ellipse((w*0.5-r*1.5, h*0.10, w*0.5-r*0.1, h*0.10+r*1.4), fill=PAL['pink'])
    d.ellipse((w*0.5+r*0.1, h*0.10, w*0.5+r*1.5, h*0.10+r*1.4), fill=PAL['pink'])
    d.polygon([(w*0.5-r*1.44, h*0.10+r*0.6), (w*0.5+r*1.44, h*0.10+r*0.6),
               (w*0.5, h*0.94)], fill=PAL['pink'])
    return im


def sweat(h=90):
    im = _clay((int(h*0.66), h)); d = ImageDraw.Draw(im)
    w = im.width
    d.polygon([(w*0.5, 0), (w, h*0.66), (0, h*0.66)], fill=PAL['blue'])
    d.ellipse((0, h*0.36, w, h), fill=PAL['blue'])
    d.ellipse((w*0.22, h*0.52, w*0.46, h*0.78), fill=(206, 232, 250))
    return im


def bubble(text_w=360, h=150, color=(255, 255, 255)):
    """말풍선 — 글자는 카드 쪽에서 얹는다"""
    im = _clay((text_w, int(h*1.22))); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, text_w, h), radius=h*0.36, fill=color)
    d.polygon([(text_w*0.30, h*0.94), (text_w*0.46, h*0.94), (text_w*0.33, h*1.20)], fill=color)
    return drop(im, blur=7, off=(0, 5), op=34)


# ─────────── 장면 조합 ───────────
def scene(base_pose, height, props=(), flip=False, pad=0.35):
    """노티 + 소품을 한 장으로 합친다.

    props = [(이미지, 앵커x, 앵커y, 기준)] · 앵커는 노티 크기 대비 비율(0~1)

    예전엔 캔버스를 노티 크기로만 잡아서, 옆이나 아래로 나간 소품이
    잘려 나갔다(자동차 바퀴가 그렇게 날아갔다).
    이제 소품 위치를 먼저 재서 필요한 만큼 캔버스를 넓힌다.
    """
    n = pose(base_pose, height, flip)
    nx, ny = n.width, n.height

    # 노티를 (0,0) 에 뒀다고 가정하고 각 소품의 좌상단을 구한다
    placed = []
    for g, fx, fy, *rest in props:
        placed.append((g, int(nx*fx - g.width/2), int(ny*fy - g.height/2),
                       rest[0] if rest else None))

    xs = [0, nx] + [p[1] for p in placed] + [p[1]+p[0].width for p in placed]
    ys = [0, ny] + [p[2] for p in placed] + [p[2]+p[0].height for p in placed]
    m = int(height * 0.04)                     # 숨 쉴 여백
    x0, x1 = min(xs) - m, max(xs) + m
    y0, y1 = min(ys) - m, max(ys) + m

    im = Image.new('RGBA', (x1-x0, y1-y0), (0, 0, 0, 0))
    back = [p for p in placed if p[3] == 'back']
    front = [p for p in placed if p[3] != 'back']
    for g, px, py, _ in back:
        im.alpha_composite(g, (px-x0, py-y0))
    im.alpha_composite(n, (-x0, -y0))
    for g, px, py, _ in front:
        im.alpha_composite(g, (px-x0, py-y0))
    return im.crop(im.getbbox())
