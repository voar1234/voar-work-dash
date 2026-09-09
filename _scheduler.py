# -*- coding: utf-8 -*-
"""예약 발행기.

여태 빠져 있던 조각이다.
「발행 승인」을 누르면 캘린더에 예정 슬롯이 잡히지만,
그 시각이 와도 아무도 올려주지 않았다. 이 파일이 그 역할을 한다.

  1) 60초마다 대시보드(Supabase)를 확인
  2) status='approved' 이면서 예정 시각이 지난 항목을 찾는다
  3) _publish_insta.py 의 발행 함수를 그대로 써서 올린다
  4) 결과(permalink)를 대시보드에 반영한다

승인 게이트는 그대로다 — 승인 안 된 건 절대 안 올린다.
예정 시각이 없으면 승인 즉시 올린다.

사용:
  python _scheduler.py             # 상주 (기본 12시간)
  python _scheduler.py --once      # 한 번만 확인하고 종료
  python _scheduler.py --dry-run   # 대상만 출력
"""
import io, json, os, sys, time, urllib.request
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _publish_insta as pub          # 이 모듈이 stdout 인코딩을 이미 잡아둔다
                                     # (여기서 또 감싸면 버퍼가 닫혀 출력이 죽는다)

SB = 'https://vgzodlljefanuipohevy.supabase.co/rest/v1/baby_studio'
KEY = 'sb_publishable_Xj1aWpDLyfaAPxkn1q-ErA_94MEBT9V'
HEAD = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}

EVERY = 60           # 확인 주기(초)
MAX_HOURS = 12
KST = timezone(timedelta(hours=9))

ONCE = '--once' in sys.argv
DRY = '--dry-run' in sys.argv


LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_scheduler.log')


def log(msg):
    """화면과 파일에 같이 남긴다 (작업 스케줄러로 돌 땐 화면이 없다)."""
    line = f'[{datetime.now(KST):%Y-%m-%d %H:%M:%S}] {msg}'
    try:
        print(line)
    except Exception:
        pass
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def now_utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def pull():
    req = urllib.request.Request(SB + '?id=eq.main&select=data', headers=HEAD)
    return json.load(urllib.request.urlopen(req, timeout=25))[0]['data']


def push(d):
    ts = now_utc()
    d['updatedAt'] = ts
    h = dict(HEAD); h['Prefer'] = 'resolution=merge-duplicates'
    urllib.request.urlopen(urllib.request.Request(
        SB + '?on_conflict=id',
        data=json.dumps([{'id': 'main', 'data': d, 'updated_at': ts}]).encode(),
        headers=h, method='POST'), timeout=25)


def slot_time(item, slots):
    """예정 슬롯에서 이 글의 발행 시각을 찾는다. 없으면 None."""
    for s in (slots or []):
        if s and s.get('postId') == item.get('id') and s.get('date'):
            return s.get('date'), (s.get('time') or '00:00')
    return None


def is_due(item, now, slots=()):
    """예정 시각이 됐는가.

    예정은 슬롯에 적히는데 예전엔 큐의 scheduledAt 만 봤다.
    그게 비어 있으면 '지금'으로 쳐서 승인하자마자 나갔다.
    (2026-09-07 15:17 — 20:30 예정이던 2건이 조기 발행)

    이제 슬롯을 먼저 보고, 예정을 어디서도 못 찾으면 올리지 않는다.
    예정 없는 글은 올리는 쪽보다 두는 쪽이 안전하다.
    """
    at = slot_time(item, slots)
    if not at:
        date = item.get('scheduledAt')
        if not date:
            return False                  # 예정 미상 — 건너뛴다
        at = (date, item.get('scheduledTime') or '00:00')
    try:
        when = datetime.strptime(f'{at[0]} {at[1]}', '%Y-%m-%d %H:%M').replace(tzinfo=KST)
    except ValueError:
        return False
    return now >= when


def already_out(q):
    """이미 인스타에 올라간 글인가. 발행 흔적이 하나라도 있으면 참."""
    return bool(q.get('mediaId') or q.get('permalink') or q.get('publishedAt'))


def due_items(d, now):
    auto = d.get('autoPublish') is True
    slots = d.get('slots') or []
    out, held = [], []
    for q in (d.get('queue') or []) + (d.get('reels') or []):
        if already_out(q):
            continue                      # 중복 발행 차단
        ok = q.get('status') == 'approved' or (auto and q.get('status') == 'pending')
        if not ok:
            continue
        if is_due(q, now, slots):
            out.append(q)
        else:
            held.append(q)
    if held:
        for q in held:
            # 슬롯에 없어도 큐에 예정이 적혀 있을 수 있다.
            # 그걸 안 보고 '미배정'이라고 찍으면 멀쩡히 대기 중인 글을
            # 예정이 없는 것처럼 오해하게 된다.
            at = slot_time(q, slots)
            if not at and q.get('scheduledAt'):
                at = (q['scheduledAt'], q.get('scheduledTime') or '00:00')
            when = f'{at[0]} {at[1]}' if at else '예정 미배정 (슬롯에 넣어주세요)'
            log(f'· 대기: {q.get("title")}  → {when}')
    return out


def run_once():
    d = pull()
    now = datetime.now(KST)
    targets = due_items(d, now)
    if not targets:
        return 0

    print(f'\n[{now:%m-%d %H:%M}] 발행 시각 도달 {len(targets)}건')
    for q in targets:
        log(f'▶ {q.get("title")}')
        if DRY:
            print('   [--dry-run] 실제 발행 안 함')
            continue
        try:
            mid, link = pub.publish(q)
            q['status'] = 'published'
            q['mediaId'] = mid
            q['permalink'] = link
            q['publishedAt'] = now_utc()
            q['updated'] = now_utc()
            log('   ✓ ' + str(link))
        except Exception as e:
            q['status'] = 'error'
            q['error'] = str(e)[:200]
            q['updated'] = now_utc()
            log('   ✗ ' + str(e)[:120])

    if not DRY:
        push(d)
        log('   대시보드 반영 완료')
    return len(targets)


def main():
    if ONCE or DRY:
        try:
            n = run_once()
        except Exception as e:
            log('실행 실패: ' + str(e)[:150])
            return
        if not n:
            log('발행 대상 없음')
        return

    deadline = time.time() + MAX_HOURS * 3600
    print(f'예약 발행기 시작 · {EVERY}초 주기 · 최대 {MAX_HOURS}시간')
    published = 0
    while time.time() < deadline:
        try:
            published += run_once()
        except Exception as e:
            log('확인 실패: ' + str(e)[:90])
        time.sleep(EVERY)
    print(f'종료 · 이번 가동에서 {published}건 발행')


if __name__ == '__main__':
    main()
