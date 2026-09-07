# -*- coding: utf-8 -*-
"""소재 자동 보충.

소재 탭이 비어가는데 손으로 채우고 있었다. 이 파일이 대신 채운다.

  1) 지금 소재가 몇 건인지 본다
  2) 최소 보유량(MIN) 아래면 후보 풀에서 뽑아 채운다
  3) 이미 만든 것 · 발행한 것 · 소재에 있는 것과 겹치면 건너뛴다
  4) 경쟁 계정에서 잡힌 새 글 주제도 후보로 섞는다

후보 풀은 시기별로 짜뒀다. 실제로 검색량이 많고
「저장해두고 꺼내보는」 성격이 있는 것들만 골랐다.

사용:
  python _idea_feed.py            # 부족하면 채운다
  python _idea_feed.py --force 5  # 무조건 5건 추가
  python _idea_feed.py --list     # 지금 소재 목록만
"""
import io, json, os, random, re, sys, urllib.request, uuid
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SB = 'https://vgzodlljefanuipohevy.supabase.co/rest/v1/baby_studio'
KEY = 'sb_publishable_Xj1aWpDLyfaAPxkn1q-ErA_94MEBT9V'
HEAD = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}
KST = timezone(timedelta(hours=9))

MIN_IDEAS = 12          # 이 아래로 떨어지면 채운다
ADD_PER_RUN = 4         # 한 번에 이만큼까지
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_idea_feed.log')

