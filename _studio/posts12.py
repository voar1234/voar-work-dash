# -*- coding: utf-8 -*-
"""제작 요청 12건 — 명세로 한 번에.

자료
  · 목욕/보습  대한소아과학회(주 2~3회), WHO·한국신생아학회(첫 목욕 6~24시간 뒤),
               목욕 후 30초~3분 내 보습
  · 예방접종   질병관리청 예방접종도우미 · 국가지원 19종
  · 나머지     육아 매체·후기 다수 교차 확인
"""
import io, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import build
import noti_studio as ns

POSTS = {}

# ─────────────── ① 신생아 목욕 ───────────────
POSTS['bath'] = [
 dict(kind='text', eyebrow='씻기기', top=200, size=74,
      title=[['신생아 목욕,'], [('며칠에 한 번',), '이']], sub='매일 안 씻겨도 괜찮습니다',
      lines=[], noti=('curious', 380), noti_y=186),
 dict(kind='rows', eyebrow='횟수', title=[['매일보다'], [('주 2~3회',), '가 나아요']],
      sub='자주 씻기면 피부 보호막이 벗겨집니다',
      rows=[('신생아 시기', '주 2~3회', '대한소아과학회 권장', 'baby', 'mint'),
            ('땀 많은 날', '가볍게', '물수건으로 닦아만 줘도 됩니다', 'check', 'sky'),
            ('목욕 시간', '5~10분', '길면 체온이 떨어져요', 'clock', 'gold')]),
 dict(kind='rows', eyebrow='첫 목욕', title=[['태어나고'], [('바로',), ' 씻기지 않아요']],
      sub='태지가 피부를 보호합니다',
      rows=[('첫 목욕', '6~24시간 뒤', 'WHO·한국신생아학회 권장', 'clock', 'gold'),
            ('배꼽 떨어지기 전', '통목욕 ✕', '부분만 닦아주세요', 'alert', 'rose'),
            ('떨어진 뒤', '통목욕 ○', '보통 생후 2주쯤', 'check', 'mint')]),
 dict(kind='rows', eyebrow='물 온도', title=[['어른한테는'], [('미지근',), '한 정도']],
      rows=[('물 온도', '37~38℃', '팔꿈치로 확인하세요', 'clock', 'sky'),
            ('실내 온도', '24~26℃', '욕실을 미리 데워두기', 'house', 'mint'),
            ('물 깊이', '아기 배꼽', '얕게 받으세요', 'alert', 'coral')]),
 dict(kind='rows', eyebrow='순서', title=[['얼굴부터'], [('아래로',), ' 내려가요']],
      rows=[('얼굴 · 머리', '1', '물 안 묻은 상태에서 먼저', 'check', 'lilac'),
            ('몸 · 팔다리', '2', '접히는 곳은 특히 꼼꼼히', 'baby', 'mint'),
            ('엉덩이', '3', '가장 마지막에', 'check', 'gold')]),
 dict(kind='close', eyebrow='기억할 것', title=[['깨끗한 것보다'], [('촉촉한',), ' 게 먼저']],
      sub='너무 자주 씻기면 오히려 건조해집니다',
      icons=[('주 2~3회', 'mint', 'baby'), ('5~10분', 'sky', 'clock'),
             ('37~38℃', 'gold', 'check'), ('바로 보습', 'rose', 'heart')],
      noti=('love', 280), noti_y=200,
      note='대한소아과학회·한국신생아학회 참고 · 아기 피부 상태에 따라 다릅니다'),
]

# ─────────────── ② 로션 타이밍 ───────────────
POSTS['lotion'] = [
 dict(kind='text', eyebrow='씻기기', top=200, size=72,
      title=[['로션은'], [('목욕 후 3분',), ' 안에']], sub='이 3분이 하루를 좌우합니다',
      lines=[], noti=('hello', 380), noti_y=186),
 dict(kind='rows', eyebrow='왜 3분이냐면', title=[['그 안에'], [('수분',), '이 날아가요']],
      rows=[('목욕 직후', '수분 최대', '피부가 물을 머금은 상태', 'heart', 'sky'),
            ('3분 지나면', '증발 시작', '오히려 씻기 전보다 건조', 'alert', 'coral'),
            ('그래서', '물기 남은 채', '톡톡 두드려 말리고 바로', 'check', 'mint')]),
 dict(kind='rows', eyebrow='바르는 법', title=[['문지르지 말고'], [('눌러서',)]],
      rows=[('손에 먼저', '체온으로', '차가우면 아기가 놀라요', 'heart', 'gold'),
            ('넓게 펴서', '누르듯이', '문지르면 자극이 됩니다', 'check', 'mint'),
            ('접히는 곳', '한 번 더', '목·겨드랑이·사타구니', 'baby', 'rose')]),
 dict(kind='rows', eyebrow='양', title=[['생각보다'], [('많이',), ' 발라요']],
      sub='얇게 바르면 안 바른 것과 비슷합니다',
      rows=[('기준', '번들거릴 정도', '흡수될 때까지 기다리지 마세요', 'check', 'lilac'),
            ('건조한 계절', '하루 2~3번', '목욕 때 말고도', 'clock', 'sky'),
            ('아기 얼굴', '더 자주', '침 닿는 입가는 특히', 'baby', 'coral')]),
 dict(kind='close', eyebrow='기억할 것', title=[['목욕은 씻는 게 아니라'], [('보습 준비',), '예요']],
      lines=['물기 톡톡 → 3분 안에 로션', '이 순서만 지키면 됩니다.'],
      noti=('best', 290), noti_y=200),
]

