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
    'D_결말': [('d1_pull_e', 1.0), ('d2_hold_e', 1.0), ('d3_blush_e', 1.0)],
}


def place(src, out, ratio):
    """keyframe.place 와 같되 목표 몸통 높이에 비율을 곱한다."""
    old = kf.BODY_H
    try:
        kf.BODY_H = int(old * ratio)
        return kf.place(src, out)
    finally:
        kf.BODY_H = old


if __name__ == '__main__':
    root = os.path.join(kf.HERE, 'for_video')
    for g, items in GROUPS.items():
        dst = os.path.join(root, g)
        os.makedirs(dst, exist_ok=True)
        print(g)
        for i, (name, ratio) in enumerate(items, 1):
            src = os.path.join(kf.MADE, name + '.png')
            if not os.path.exists(src):
                print('   없음:', name)
                continue
            out = place(src, os.path.join(dst, f'{i}_{name}.jpg'), ratio)
            print('   ', os.path.basename(out))
    print('→', root)
