# -*- coding: utf-8 -*-
"""인스타 지표 → 대시보드(Supabase) 동기화.

대시보드는 GitHub Pages 공개 페이지라 액세스 토큰을 심을 수 없다.
그래서 여기서 Graph API를 호출해 결과만 Supabase에 넣고, 대시보드는 그걸 읽는다.

사용: python _sync_insta_metrics.py
"""
import io, json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
def _load_cfg():
    """GitHub Actions 에서는 Secrets(환경변수), 로컬에서는 파일."""
    tok = os.environ.get('IG_ACCESS_TOKEN')
    if tok:
        return {'access_token': tok,
                'ig_user_id': os.environ.get('IG_USER_ID', ''),
                'graph_version': os.environ.get('IG_GRAPH_VERSION', 'v21.0')}
    return json.load(open(os.path.join(HERE, 'baby', 'data', 'insta_config.json'),
                          encoding='utf-8'))


CFG = _load_cfg()
TOK, IG = CFG['access_token'], CFG['ig_user_id']
GRAPH = 'https://graph.facebook.com/' + CFG['graph_version']

SB = 'https://vgzodlljefanuipohevy.supabase.co/rest/v1/baby_studio'
SB_KEY = 'sb_publishable_Xj1aWpDLyfaAPxkn1q-ErA_94MEBT9V'
SB_HEAD = {'apikey': SB_KEY, 'Authorization': 'Bearer ' + SB_KEY,
           'Content-Type': 'application/json'}


def g(path, **params):
    params['access_token'] = TOK
    url = GRAPH + path + '?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except Exception as e:
        try:
            return {'_err': json.load(e).get('error', {}).get('message')}
        except Exception:
            return {'_err': str(e)}


def collect():
    m = {}
    prof = g('/' + IG, fields='username,followers_count,follows_count,media_count')
    if '_err' in prof:
        raise SystemExit('프로필 조회 실패: ' + prof['_err'])
    m['username'] = prof.get('username')
    m['followers'] = prof.get('followers_count')
    m['follows'] = prof.get('follows_count')
    m['posts'] = prof.get('media_count')

    # 최근 30일 도달 — 계정 인사이트는 한 번에 30일까지만 조회됨
    until = datetime.now(timezone.utc)
    since = until - timedelta(days=29)
    ins = g(f'/{IG}/insights', metric='reach', period='day',
            since=int(since.timestamp()), until=int(until.timestamp()))
    if '_err' not in ins:
        vals = []
        for row in ins.get('data', []):
            vals += [v.get('value', 0) for v in row.get('values', [])]
        m['reach30'] = sum(vals)
    else:
        m['reach30'] = None
        print('  · 도달 조회 실패:', ins['_err'])

    # 게시물별 저장수 평균
    med = g(f'/{IG}/media', fields='id,timestamp,permalink', limit=30)
    saves, per = [], []
    for it in med.get('data', []):
        mi = g(f"/{it['id']}/insights", metric='saved,reach,likes,comments')
        if '_err' in mi:
            continue
        row = {x['name']: x['values'][0]['value'] for x in mi.get('data', [])}
        row['permalink'] = it.get('permalink')
        row['timestamp'] = it.get('timestamp')
        per.append(row)
        if 'saved' in row:
            saves.append(row['saved'])
    m['avgSaved'] = round(sum(saves) / len(saves)) if saves else None
    m['recent'] = per[:10]
    m['syncedAt'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    return m


def push(metrics):
    req = urllib.request.Request(SB + '?id=eq.main&select=data', headers=SB_HEAD)
    rows = json.load(urllib.request.urlopen(req, timeout=30))
    if not rows:
        raise SystemExit('대시보드 상태(main)가 없습니다.')
    d = rows[0]['data']
    d['metrics'] = metrics
    d['followers'] = metrics.get('followers')      # 기존 필드도 맞춰둠
    ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    d['updatedAt'] = ts
    h = dict(SB_HEAD); h['Prefer'] = 'resolution=merge-duplicates'
    body = json.dumps([{'id': 'main', 'data': d, 'updated_at': ts}]).encode()
    urllib.request.urlopen(
        urllib.request.Request(SB + '?on_conflict=id', data=body, headers=h, method='POST'),
        timeout=30)


if __name__ == '__main__':
    m = collect()
    print('계정   : @%s' % m['username'])
    print('팔로워 : %s  (팔로잉 %s)' % (m['followers'], m['follows']))
    print('게시물 : %s' % m['posts'])
    print('30일 도달 : %s' % m['reach30'])
    print('평균 저장 : %s' % m['avgSaved'])
    for r in m['recent']:
        print('   -', r.get('timestamp', '')[:10],
              '저장 %s · 도달 %s · 좋아요 %s' % (r.get('saved'), r.get('reach'), r.get('likes')))
    push(m)
    print('\n대시보드에 반영 완료.')
