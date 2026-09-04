# -*- coding: utf-8 -*-
"""보아르 아가노트 · 인스타 발행기 (승인 게이트 적용)

대시보드(Supabase)의 발행 큐에서 **승인된 항목만** 가져와 발행한다.
  status='approved'                     → 발행
  status='pending'  + autoPublish=True  → 발행
  그 외                                  → 건너뜀

사용:
  python _publish_insta.py            # 승인 + 예정 시각이 된 것만 발행
  python _publish_insta.py --now      # 예정 무시하고 지금 발행
  python _publish_insta.py --dry-run  # 발행 없이 대상만 확인
"""
import json, sys, time, urllib.request, urllib.parse, io, os
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
def _load_cfg():
    """설정을 읽는다.

    GitHub Actions 처럼 토큰 파일을 둘 수 없는 곳에서는
    환경변수(Secrets)를 쓴다. 로컬에서는 기존 파일을 그대로 쓴다.
    """
    tok = os.environ.get('IG_ACCESS_TOKEN')
    if tok:
        return {
            'access_token': tok,
            'ig_user_id': os.environ.get('IG_USER_ID', ''),
            'graph_version': os.environ.get('IG_GRAPH_VERSION', 'v21.0'),
        }
    p = os.path.join(HERE, 'baby', 'data', 'insta_config.json')
    return json.load(open(p, encoding='utf-8'))


CFG = _load_cfg()
TOK, IG = CFG['access_token'], CFG['ig_user_id']
GRAPH = 'https://graph.facebook.com/' + CFG['graph_version']

SB_URL = 'https://vgzodlljefanuipohevy.supabase.co/rest/v1/baby_studio'
SB_KEY = 'sb_publishable_Xj1aWpDLyfaAPxkn1q-ErA_94MEBT9V'
SB_HEAD = {'apikey': SB_KEY, 'Authorization': 'Bearer ' + SB_KEY,
           'Content-Type': 'application/json'}

DRY = '--dry-run' in sys.argv
NOW = '--now' in sys.argv      # 예정 시각을 무시하고 지금 올린다 (명시할 때만)
KST = timezone(timedelta(hours=9))


def is_due(item):
    """예정 시각이 됐는가.

    이걸 안 보고 올리는 바람에 예정이 6시간 남은 글이 먼저 나간 적이 있다.
    예정이 아예 없으면 지금 올려도 되는 것으로 본다.
    """
    d = item.get('scheduledAt')
    if not d:
        return True
    t = item.get('scheduledTime') or '00:00'
    try:
        when = datetime.strptime(f'{d} {t}', '%Y-%m-%d %H:%M').replace(tzinfo=KST)
    except ValueError:
        return True
    return datetime.now(KST) >= when


# ─────────────────────── Supabase ───────────────────────
def load_state():
    req = urllib.request.Request(SB_URL + '?id=eq.main&select=data', headers=SB_HEAD)
    rows = json.load(urllib.request.urlopen(req, timeout=30))
    if not rows:
        raise SystemExit('대시보드 상태(main)가 없습니다.')
    return rows[0]['data']


def save_state(d):
    ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    d['updatedAt'] = ts
    h = dict(SB_HEAD); h['Prefer'] = 'resolution=merge-duplicates'
    body = json.dumps([{'id': 'main', 'data': d, 'updated_at': ts}]).encode()
    urllib.request.urlopen(
        urllib.request.Request(SB_URL + '?on_conflict=id', data=body, headers=h, method='POST'),
        timeout=30)


