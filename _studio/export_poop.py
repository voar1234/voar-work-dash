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
    # A — 아기 단독 컷(1·2)을 0.78 로 키워 3·4 의 아기와 크기를 맞춘다.
    #     0.62 로 두니 둘이 함께 나오는 컷에서 아기가 갑자기 커져 보였다.
    'A_평소': [('a1_toddle', 0.78), ('a2_tell', 0.78),
               ('a3_check', 1.0), ('a4_lift', 1.0)],
    # B — 전부 아기 단독이라 묶음 안에서만 일정하면 된다.
    'B_그날': [('b1_play', BABY), ('b2_lookup', BABY), ('b3_run2', BABY)],
    # C — 아기 키가 노티 엉덩이에 닿아야 방귀 설정이 산다. 셋 다 둘이 함께 나오는 컷으로 다시 뽑았다.
    'C_사건': [('c1_dish', 1.0), ('c2_arrive2', 1.0),
               ('c3_toot2', 1.0), ('c4_sniff2', 1.0)],
    'D_결말': [('d1_pull', 1.0), ('d2_blush', 1.0)],
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
