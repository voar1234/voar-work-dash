# -*- coding: utf-8 -*-
"""점토 질감 렌더러.

노티는 3D로 렌더링된 점토 인형이라 도형에 그라데이션만 얹으면 붙여놨을 때 겉돈다.
원본을 측정해서(hello.png) 그 특성을 그대로 흉내낸다.

  · 명암 폭 121 / 255  — 대비가 꽤 크다
  · 가장자리 128 vs 내부 159 — 테두리가 어둡게 말려 들어간다 (둥근 단면)
  · 위→아래로 갈수록 어두워지고, 맨 위/맨 아래는 다시 꺾인다
  · 좌상단이 밝다 (조명이 왼쪽 위)

핵심은 '두께 맵'이다.
알파를 크게 흐리면 중심이 높고 가장자리가 낮은 값이 나오는데,
이걸 표면 높이로 보고 명암을 계산하면 도형이 부풀어 오른 것처럼 보인다.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

LIGHT = (-0.42, -0.55)      # 조명 방향 (왼쪽 위)


def _arr(img):
    return np.asarray(img).astype(np.float32)


def thickness(alpha, r):
    """알파 → 두께 맵(0~1). 가장자리 0, 중심 1.

    한 번만 흐리면 안쪽이 전부 1.0 으로 포화돼 평평해진다.
    반지름을 달리해 여러 번 흐린 뒤 겹쳐야 안쪽에도 완만한 언덕이 생긴다.
    """
    a = Image.fromarray(alpha)
    acc = None
    for k, wgt in ((0.45, 0.25), (1.0, 0.40), (2.1, 0.35)):
        b = _arr(a.filter(ImageFilter.GaussianBlur(max(1.5, r * k)))) / 255.0
        acc = b * wgt if acc is None else acc + b * wgt
    m = acc.max()
    if m > 1e-6:
        acc = acc / m
    return np.clip(acc, 0, 1)


def normal_from(t):
    """두께 맵의 기울기로 표면 법선을 근사한다."""
    gy, gx = np.gradient(t)
    nz = 0.55
    ln = np.sqrt(gx * gx + gy * gy + nz * nz) + 1e-6
    return gx / ln, gy / ln, nz / ln


def render(layer, strength=1.0, edge=0.42, glossy=0.22, warm=(255, 240, 214)):
    """평면 도형 → 점토 덩어리.

    layer  : RGBA (단색으로 칠해진 도형)
    strength: 전체 입체감
    edge   : 가장자리가 말려 들어가는 정도
    glossy : 위쪽 하이라이트 세기
    """
    rgba = _arr(layer)
    rgb, a = rgba[..., :3], rgba[..., 3]
    h, w = a.shape
    r = max(3.0, min(h, w) * 0.16)

    t = thickness(a.astype(np.uint8), r)
    nx, ny, nz = normal_from(t)

    lx, ly = LIGHT
    lz = 0.72
    ln = (lx * lx + ly * ly + lz * lz) ** 0.5
    lx, ly, lz = lx / ln, ly / ln, lz / ln

    # 확산광 — 좌상단이 밝게
    ndl = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
    diff = 0.72 + 0.46 * ndl

    # 덩어리 전체에 걸리는 완만한 명암.
    # 3D 렌더는 면 하나하나가 아니라 덩어리 전체가 위→아래로 어두워진다.
    yy = np.linspace(0, 1, h)[:, None]
    xx = np.linspace(0, 1, w)[None, :]
    volume = 1.05 - 0.26 * yy - 0.07 * xx

    # 가장자리 말림 — 두께가 얇은 곳이 어둡게 (측정값: 테두리가 31 어두움)
    rim = np.clip(t / 0.72, 0, 1)
    shade = 1.0 - edge * (1.0 - rim) ** 1.5

    # 위쪽 반사 하이라이트
    spec = ndl ** 12 * glossy * t

    # 아래쪽 바운스 — 점토는 밑에서 살짝 되받는 빛이 있다
    yy = np.linspace(0, 1, h)[:, None]
    bounce = np.clip((yy - 0.74) / 0.26, 0, 1) * 0.10 * t

    k = diff * shade * volume
    # 면적의 중앙값이 원래 색 그대로 나오도록 정규화한다.
    # 이걸 안 하면 전체가 눌려 색이 탁해진다 (첫 시도의 실패 원인).
    inside = a > 200
    if inside.sum() > 20:
        k = k / max(0.35, float(np.median(k[inside])))
    k = np.clip(k, 0.32, 1.12) ** (1.0 / max(0.2, strength))
    out = rgb * k[..., None]
    out += np.array(warm, dtype=np.float32) * (spec + bounce)[..., None]

    # 실루엣 바로 안쪽의 어두운 테.
    # 3D 렌더는 면이 시선에서 급히 꺾이는 가장자리가 어둡게 깔린다.
    # 이게 없으면 아무리 명암을 넣어도 스티커처럼 보인다.
    am = Image.fromarray(a.astype(np.uint8))
    inner = _arr(am.filter(ImageFilter.MinFilter(5)))
    band = np.clip((a - inner) / 255.0, 0, 1)
    band = _arr(Image.fromarray((band * 255).astype(np.uint8))
                .filter(ImageFilter.GaussianBlur(max(1.0, r * 0.10)))) / 255.0
    out *= (1.0 - 0.20 * band)[..., None]

    # 표면 결 — 점토는 완전히 매끈하지 않다. 아주 옅게만.
    rs = np.random.RandomState(7)
    grain = rs.normal(0, 1, (h, w)).astype(np.float32)
    grain = _arr(Image.fromarray(((grain * 40) + 128).clip(0, 255).astype(np.uint8))
                 .filter(ImageFilter.GaussianBlur(0.8))) - 128.0
    out += (grain * 0.04 * t)[..., None]

    out = np.clip(out, 0, 255)

    im = Image.fromarray(np.dstack([out, a]).astype(np.uint8), 'RGBA')
    return im


def ground_shadow(size, cx, cy, rx, ry, op=64):
    """바닥 그림자 — 도형 모양이 아니라 눌린 타원이라야 자연스럽다."""
    sh = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(122, 96, 66, op))
    return sh.filter(ImageFilter.GaussianBlur(max(4, ry * 0.7)))


def finish(layer, shadow=True, **kw):
    """점토 렌더링 + 바닥 그림자를 얹어 마무리."""
    body = render(layer, **kw)
    if not shadow:
        return body
    w, h = body.size
    pad = int(h * 0.14)
    out = Image.new('RGBA', (w, h + pad), (0, 0, 0, 0))
    a = np.asarray(body)[..., 3]
    rows = np.where(a.max(axis=1) > 20)[0]
    bottom = rows[-1] if len(rows) else h - 1
    cols = np.where(a.max(axis=0) > 20)[0]
    cx = (cols[0] + cols[-1]) / 2 if len(cols) else w / 2
    span = (cols[-1] - cols[0]) if len(cols) else w
    out.alpha_composite(ground_shadow((w, h + pad), cx, bottom + pad * 0.45,
                                      span * 0.46, pad * 0.42))
    out.alpha_composite(body, (0, 0))
    return out
