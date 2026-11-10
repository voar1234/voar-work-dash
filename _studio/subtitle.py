# -*- coding: utf-8 -*-
"""릴스 「응가 사건」 — 묶음 영상 이어붙이기 + 자막 얹기.

왜 자막을 키프레임에 안 넣었나
  힉스필드가 키프레임 사이를 보간하면 글자가 같이 녹아서 뭉개진다.
  글자는 보간이 끝난 영상 위에 나중에 얹어야 또렷하다.

쓰는 법
  1) 힉스필드에서 받은 영상을 for_video/clips 에 넣는다.
       2장(시작·끝) 모드로 받았으면 — 9개
         A1 A2 A3 / B1 B2 / C1 C2 C3 / D1    (.mp4)
       멀티 키프레임으로 묶음째 받았으면 — 4개
         A B C D                             (.mp4)
       앞글자로 묶고 번호순으로 이어 붙이므로 둘 다 그대로 돌아간다.
  2) python subtitle.py
  3) for_video/아가노티_응가사건.mp4 가 나온다.

자막 시각을 '초'가 아니라 '묶음 안에서의 비율'로 적은 이유
  힉스필드가 뱉는 길이가 매번 조금씩 다르다. 초로 박아두면 길이가 바뀔 때마다
  자막이 밀린다. 비율로 두면 묶음이 3초든 5초든 제자리에 붙는다.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, 'for_video')
CLIPS = os.path.join(VID, 'clips')
TMP = os.path.join(VID, '_sub_tmp')

FD = r'C:\Users\OA\claude-test\폰트'
HEAVY = os.path.join(FD, 'NanumSquareNeo-eHv.ttf')
BOLD = os.path.join(FD, 'NanumSquareNeo-cBd.ttf')

W, H = 1080, 1920
# 릴스는 아래 420px 쯤을 캡션·버튼이 덮는다. 글자는 1500 위에만 둔다.
INK = (58, 48, 40)
CREAM = (255, 250, 240)

# 영상 내내 붙어 있는 상단 제목 띠. (글자, 색) 조각으로 적어 핵심만 노랑으로 뺀다.
TITLE = [('아기가 ', 'w'), ('응가', 'y'), ('를 배우면 생기는 일', 'w')]

# (시작비율, 끝비율, 문구, 스타일)
#   style 'hook'  맨 위 띠  — 첫 3초 동안 이탈을 막는 한 줄
#         'line'  아래쪽   — 보통 설명 자막
#         'talk'  아래쪽   — 대사. 따옴표 대신 색으로 구분
#         'bang'  화면 중앙 — 효과음. 크게 한 번 때린다
CAPS = {
    'A': [(0.00, 0.50, '응가하면 꼭 알려주러 와요', 'line'),
          (0.52, 1.00, '응가! 응가!', 'talk')],
    'B': [(0.00, 0.50, '그날도 혼자 잘 놀던 중', 'line'),
          (0.52, 1.00, '엄마 찾아 부엌으로 쪼르르', 'line')],
    'C': [(0.00, 0.45, '설거지하던 엄마', 'line'),
          (0.48, 0.70, '뿡', 'bang'),
          (0.72, 1.00, '어...? 이 냄새는...', 'line')],
    'D': [(0.00, 0.55, '엄마! 응가! 응가!', 'talk'),
          (0.58, 1.00, '아니야 아기야… 엄마 아니야…', 'line')],
}


def run(args):
    p = subprocess.run(args, capture_output=True)
    if p.returncode:
        sys.stderr.write(p.stderr.decode('utf-8', 'replace')[-2000:])
        raise SystemExit('ffmpeg 실패')
    return p.stdout.decode('utf-8', 'replace').strip()


def dur(path):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                      '-of', 'default=nw=1:nk=1', path]))


def _wrap(d, text, fnt, limit):
    out, line = [], ''
    for w in text.split(' '):
        t = (line + ' ' + w).strip()
        if line and d.textlength(t, font=fnt) > limit:
            out.append(line)
            line = w
        else:
            line = t
    if line:
        out.append(line)
    return out


def card(text, style, path):
    """자막 한 장을 투명 PNG 로 그린다.

    ffmpeg drawtext 를 안 쓰는 이유: 윈도우에서 한글 경로·글꼴 지정이 자주 깨지고
    줄바꿈·외곽선을 세밀하게 못 준다. PIL 로 그려 올리는 쪽이 확실하다.
    """
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    if style == 'bang':
        fnt = ImageFont.truetype(HEAVY, 150)
        col, y0, stroke = (255, 138, 92), 170, 14
    elif style == 'hook':
        fnt = ImageFont.truetype(HEAVY, 62)
        col, y0, stroke = INK, 150, 0
    elif style == 'talk':
        fnt = ImageFont.truetype(HEAVY, 76)
        col, y0, stroke = (240, 124, 80), 1310, 10
    else:
        fnt = ImageFont.truetype(BOLD, 68)
        col, y0, stroke = INK, 1330, 10

    lines = _wrap(d, text, fnt, W - 140)
    gap = int(fnt.size * 1.28)
    y = y0 - (len(lines) - 1) * gap // 2

    if style == 'hook':                      # 크림 띠를 깔아 배경과 분리한다
        top = y - 34
        bot = y + (len(lines) - 1) * gap + fnt.size + 34
        d.rounded_rectangle([60, top, W - 60, bot], 30, fill=CREAM + (236,))

    for ln in lines:
        x = (W - d.textlength(ln, font=fnt)) / 2
        d.text((x, y), ln, font=fnt, fill=col,
               stroke_width=stroke, stroke_fill=(255, 252, 246))
        y += gap

    im.save(path)
    return path


def title_card(path):
    """검은 띠 + 흰 글씨, 핵심 단어만 노랑. 영상 내내 떠 있는다."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(HEAVY, 72)

    # 줄바꿈: 조각을 이어 붙이며 폭을 넘으면 끊는다
    lines, cur, limit = [], [], W - 120
    for text, col in TITLE:
        for word in text.replace(' ', ' ​').split('​'):
            if not word:
                continue
            wide = sum(d.textlength(t, font=fnt) for t, _ in cur) + d.textlength(word, font=fnt)
            if cur and wide > limit:
                lines.append(cur)
                cur = []
            cur.append((word, col))
    if cur:
        lines.append(cur)

    gap = int(fnt.size * 1.26)
    pad = 34
    bot = pad * 2 + gap * (len(lines) - 1) + fnt.size
    d.rectangle([0, 0, W, bot], fill=(18, 16, 15, 242))

    y = pad
    for ln in lines:
        x = (W - sum(d.textlength(t, font=fnt) for t, _ in ln)) / 2
        for t, col in ln:
            d.text((x, y), t, font=fnt,
                   fill=(255, 221, 64) if col == 'y' else (255, 255, 255))
            x += d.textlength(t, font=fnt)
        y += gap
    im.save(path)
    return path