# (주제, 축, 시기)
POOL = [
    # ── 임신 막달 · 출산 준비 ──
    ('출산가방, 36주 전에 싸야 하는 이유', 'prep', '임신 막달'),
    ('진통 시작 신호와 병원 가는 타이밍', 'prep', '임신 막달'),
    ('제왕절개 후 회복, 첫 일주일 순서', 'prep', '임신 막달'),
    ('산후조리원 고를 때 꼭 물어볼 5가지', 'prep', '임신 막달'),
    ('출생신고 언제까지? 놓치면 과태료', 'prep', '임신 막달'),
    ('모유수유 첫 주에 겪는 일들', 'feed', '임신 막달'),

    # ── 신생아 0~3개월 ──
    ('신생아 목욕, 며칠에 한 번이 맞나요', 'care', '0~6개월'),
    ('로션 바르는 타이밍 — 목욕 후 3분', 'care', '0~6개월'),
    ('배꼽 소독 언제까지 하나요', 'care', '0~6개월'),
    ('신생아 황달, 언제 병원 가야 하나요', 'health', '0~6개월'),
    ('트림 안 시키면 생기는 일', 'feed', '0~6개월'),
    ('분유 온도 몇 도가 맞나요', 'feed', '0~6개월'),
    ('눕히자마자 깨는 아기, 등센서 없애는 법', 'sleep', '0~6개월'),
    ('신생아 코막힘, 집에서 할 수 있는 것', 'health', '0~6개월'),
    ('아기 손싸개 언제까지 씌우나요', 'care', '0~6개월'),
    ('영아산통(배앓이) 우는 아기 달래는 법', 'health', '0~6개월'),

    # ── 영유아 4~12개월 ──
    ('월령별 하루 수면시간표 (신생아~36개월)', 'sleep', '0~6개월'),
    ('이앓이 시작 신호와 달래는 법', 'health', '7~12개월'),
    ('예방접종 일정 한눈에 정리', 'health', '7~12개월'),
    ('아기 변 색깔로 보는 건강 신호', 'health', '7~12개월'),
    ('중기 이유식, 덩어리 언제부터', 'feed', '7~12개월'),
    ('철분 부족 신호와 채우는 음식', 'feed', '7~12개월'),
    ('기어다니기 시작하면 집에서 치울 것', 'safety', '7~12개월'),
    ('아기 첫 신발 고르는 기준', 'care', '7~12개월'),
    ('밤중에 자꾸 깨는 4개월 수면퇴행', 'sleep', '0~6개월'),

    # ── 돌 이후 ──
    ('돌 지나면 분유 끊어야 하나요', 'feed', '12개월~'),
    ('생우유 언제부터 먹여도 되나요', 'feed', '12개월~'),
    ('밥 안 먹는 아기, 억지로 먹이면 안 되는 이유', 'feed', '12개월~'),
    ('낮잠 몇 번까지 재워야 하나요', 'sleep', '12개월~'),
    ('어린이집 적응, 첫 2주 버티는 법', 'life', '12개월~'),
    ('말 트이는 시기와 늦을 때 확인할 것', 'dev', '12개월~'),
    ('훈육은 몇 개월부터 통하나요', 'dev', '12개월~'),
    ('아기 열성경련, 그 순간 해야 할 것', 'health', '12개월~'),
    ('기저귀 떼는 시기와 신호', 'care', '12개월~'),
    ('18개월 재접근기 — 엄마 껌딱지', 'dev', '12개월~'),

    # ── 제도·비용 ──
    ('어린이집 입소 대기 넣는 법', 'life', '전체 공통'),
    ('아이 의료비 지원, 놓치기 쉬운 것', 'life', '전체 공통'),
    ('아기 여권 만들기 — 준비물과 순서', 'life', '전체 공통'),
    ('첫만남이용권 쓸 수 있는 곳', 'life', '전체 공통'),

    # ── 임신 막달 · 출산 준비 (추가) ──
    ('유도분만, 어떤 경우에 하나요', 'prep', '임신 막달'),
    ('무통주사 언제 맞고 언제 못 맞나', 'prep', '임신 막달'),
    ('출산 후 첫 배변이 무서운 이유', 'prep', '임신 막달'),
    ('젖몸살 왔을 때 푸는 순서', 'feed', '임신 막달'),
    ('초유가 안 나와도 괜찮은 이유', 'feed', '임신 막달'),
    ('배냇저고리 몇 벌이면 충분할까', 'prep', '임신 막달'),
    ('출산 준비물 중 안 사도 되는 것', 'prep', '임신 막달'),
    ('산후도우미 정부지원 신청하는 법', 'life', '임신 막달'),

    # ── 신생아 0~6개월 (추가) ──
    ('신생아 딸꾹질, 멈추게 해야 하나요', 'health', '0~6개월'),
    ('태열과 아토피 구분하는 법', 'health', '0~6개월'),
    ('신생아 여드름 언제 없어지나요', 'care', '0~6개월'),
    ('아기 눈곱이 계속 낄 때', 'health', '0~6개월'),
    ('게우는 것과 토하는 것의 차이', 'feed', '0~6개월'),
    ('유축 모유 보관 기간과 해동법', 'feed', '0~6개월'),
    ('젖병 소독 언제까지 하나요', 'care', '0~6개월'),
    ('공갈젖꼭지 써도 되나요', 'care', '0~6개월'),
    ('속싸개 언제 졸업하나요', 'sleep', '0~6개월'),
    ('신생아 체중이 안 늘 때 볼 것', 'feed', '0~6개월'),
    ('백일의 기적은 정말 오나요', 'sleep', '0~6개월'),
    ('아기 방 온도·습도 맞추기', 'care', '0~6개월'),
    ('신생아 첫 외출, 언제부터', 'care', '0~6개월'),
    ('사경(고개 기울임) 의심 신호', 'health', '0~6개월'),

    # ── 7~12개월 (추가) ──
    ('이유식 거부할 때 확인할 것', 'feed', '7~12개월'),
    ('알레르기 유발 식품 먹이는 순서', 'feed', '7~12개월'),
    ('컵 연습 언제 시작하나요', 'feed', '7~12개월'),
    ('분리불안 시작 시기와 대처', 'dev', '7~12개월'),
    ('낮잠 붙이기가 실패하는 이유', 'sleep', '7~12개월'),
    ('치아 나는 순서와 칫솔질 시작', 'care', '7~12개월'),
    ('기저귀 발진 빨리 낫게 하는 법', 'health', '7~12개월'),
    ('해열제 교차복용, 이럴 때만', 'health', '7~12개월'),
    ('수족구와 구내염 구분하는 법', 'health', '7~12개월'),
    ('잡고 서기 시작하면 확인할 것', 'safety', '7~12개월'),
    ('아기 물, 언제부터 얼마나', 'feed', '7~12개월'),
    ('돌잔치 준비 체크리스트', 'life', '7~12개월'),

    # ── 돌 이후 (추가) ──
    ('편식 시작됐을 때 안 통하는 방법', 'feed', '12개월~'),
    ('미디어 노출은 몇 개월부터', 'dev', '12개월~'),
    ('놀이터 데뷔 전에 알아둘 것', 'safety', '12개월~'),
    ('대소변 가리기, 실패해도 되는 이유', 'care', '12개월~'),
    ('어린이집 첫 감기 릴레이 버티기', 'health', '12개월~'),
    ('낮잠 끊는 시기와 신호', 'sleep', '12개월~'),
    ('자다 우는 야경증과 악몽의 차이', 'sleep', '12개월~'),
    ('둘째 생기면 첫째가 아기가 되는 이유', 'dev', '12개월~'),
    ('카시트 거부하는 아이, 이렇게', 'safety', '12개월~'),
    ('말 늦은 아이, 언제 검사받나요', 'dev', '12개월~'),
    ('밥상 앞에서 돌아다니는 아이', 'feed', '12개월~'),
    ('손톱 물어뜯기 시작하면', 'dev', '12개월~'),

    # ── 제도 · 비용 (추가) ──
    ('아동수당·부모급여 언제까지 받나요', 'life', '전체 공통'),
    ('영유아 건강검진 시기 놓치면', 'life', '전체 공통'),
    ('어린이집과 유치원은 뭐가 다른가요', 'life', '전체 공통'),
    ('아이 실비보험 가입 시기', 'life', '전체 공통'),
    ('육아휴직 나눠 쓰는 법', 'life', '전체 공통'),
    ('아이 계좌 만들기와 증여신고', 'life', '전체 공통'),
    ('예방접종 증명서 발급받는 법', 'life', '전체 공통'),
    ('소아과 진료 잘 받는 법', 'life', '전체 공통'),

    # ── 안전 (추가) ──
    ('카시트 각도와 장착, 이것만은', 'safety', '전체 공통'),
    ('아기 화상, 첫 1분에 할 일', 'safety', '전체 공통'),
    ('삼켰을 때 응급처치 순서', 'safety', '전체 공통'),
    ('침대에서 떨어졌을 때 관찰할 것', 'safety', '전체 공통'),
    ('응급실 갈까 말까 판단 기준', 'health', '전체 공통'),
    ('목욕 중 사고, 이 순간을 조심', 'safety', '전체 공통'),
]