# ─────────────── ③ 등센서 ───────────────
POSTS['back'] = [
 dict(kind='text', eyebrow='재우기', top=196, size=70,
      title=[['눕히자마자 깨는'], [('등센서',), ' 없애기']], sub='품에서 잘 자다가 왜 그럴까요',
      lines=[], noti=('sleepy', 380), noti_y=186),
 dict(kind='rows', eyebrow='왜 깨냐면', title=[['깊이 잠들기 ', ('전',)], ['눕혀서예요']],
      rows=[('잠든 직후', '얕은 잠', '작은 자극에도 깹니다', 'clock', 'lilac'),
            ('깊은 잠까지', '15~20분', '팔에 힘이 빠질 때까지', 'baby', 'mint'),
            ('자세 변화', '놀람 반사', '갑자기 떨어지는 느낌', 'alert', 'coral')]),
 dict(kind='rows', eyebrow='순서', title=[['이 순서대로'], ['하면 ', ('덜 깨요',)]],
      rows=[('팔 힘 확인', '1', '축 늘어지면 깊은 잠', 'check', 'mint'),
            ('엉덩이부터', '2', '머리 말고 엉덩이가 먼저 닿게', 'baby', 'sky'),
            ('손 떼지 말고', '3', '30초쯤 가슴에 손 얹고 있기', 'heart', 'rose')]),
 dict(kind='rows', eyebrow='환경', title=[['눕는 자리가'], [('차가우면',), ' 깹니다']],
      rows=[('잠자리 온도', '미리 데우기', '손으로 몇 초 짚어두면 됩니다', 'house', 'gold'),
            ('속싸개', '감싸주기', '놀람 반사를 줄여줍니다', 'heart', 'mint'),
            ('소리·빛', '일정하게', '갑자기 조용해져도 깨요', 'check', 'sky')]),
 dict(kind='close', eyebrow='기억할 것', title=[['등센서는'], [('고장',), '이 아니에요']],
      lines=['크면서 저절로 없어집니다.', '', '지금 안 되는 건 아기가 아직', '어려서일 뿐이에요.'],
      noti=('love', 280), noti_y=196),
]

# ─────────────── ④ 트림 ───────────────
POSTS['burp'] = [
 dict(kind='text', eyebrow='먹이기', top=200, size=72,
      title=[['트림 안 시키면'], [('생기는 일',)]], sub='꼭 시켜야 하나 싶으시죠',
      lines=[], noti=('curious', 380), noti_y=186),
 dict(kind='rows', eyebrow='왜 필요하냐면', title=[['먹을 때 ', ('공기',)], ['도 같이 들어가요']],
      rows=[('공기가 차면', '배가 아파요', '먹고 나서 우는 이유', 'alert', 'coral'),
            ('눕히면', '역류', '토하거나 사레들릴 수 있어요', 'alert', 'rose'),
            ('트림으로', '빼주기', '이게 전부입니다', 'check', 'mint')]),
 dict(kind='rows', eyebrow='방법 3', title=[['셋 중 ', ('편한 걸로',)]],
      rows=[('어깨에 올리기', '가장 흔함', '턱을 어깨에 걸치고 등 토닥', 'baby', 'mint'),
            ('앉혀서', '턱 받치고', '한 손으로 가슴·턱 지지', 'check', 'sky'),
            ('엎드려 눕히기', '무릎 위에', '배가 눌리며 나옵니다', 'heart', 'gold')]),
 dict(kind='rows', eyebrow='안 나올 때', title=[['5분 해보고'], [('안 나오면',), ' 그만']],
      sub='억지로 오래 하면 아기가 힘들어요',
      rows=[('5분 시도', '충분', '안 나오면 없는 겁니다', 'clock', 'lilac'),
            ('눕힐 때', '고개 옆으로', '역류에 대비해서', 'alert', 'rose'),
            ('중간에 한 번', '더 좋아요', '먹는 도중에도 시켜주기', 'check', 'mint')]),
 dict(kind='close', eyebrow='기억할 것', title=[['돌 무렵이면'], [('안 해도',), ' 됩니다']],
      lines=['혼자 앉고 움직이면서', '스스로 빠집니다.'],
      noti=('best', 280), noti_y=196),
]

