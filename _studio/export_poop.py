# -*- coding: utf-8 -*-
"""릴스 「응가 사건」 키프레임 내보내기.

힉스필드에 묶음별로 올려 사이를 채우게 한다.
묶음 하나가 영상 한 토막(4초 안팎)이 된다.

크기 비율을 따로 주는 이유:
  몸통 높이를 똑같이 맞추면 아기만 나오는 컷에서 아기가 어른만 해진다.
  묶음 안에서 캐릭터가 커졌다 작아졌다 하면 보간이 깨지므로,
  아기 단독 컷은 어른 대비 0.62 로 줄여 일정하게 유지한다.
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keyframe as kf

BABY = 0.62          # 어른 몸통 대비 아기 몸통 비율

GROUPS = {
    # 2026-11-10 ② 빠져 있던 웃음 포인트를 되살려 다시 뽑았다 (_e).
    #   엄마가 기저귀를 '들쳐' 확인 → 아기가 그걸 따라 엄마 바지를 '내려' 확인.
    #   이 두 동작이 이 릴스의 전부인데 그림에 아예 없었다.
    # A — 전에는 1·2 컷에 엄마가 없어서 2→3 보간 때 엄마가 허공에서 생겼다.
    #     네 컷 모두 엄마를 넣었고, 그래서 비율도 전부 1.0 이다.
    'A_평소': [('a1_toddle_e', 1.0), ('a2_tell_e', 1.0),
               ('a3_check_e', 1.0), ('a4_lift_e', 1.0)],
    # B — 전부 아기 단독. 블록이 1번에만 있으면 보간 중에 사라지므로 3컷 모두 깔았다.
    #     바지와 무관해 그대로 둔다 (_c).
    'B_그날': [('b1_play_c', BABY), ('b2_lookup_c', BABY), ('b3_run_c', BABY)],
    # C — 바지가 D 에서 갑자기 생기면 안 되므로 같이 다시 뽑았다.
    'C_사건': [('c1_dish_e', 1.0), ('c2_arrive_e', 1.0),
               ('c3_toot_e', 1.0), ('c4_sniff_e', 1.0)],
    # D — 2컷으로는 펀치라인이 안 산다. 당긴다 → 붙잡는다 → 빨개진다 3컷으로 늘렸다.
    #     d2 는 혼자 아기가 엄마 왼쪽에 서 있다. 그대로 두면 d1->d2 에서 아기가
    #     화면을 가로질러 순간이동한다. 뒤집어 아기를 오른쪽으로 보낸다(세 번째 값).
    'D_결말': [('d1_pull_e', 1.0), ('d2_hold_e', 1.0, True), ('d3_shy_e', 1.0)],
}


def _prep(src):
    """원본을 여백만 잘라 들고 오고, 큰 노티 몸통 상자도 같이 준다."""
    im = Image.open(src).convert('RGBA')
    box = kf._solid(im).getbbox()
    if box:
        im = im.crop(box)
    return im, kf.body_box(im)


def plan(items):
    """묶음 하나의 확대배율을 한꺼번에 정한다.

    컷마다 따로 정하면 두 가지가 깨진다.
      · 측정이 조금만 흔들려도 묶음 안에서 캐릭터가 커졌다 작아졌다 한다
      · 몸통을 BODY_H 로 맞추다 보면 그림 전체가 안전영역을 넘어 머리가 잘린다
        (c3_toot_e 가 1.80배로 확대돼 위쪽 573px 이 날아갔다)

    그래서 ① 컷마다 목표 몸통 높이로 배율을 잡고
          ② 그중 하나라도 안전영역(FIT_H)을 넘으면 묶음 전체를 같은 비율로
             줄인다. 묶음 안의 상대 크기는 그대로 남는다.
    """
    sized, k = [], 1.0
    for it in items:
        name, ratio, flip = (it + (False,))[:3]
        src = os.path.join(kf.MADE, name + '.png')
        if not os.path.exists(src):
            sized.append((name, None, None, None))
            continue
        im, bb = _prep(src)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            bb = kf.body_box(im)
        sc = (kf.BODY_H * ratio) / (bb[3] - bb[1]) if bb else 1.0
        sc = max(0.2, min(3.0, sc))
        k = min(k, kf.FIT_H / (im.height * sc))
        sized.append((name, im, bb, sc))
    return [(n, im, bb, sc * k if sc else None) for n, im, bb, sc in sized], k


def put(im, scale, out):
    """1080×1920 크림 배경 위에 규격대로 올린다 (kf.place 와 같은 규칙)."""
    im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))),
                   Image.LANCZOS)
    bb = kf.body_box(im)
    canvas = Image.new('RGB', (kf.W, kf.H), kf.BG)
    cx = ((bb[0] + bb[2]) // 2) if bb else im.width // 2
    canvas.paste(im, (kf.W // 2 - cx, kf.BASELINE - im.height), im)
    canvas.save(out, quality=95)
    return out


if __name__ == '__main__':
    root = os.path.join(kf.HERE, 'for_video')
    for g, items in GROUPS.items():
        dst = os.path.join(root, g)
        os.makedirs(dst, exist_ok=True)
        rows, k = plan(items)
        print('%s   묶음 공통 축소 %.2f배' % (g, k))
        for i, (name, im, bb, sc) in enumerate(rows, 1):
            if im is None:
                print('   없음:', name)
                continue
            out = put(im, sc, os.path.join(dst, f'{i}_{name}.jpg'))
            print('    %-16s 몸통 %3d -> %3d · %.2f배'
                  % (os.path.basename(out), bb[3] - bb[1],
                     int((bb[3] - bb[1]) * sc), sc))
    print('→', root)