# ─────────────────────── Graph API ───────────────────────
def api(path, params, method='GET'):
    params['access_token'] = TOK
    if method == 'POST':
        req = urllib.request.Request(GRAPH + path,
                                     data=urllib.parse.urlencode(params).encode(), method='POST')
    else:
        req = urllib.request.Request(GRAPH + path + '?' + urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except Exception as e:
        try:
            return {'_error': json.load(e).get('error', {})}
        except Exception:
            return {'_error': str(e)}


def publish_reel(item):
    """릴스 발행. video_url 은 공개 접근 가능한 MP4 여야 한다."""
    url = item.get('videoUrl')
    if not url:
        raise RuntimeError('videoUrl 이 없습니다')
    r = api(f'/{IG}/media', {'media_type': 'REELS', 'video_url': url,
                             'caption': item.get('caption', '')}, 'POST')
    if '_error' in r:
        raise RuntimeError(r['_error'])
    cid = r['id']

    # 영상은 이미지보다 처리 시간이 길다 (수십 초~수 분)
    for _ in range(60):
        st = api(f'/{cid}', {'fields': 'status_code,status'})
        code = st.get('status_code')
        if code == 'FINISHED':
            break
        if code == 'ERROR':
            raise RuntimeError(f'영상 처리 실패: {st.get("status") or st}')
        time.sleep(6)
    else:
        raise RuntimeError('영상 처리 시간 초과')

    pub = api(f'/{IG}/media_publish', {'creation_id': cid}, 'POST')
    if '_error' in pub:
        raise RuntimeError(pub['_error'])
    mid = pub['id']
    info = api(f'/{mid}', {'fields': 'permalink'})
    return mid, info.get('permalink')


def publish(item):
    """캐러셀(2장 이상) 또는 단일 이미지 발행. 성공 시 (media_id, permalink)."""
    if item.get('videoUrl'):
        return publish_reel(item)

    imgs = item.get('images') or []
    if not imgs:
        raise RuntimeError('이미지가 없습니다')

    if len(imgs) == 1:
        r = api(f'/{IG}/media', {'image_url': imgs[0], 'caption': item.get('caption', '')}, 'POST')
        if '_error' in r: raise RuntimeError(r['_error'])
        cid = r['id']
    else:
        children = []
        for u in imgs:
            r = api(f'/{IG}/media', {'image_url': u, 'is_carousel_item': 'true'}, 'POST')
            if '_error' in r: raise RuntimeError(f'{u} → {r["_error"]}')
            children.append(r['id'])
        r = api(f'/{IG}/media', {'media_type': 'CAROUSEL',
                                 'children': ','.join(children),
                                 'caption': item.get('caption', '')}, 'POST')
        if '_error' in r: raise RuntimeError(r['_error'])
        cid = r['id']

    # 컨테이너 처리 대기
    for _ in range(25):
        st = api(f'/{cid}', {'fields': 'status_code'})
        code = st.get('status_code')
        if code == 'FINISHED':
            break
        if code == 'ERROR':
            raise RuntimeError(f'컨테이너 처리 실패: {st}')
        time.sleep(4)

    pub = api(f'/{IG}/media_publish', {'creation_id': cid}, 'POST')
    if '_error' in pub: raise RuntimeError(pub['_error'])
    mid = pub['id']
    info = api(f'/{mid}', {'fields': 'permalink'})
    return mid, info.get('permalink')


# ─────────────────────── 메인 ───────────────────────
def already_out(q):
    """이미 인스타에 올라간 글인가. 발행 흔적이 하나라도 있으면 참."""
    return bool(q.get('mediaId') or q.get('permalink') or q.get('publishedAt'))


def main():
    d = load_state()
    # 게시물 큐와 릴스 큐를 함께 처리한다 (릴스는 videoUrl 유무로 구분)
    queue = (d.get('queue') or []) + (d.get('reels') or [])
    auto = d.get('autoPublish') is True

    print(f'발행 모드 : {"자동 발행 허용" if auto else "수동 승인 (승인된 것만)"}')
    print(f'큐        : {len(queue)}건\n')

    ready = [q for q in queue
             if not already_out(q)
             and (q.get('status') == 'approved' or (auto and q.get('status') == 'pending'))]
    targets = ready if NOW else [q for q in ready if is_due(q)]
    waiting = [q for q in ready if q not in targets]

    if waiting:
        print('예정 시각 전이라 건너뜁니다:')
        for q in waiting:
            print(f'   - {q.get("title")}  → {q.get("scheduledAt")} {q.get("scheduledTime", "")}')
        print('   (지금 바로 올리려면 --now)')
        print()

    if not targets:
        pend = [q for q in queue if q.get('status') == 'pending']
        print('발행할 항목이 없습니다.')
        if pend:
            print(f'\n※ 승인 대기 {len(pend)}건 — 대시보드 「발행」 탭에서 「발행 승인」을 눌러주세요:')
            for q in pend:
                print('   -', q.get('title'))
        return

    print(f'발행 대상 {len(targets)}건:')
    for q in targets:
        print(f'   - {q.get("title")}  (카드 {len(q.get("images") or [])}장)')

    if DRY:
        print('\n[--dry-run] 실제 발행은 하지 않았습니다.')
        return

    for q in targets:
        print(f'\n▶ {q.get("title")}')
        try:
            mid, link = publish(q)
            q['status'] = 'published'
            q['mediaId'] = mid
            q['permalink'] = link
            q['publishedAt'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            print('  ✓ 발행 완료 →', link)
        except Exception as e:
            q['status'] = 'error'
            q['error'] = str(e)
            print('  ✗ 실패:', e)

    # queue 는 두 목록을 합친 것이라, 항목 객체 자체가 원본을 참조한다.
    # 따라서 d 를 그대로 저장하면 양쪽 모두 갱신된다.
    save_state(d)
    print('\n대시보드에 결과 반영 완료.')


if __name__ == '__main__':
    main()