# ─────────────── ⑤ 코막힘 ───────────────
POSTS['nose'] = [
 dict(kind='text', eyebrow='아플 때', top=196, size=70,
      title=[['신생아 코막힘,'], ['집에서 ', ('할 수 있는 것',)]], sub='숨소리가 그렁그렁할 때',
      lines=[], noti=('worry', 380), noti_y=186),
 dict(kind='rows', eyebrow='먼저 알아둘 것', title=[['코가 ', ('원래',)], ['좁아요']],
      rows=[('신생아 콧구멍', '아주 좁음', '조금만 막혀도 소리가 납니다', 'baby', 'sky'),
            ('입으로 숨쉬기', '아직 못함', '그래서 더 힘들어해요', 'alert', 'coral'),
            ('감기 아니어도', '흔함', '건조하면 그렇습니다', 'check', 'mint')]),
 dict(kind='rows', eyebrow='집에서', title=[['이 세 가지면'], [('대부분',), ' 나아져요']],
      rows=[('가습', '40~60%', '건조하면 콧속이 마릅니다', 'house', 'mint'),
            ('식염수', '한두 방울', '굳은 콧물을 불려줍니다', 'bottle', 'sky'),
            ('목욕 후', '수증기', '자연스럽게 풀립니다', 'heart', 'gold')]),
 dict(kind='rows', eyebrow='주의', title=[['흡입기는'], [('살살',), ' 조금만']],
      rows=[('세게 빨기', '@alert', '점막이 부어 더 막힙니다', 'alert', 'rose'),
            ('면봉', '@alert', '더 안으로 밀려 들어가요', 'alert', 'coral'),
            ('하루 여러 번', '@alert', '2~3회면 충분합니다', 'alert', 'lilac')]),
 dict(kind='rows', eyebrow='병원 갈 때', title=[['이러면'], [('바로',), ' 진료']],
      rows=[('먹지를 못함', '@alert', '숨차서 수유가 안 될 때', 'alert', 'rose'),
            ('열이 같이', '@alert', '3개월 미만은 38℃ 이상 즉시', 'alert', 'coral'),
            ('숨소리 이상', '@alert', '쌕쌕거리거나 갈비뼈가 들어감', 'alert', 'gold')]),
 dict(kind='close', eyebrow='기억할 것', title=[['막힌 코보다'], [('아기 상태',), '를 보세요']],
      lines=['잘 먹고 잘 자면 지켜봐도 됩니다.'],
      noti=('love', 280), noti_y=196,
      note='일반적인 안내입니다 · 진단은 소아과에서 받으세요'),
]

# ─────────────── ⑥ 4개월 수면퇴행 ───────────────
POSTS['regress'] = [
 dict(kind='text', eyebrow='재우기', top=196, size=70,
      title=[['잘 자던 아기가'], [('4개월',), '에 깨는 이유']], sub='수면퇴행이 왔습니다',
      lines=[], noti=('sleepy', 380), noti_y=186),
 dict(kind='rows', eyebrow='왜 그러냐면', title=[['잠의 구조가'], [('바뀌어서',), '예요']],
      rows=[('신생아 잠', '단순', '깊은 잠 · 얕은 잠 둘뿐', 'baby', 'lilac'),
            ('4개월부터', '어른처럼', '주기가 여러 단계로 나뉩니다', 'clock', 'sky'),
            ('주기 사이', '잠깐 깸', '스스로 못 자면 완전히 깨요', 'alert', 'coral')]),
 dict(kind='rows', eyebrow='신호', title=[['이러면'], [('퇴행',), ' 맞아요']],
      rows=[('갑자기 자주 깸', '@check', '2시간마다 깨기도 합니다', 'clock', 'lilac'),
            ('낮잠이 짧아짐', '@check', '30~40분에 깨요', 'baby', 'mint'),
            ('안 자려고 함', '@check', '눕히면 웁니다', 'alert', 'rose')]),
 dict(kind='rows', eyebrow='버티는 법', title=[['새 습관을'], [('만들 기회',), '예요']],
      rows=[('졸릴 때 눕히기', '1', '완전히 잠든 뒤 말고', 'check', 'mint'),
            ('잠자리 일정하게', '2', '같은 순서 · 같은 자리', 'house', 'sky'),
            ('낮 활동 늘리기', '3', '햇빛 보면 밤낮이 잡힙니다', 'heart', 'gold')]),
 dict(kind='close', eyebrow='기억할 것', title=[['보통'], [('2~6주',), '면 지나갑니다']],
      lines=['퇴행은 뒤로 가는 게 아니라', '발달하고 있다는 신호예요.', '', '이 시기에 만든 습관이 오래 갑니다.'],
      noti=('love', 280), noti_y=196),
]

if __name__ == '__main__':
    for tag, cards in POSTS.items():
        n = build(tag, cards)
        print(f'{tag} · {n}장')
