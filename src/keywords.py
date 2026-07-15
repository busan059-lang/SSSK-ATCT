"""정규식 기반 한글 키워드 빈도 추출 (형태소 분석기 미사용, 배포 경량화 목적)."""

import math
import re
from collections import Counter

import numpy as np

_HANGUL_RUN = re.compile(r"[가-힣]{2,}")

# 조사/어미로 끝나는 흔한 패턴 (긴 것부터 매칭되도록 정렬)
_PARTICLE_SUFFIXES = sorted(
    [
        "으로는", "에서는", "한테는", "에게는", "까지는", "이라도", "이지만",
        "이라서", "이라고", "라고는", "으로도", "에서도", "이라면", "한테서",
        "이나마", "이라야", "부터는", "만큼은",
        "이라", "이랑", "이며", "이면", "이지", "이나", "이든", "이야",
        "에서", "에게", "한테", "까지", "부터", "보다", "마저", "조차",
        "이고", "이다", "라서", "라도", "라는", "라며", "라면",
        "은", "는", "이", "가", "을", "를", "의", "에", "도", "만",
        "와", "과", "로", "나", "야", "요",
    ],
    key=len,
    reverse=True,
)

_STOPWORDS = {
    "그리고", "그러나", "하지만", "그래서", "그런데", "그냥", "근데", "진짜",
    "정말", "완전", "너무", "이제", "우리", "이번", "저번", "다시", "한번",
    "조금", "그런", "이런", "저런", "이거", "저거", "그거", "것도", "같은",
    "이렇게", "그렇게", "저렇게", "오늘", "내일", "어제", "지금", "당신",
    "여기", "저기", "거기", "합니다", "습니다", "있습니다", "없습니다",
    "그것", "저것", "이것", "무슨", "어떤", "누가", "누구", "왜냐면",
    "때문", "정도", "얼마나", "아니고", "아니라", "아니면", "그러면",
    "하는데", "하면서", "해서", "해도", "한다", "한다는", "합니다만",
    "삼성전자", "하이닉스", "sk하이닉스", "종목", "게시글", "댓글",
}


def _strip_particle(token: str) -> str:
    for suf in _PARTICLE_SUFFIXES:
        if len(token) > len(suf) + 1 and token.endswith(suf):
            return token[: -len(suf)]
    return token


def extract_keywords(texts, top_n: int = 20, extra_stopwords=None):
    """공백 기준 어절 분리 -> 한글 추출 -> 조사 제거 -> 불용어 필터 -> 빈도 집계."""
    stopwords = _STOPWORDS | set(extra_stopwords or [])
    counter = Counter()

    for text in texts:
        if not isinstance(text, str) or not text:
            continue
        for token in text.split():
            for run in _HANGUL_RUN.findall(token):
                word = _strip_particle(run)
                if len(word) < 2:
                    continue
                if word in stopwords:
                    continue
                counter[word] += 1

    return counter.most_common(top_n)


def _boxes_overlap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def layout_wordcloud(freq_pairs, width: int = 440, height: int = 340, seed: int = 42):
    """워드클라우드 폰트 라이선스/서버 렌더링 문제를 피하기 위한 Plotly 기반 대체 레이아웃.

    matplotlib+wordcloud는 한글 폰트를 서버에 번들링해야 렌더링되지만,
    Plotly는 브라우저(클라이언트)가 폰트를 그리므로 이 문제가 없다.

    ``width``/``height``는 실제로 렌더링될 플롯 영역의 픽셀 크기(차트 크기 - 여백)와
    동일하게 맞춰야 한다. 좌표계를 그 픽셀 크기와 1:1로 맞추고(호출부에서 axis range를
    동일 크기로 고정), 글자 크기(pt)로부터 추정한 사각 영역이 서로 겹치지 않도록
    나선(spiral)을 따라가며 빈 자리를 찾는다 — 값이 클수록(빈도 높을수록) 중심 근처에,
    크게 배치된다.
    """
    if not freq_pairs:
        return []

    rng = np.random.default_rng(seed)
    counts = [c for _, c in freq_pairs]
    max_c, min_c = max(counts), min(counts)

    def size_for(count):
        if max_c == min_c:
            return 30.0
        return 15.0 + (count - min_c) / (max_c - min_c) * 37.0

    half_width_bound = width / 2
    half_height_bound = height / 2
    max_radius = math.hypot(half_width_bound, half_height_bound)

    placed_boxes = []
    points = []
    angle_step = 0.30
    radius_step = 2.4

    for word, count in freq_pairs:
        size = size_for(count)
        found = None

        # 자리를 못 찾으면 글자를 조금씩 줄여가며(최대 6회) 다시 나선 탐색을 시도한다.
        for _ in range(6):
            half_w = size * len(word) * 0.56 + 5
            half_h = size * 0.62 + 5
            if half_w > half_width_bound or half_h > half_height_bound:
                size *= 0.8
                continue

            angle = rng.uniform(0, 2 * math.pi)
            radius = 0.0
            while radius <= max_radius:
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                if abs(x) + half_w <= half_width_bound and abs(y) + half_h <= half_height_bound:
                    box = (x - half_w, y - half_h, x + half_w, y + half_h)
                    if not any(_boxes_overlap(box, placed) for placed in placed_boxes):
                        found = (x, y, box)
                        break
                angle += angle_step
                radius += radius_step * (angle_step / (2 * math.pi))
            if found:
                break
            size *= 0.8

        if found:
            x, y, box = found
            placed_boxes.append(box)
        else:
            # 최후의 수단: 겹침은 감수하되 캔버스 밖으로는 절대 나가지 않게 배치
            half_w = min(size * len(word) * 0.56 + 5, half_width_bound - 1)
            half_h = min(size * 0.62 + 5, half_height_bound - 1)
            x = rng.uniform(-(half_width_bound - half_w), half_width_bound - half_w)
            y = rng.uniform(-(half_height_bound - half_h), half_height_bound - half_h)

        points.append({"word": word, "x": x, "y": y, "size": size, "count": count})

    return points