def main():
    os.makedirs(TMP, exist_ok=True)
    # 한 묶음이 영상 여러 토막으로 쪼개져 올 수 있다.
    # 힉스필드 기본 모드는 이미지 2장(시작·끝)만 받으므로 4컷 묶음은 3토막이 된다.
    # A1.mp4 A2.mp4 A3.mp4 처럼 앞글자+번호로 넣으면 번호순으로 이어 붙인다.
    # 멀티 키프레임 모델로 묶음째 받았으면 A.mp4 한 개만 넣어도 그대로 돌아간다.
    found = []
    for key in 'ABCD':
        hit = sorted(f for f in os.listdir(CLIPS)
                     if f.lower().endswith(('.mp4', '.mov')) and f.upper().startswith(key))
        if not hit:
            raise SystemExit(f'{CLIPS} 에 {key} 로 시작하는 영상이 없습니다')
        found.append((key, [os.path.join(CLIPS, f) for f in hit]))

    # ① 묶음마다 9:16 으로 맞춰 다시 쓴다.
    #    힉스필드가 정사각(1440x1440)으로 뱉는 경우가 있어 그대로 이으면 섞인다.
    #    자막은 '묶음 전체' 기준 비율이라, 묶음이 몇 토막으로 왔든
    #    토막 길이를 합친 구간에 걸쳐 붙는다.
    parts, marks, t = [], [], 0.0
    for key, srcs in found:
        g0 = t
        for i, src in enumerate(srcs, 1):
            out = os.path.join(TMP, '%s%d_9x16.mp4' % (key, i))
            run(['ffmpeg', '-y', '-i', src, '-vf',
                 f'scale={W}:{H}:force_original_aspect_ratio=increase,'
                 f'crop={W}:{H},fps=30,setsar=1',
                 '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out])
            parts.append(out)
            t += dur(out)
        marks.append((key, g0, t - g0))
        print('  %s : 토막 %d개 · %.1f초' % (key, len(srcs), t - g0))

    lst = os.path.join(TMP, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as f:
        for q in parts:
            f.write("file " + repr(q.replace(chr(92), "/")) + chr(10))
    joined = os.path.join(TMP, 'joined.mp4')
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', joined])

    # ② 자막을 비율 → 실제 초로 바꿔 얹는다
    ins, filt, last, n = ['-i', joined], [], '[0:v]', 0
    ins += ['-i', title_card(os.path.join(TMP, 'title.png'))]
    n += 1
    filt.append(f'{last}[{n}:v]overlay=0:0[v{n}]')      # 제목은 처음부터 끝까지
    last = f'[v{n}]'
    for key, start, length in marks:
        for a, b, text, style in CAPS.get(key, []):
            png = card(text, style, os.path.join(TMP, f'{key}{n}.png'))
            ins += ['-i', png]
            n += 1
            s, e = start + length * a, start + length * b
            tag = f'[v{n}]'
            filt.append(f"{last}[{n}:v]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'{tag}")
            last = tag

    final = os.path.join(VID, '아가노티_응가사건.mp4')
    run(['ffmpeg', '-y'] + ins + ['-filter_complex', ';'.join(filt),
         '-map', last, '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
         '-r', '30', final])
    print('길이 %.1f초 · 자막 %d장' % (t, n))
    print('→', final)


if __name__ == '__main__':
    main()
