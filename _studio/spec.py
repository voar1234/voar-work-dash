# -*- coding: utf-8 -*-
"""게시물을 '명세(spec)'로 적고 한 번에 찍어내는 엔진.

여태 게시물마다 함수를 따로 썼다. 12건을 그렇게 짜면 1,500줄이 넘고
고칠 때마다 같은 실수를 반복하게 된다.

카드 종류는 사실 몇 개 안 된다.
  cover  표지          — 눈썹 · 큰 제목 · 부제 · 노티
  rows   항목 나열      — 제목 + 표(아이콘·값·설명)
  text   문장 나열      — 제목 + 여러 줄
  close  마무리         — 제목 + 문장 + 아이콘 띠 + 출처
이 넷으로 명세를 쓰면 카드가 나온다.
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_v3 import *
from PIL import Image
import picto
import noti_studio as ns

# 이미 UTF-8 이면 다시 감싸지 않는다.
# 두 번 감싸면 먼저 감싼 쪽 버퍼가 닫혀서 출력이 죽는다 (여러 번 겪음).
if (getattr(sys.stdout, 'encoding', '') or '').lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TONES = ['coral', 'mint', 'gold', 'sky', 'lilac', 'rose', 'sage']


def _title(d, y, lines, size):
    """['평문', ('강조', True)] 형태를 받아 색을 섞어 그린다."""
    for ln in lines:
        parts = []
        for seg in (ln if isinstance(ln, list) else [ln]):
            if isinstance(seg, tuple):
                parts.append((seg[0], seg[1]))
            else:
                parts.append((seg, INK))
        y = center_mixed(d, y, parts, size)
    return y


def render(card, tone, seed, out, page=None):
    kind = card.get('kind', 'rows')
    acc = ACC[tone][0]
    im, d = canvas(tone, seed=seed)
    brandmark(d)

    def T(lines, size):
        return _title(d, y, [[(s, acc) if isinstance(s, tuple) else s for s in
                              (ln if isinstance(ln, list) else [ln])] for ln in lines], size)

    y = eyebrow(d, card.get('top', 190), card['eyebrow'], tone)

    for ln in card['title']:
        segs = []
        for seg in (ln if isinstance(ln, list) else [ln]):
            segs.append((seg[0], acc) if isinstance(seg, tuple) else (seg, INK))
        y = center_mixed(d, y, segs, card.get('size', 64))

    if card.get('sub'):
        y = center(d, y + 8, card['sub'], f(REG, card.get('sub_size', 33)), SUB)

    if kind == 'rows':
        rows = [(r[0], r[1], r[2], r[3], r[4] if len(r) > 4 else tone) for r in card['rows']]
        h = card.get('row_h') or (112 if len(rows) >= 4 else 124)
        y = stat_box(d, y + card.get('gap', 26), rows, tone, h_row=h)
        for t in card.get('after', []):
            y = center(d, y + 2, t, f(BOLD if t.startswith('*') else REG, 33),
                       INK if t.startswith('*') else SUB)

    elif kind == 'text':
        y = rule(d, y + 16, 90, tone)
        for t in card['lines']:
            y = center(d, y, t, f(REG, card.get('line_size', 36)), SUB) if t else y + 18

    elif kind == 'close':
        if card.get('lines'):
            y = rule(d, y + 16, 90, tone)
            for t in card['lines']:
                y = center(d, y, t, f(REG, 35), SUB) if t else y + 16
        if card.get('icons'):
            y = icon_row(d, y + 34, card['icons'])

    if card.get('noti'):
        name, size = card['noti'][0], card['noti'][1]
        props = card['noti'][2] if len(card['noti']) > 2 else None
        if isinstance(name, dict):
            # 주문제작 — 처음 한 번만 만들고 그 뒤로는 만들어둔 파일을 쓴다
            g = ns.made(name['name'], name['prompt'], name.get('base', 'hello'), size)
        elif props:
            g = ns.scene(name, size, props, pad=0.42)
        else:
            g = ns.pose(name, size)
        paste(im, g, W/2, H - card.get('noti_y', 186))

    if card.get('note'):
        fnt = f(REG, 22)
        d.text(((W - d.textlength(card['note'], font=fnt)) / 2, H - 172),
               card['note'], font=fnt, fill=(206, 196, 182))

    footer(d, page, save_hint=bool(page))
    im.save(out, quality=95)
    return y          # 콘텐츠가 끝난 높이 — 세로 배치를 잡을 때 쓴다


def build(tag, cards):
    n = len(cards)
    for i, c in enumerate(cards, 1):
        tone = c.get('tone') or TONES[(i - 1) % len(TONES)]
        render(c, tone, i - 1, f'{tag}{i}.jpg', None if i == 1 else f'{i}/{n}')
    ims = [Image.open(f'{tag}{i}.jpg') for i in range(1, n + 1)]
    s = 0.30
    tw, th = int(W * s), int(H * s)
    cols = 4
    rows = (n + cols - 1) // cols
    sh = Image.new('RGB', (tw * cols + 10 * (cols + 1), (th + 10) * rows + 10), (236, 236, 236))
    for i, g in enumerate(ims):
        sh.paste(g.resize((tw, th), Image.LANCZOS),
                 ((i % cols) * (tw + 10) + 10, (i // cols) * (th + 10) + 10))
    sh.save(f'preview_{tag}.jpg', quality=92)
    return n