def log(msg):
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


def pull():
    req = urllib.request.Request(SB + '?id=eq.main&select=data', headers=HEAD)
    return json.load(urllib.request.urlopen(req, timeout=30))[0]['data']


def push(d):
    ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    d['updatedAt'] = ts
    h = dict(HEAD); h['Prefer'] = 'resolution=merge-duplicates'
    urllib.request.urlopen(urllib.request.Request(
        SB + '?on_conflict=id',
        data=json.dumps([{'id': 'main', 'data': d, 'updated_at': ts}]).encode(),
        headers=h, method='POST'), timeout=30)


def norm(t):
    """제목 비교용 — 공백·기호를 털어낸다."""
    return re.sub(r'[^0-9가-힣a-zA-Z]', '', (t or '')).lower()


def taken(d):
    """이미 쓴 주제 (소재 · 제작 · 발행 전부)"""
    s = set()
    for i in d.get('ideas', []):
        s.add(norm(i.get('topic')))
    for q in list(d.get('queue', [])) + list(d.get('reels') or []):
        s.add(norm(q.get('title')))
    return s




def main():
    d = pull()

    if '--list' in sys.argv:
        for i in d.get('ideas', []):
            print(f"  [{i.get('status','')}] {i.get('topic','')}")
        print(f'\n총 {len(d.get("ideas", []))}건')
        return

    used = taken(d)
    have = len(d.get('ideas', []))

    force = 0
    if '--force' in sys.argv:
        k = sys.argv.index('--force')
        force = int(sys.argv[k + 1]) if len(sys.argv) > k + 1 else ADD_PER_RUN

    need = force if force else max(0, MIN_IDEAS - have)
    if not need:
        log(f'소재 {have}건 — 충분함 (기준 {MIN_IDEAS})')
        return
    need = min(need, ADD_PER_RUN if not force else need)

    # 경쟁사 캡션은 더 이상 소재로 쓰지 않는다.
    # 남의 글 첫 줄을 그대로 제목에 넣는 셈이라 쓸 수도 없고 저작권상으로도 위험하다.
    cands = [(t, p, a, '') for t, p, a in POOL if norm(t) not in used]
    if not cands:
        log('후보 소진 — 풀에 새 주제를 추가해야 합니다')
        return

    random.shuffle(cands)
    today = datetime.now(KST).strftime('%Y-%m-%d')
    added = []
    d.setdefault('ideas', [])
    for topic, pillar, age, src in cands[:need]:
        if norm(topic) in used:
            continue
        used.add(norm(topic))
        d['ideas'].insert(0, {
            # 마이크로초를 잘라 쓰고 두 자리 난수만 붙이면 같은 실행에서 부딪힌다.
            # 실제로 '배꼽 소독' 소재가 같은 ID 로 두 번 들어갔다.
            'id': 'i_' + uuid.uuid4().hex[:14],
            'topic': topic, 'pillar': pillar, 'age': age,
            'status': '아이디어', 'created': today,
            'auto': True, **({'from': src} if src else {}),
        })
        added.append(topic)

    if added:
        push(d)
        log(f'소재 {len(added)}건 추가 (보유 {have} → {have + len(added)})')
        for t in added:
            log('   + ' + t)


if __name__ == '__main__':
    main()
