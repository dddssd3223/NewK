"""양정고 정기고사 시험지 양식(양식 복사본.pdf)을 따라 만든 2학년 화법과 언어 빈 시험지 양식 PDF 생성기.

사용법:  python3 make_template.py            -> 시험지_양식.pdf
필요:    pip install pymupdf fonttools
글꼴:    gulim.ttc(굴림/굴림체). 학교 로고·꼬리말 엠블럼·이모티콘은 assets/ 의 원본 양식에서 잘라 낸 것을 쓴다.
좌표는 모두 원본 양식 PDF와 같은 pt 단위(왼쪽 위 기준)이다.
"""
import os
import zipfile

import pymupdf
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTCollection, TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FONT_DIR = os.path.join(HERE, "fonts")

# ── 시험 정보 (필요에 따라 수정) ─────────────────────────────
INFO = {
    "school": "양정고등학교",
    "school_spaced": "양 정 고 등 학 교",
    "grade": "2",
    "subject": "화법과 언어",
    "exam": "중간고사",
    "date": "2026년 4월 27일(월)",
    "period": "1교시",
    "course": "2022 개정 교육과정",
    "code": "02",
    "credits": "4",
    "n_choice": 24,
    "n_essay": 6,
    "choice_score": 65,
    "essay_score": 35,
    "pages": 14,
}

NOTICES = [  # (글머리 기호 여부, 줄)
    (True, "아래의 내용을 반드시 읽고 시험에 임하시기 바랍니다!"),
    (True, "휴대폰 등 전자기기는 전원을 꺼 가방 속에 넣어야 "),
    (False, "  합니다."),
    (True, "선택형 답안지에는 반드시 컴퓨터용 사인펜으로 표기해야"),
    (False, "  합니다. 답안을 수정할 경우 답안지를 교체하거나 수정테이 "),
    (False, "  프를 사용하기 바랍니다."),
    (True, "시험지 아래쪽에 적힌 총 쪽수를 참조하여 받은 시험지의"),
    (False, "  매수를 확인하기 바랍니다."),
    (True, "정해진 시험 종료 시각을 확인하여 답안지를 미리 작성하 "),
    (False, "  기 바랍니다."),
]
NOTICE_Y = [175.9, 186.7, 196.9, 207.4, 217.7, 229.2, 241.4, 251.6, 264.7, 274.9]

BLACK = (0, 0, 0)
WHITE = (1, 1, 1)


# ── 글꼴 ────────────────────────────────────────────────────
def font_files():
    os.makedirs(FONT_DIR, exist_ok=True)
    out = {}
    for idx, name in ((0, "Gulim"), (1, "GulimChe")):
        path = os.path.join(FONT_DIR, name + ".ttf")
        if not os.path.exists(path):
            TTCollection(os.path.join(HERE, "gulim.ttc"))[idx].save(path)
        out[name] = path
    return out


def goorm_bold():
    """goorm-sans-all-1.0.0.zip 에서 구름 산스 Bold 를 fonts/ 로 꺼낸다."""
    path = os.path.join(FONT_DIR, "goorm-sans-bold.ttf")
    if not os.path.exists(path):
        with zipfile.ZipFile(os.path.join(HERE, "goorm-sans-all-1.0.0.zip")) as z:
            data = z.read("goorm sans/Public/TTF/goorm-sans-bold.ttf")
        open(path, "wb").write(data)
    return path


FONTS = font_files()
FONTS["Title"] = goorm_bold()  # 제목: 구름 산스 Bold
METRICS = {k: pymupdf.Font(fontfile=v) for k, v in FONTS.items()}


SPACE = 0.5  # 본문 공백 폭(글자 크기 비율). 원본 양식(한글 문서)과 같다.
NARROW = 1 / 3  # 꼬리말·마무리 문구의 공백 폭 (글꼴 기본값)


def width(s, font, size, space=SPACE):
    m = METRICS[font]
    return m.text_length(s.replace(" ", ""), fontsize=size) + s.count(" ") * space * size


def text(page, x, y, s, font="Gulim", size=8.04, anchor="l", stroke=0.025, space=SPACE):
    """(x, y)는 글자 기준선(baseline) 위치.
    원본 양식처럼 채우기+외곽선(render mode 2)으로 그리며, 외곽선 두께는 글자 크기의 비율이다."""
    if anchor == "r":
        x -= width(s, font, size, space)
    elif anchor == "c":
        x -= width(s, font, size, space) / 2
    for i, run in enumerate(s.split(" ")):
        if i:
            x += space * size
        if run:
            page.insert_text((x, y), run, fontname=font, fontfile=FONTS[font],
                             fontsize=size, color=BLACK, fill=BLACK, render_mode=2,
                             border_width=stroke)
            x += width(run, font, size)
    return x


def line(page, p0, p1, w):
    page.draw_line(p0, p1, color=BLACK, width=w)


# ── 공통 틀 ────────────────────────────────────────────────
# 머리글은 원본 문학 시험지(스캔, 144dpi)에 맞춘다. 스캔 좌표(px) -> 양식 좌표(pt):
# 스캔 본문 테두리 왼쪽 77px, 위 277.5px 가 양식의 34pt, 144.6pt 에 오도록 맞춘 배율.
SCAN_K = 527.2 / 1036


def sx(px):
    return 34.0 + (px - 77) * SCAN_K


def sy(py):
    return 144.6 + (py - 277.5) * SCAN_K


_TT = {}


def ink_bounds(s, font):
    """문자열 s 의 첫 글자 왼쪽 잉크 위치와 전체 잉크 아래끝(em 비율)."""
    if font not in _TT:
        t = TTFont(FONTS[font])
        _TT[font] = (t, t.getBestCmap(), t.getGlyphSet(), t["head"].unitsPerEm)
    t, cmap, gs, upm = _TT[font]
    lsb, ymin = None, 0
    for ch in s:
        if ch == " ":
            continue
        pen = BoundsPen(gs)
        gs[cmap[ord(ch)]].draw(pen)
        if pen.bounds:
            if lsb is None:
                lsb = pen.bounds[0] / upm
            ymin = min(ymin, pen.bounds[1] / upm)
    return lsb or 0, ymin


def scan_text(page, s, ink_left_px, ink_bottom_px, size, font, stroke=0.0):
    """글자 잉크의 왼쪽·아래 끝이 스캔의 (ink_left_px, ink_bottom_px)에 오도록 쓴다.
    stroke 는 굵게(외곽선 두께, 글자 크기 비율)."""
    lsb, ymin = ink_bounds(s, font)
    x = sx(ink_left_px) - lsb * size
    y = sy(ink_bottom_px + 0.5) + ymin * size
    kw = dict(fontname=font, fontfile=FONTS[font], fontsize=size, color=BLACK)
    if stroke:
        kw.update(fill=BLACK, render_mode=2, border_width=stroke)
    page.insert_text((x, y), s, **kw)


# 제목: 구름 산스 Bold. 원본 스캔의 글자 높이(약 38px)에 맞춘 크기와 장평(가로 비율).
TITLE_SIZE, TITLE_X = 20.54, 1.055
TITLE_LEFT, TITLE_RIGHT_MAX = 219, 830   # 제목이 들어갈 스캔 x 범위 (오른쪽은 시행일 앞)
TITLE_GAPS = (22, 28, 28, 20)            # 낱말 사이 간격(px): 2|학년|과목|중간고사|문제
SUBJECT_SPACE = 12                       # 과목명 안의 띄어쓰기(px)


def title(page, info):
    """제목: '2 학년  <과목>  중간고사 문제'"""
    m = METRICS["Title"]
    size_px = TITLE_SIZE / SCAN_K
    px = lambda s: m.text_length(s, fontsize=size_px)       # 글자 폭(스캔 px, 장평 전)
    words = [info["grade"], "학년", info["subject"], info["exam"], "문제"]
    total = sum(px(p) * TITLE_X for w in words for p in w.split(" "))
    total += sum(TITLE_GAPS) + SUBJECT_SPACE * (len(info["subject"].split(" ")) - 1)
    lsb = ink_bounds(words[0], "Title")[0] * size_px * TITLE_X
    k = min(1.0, (TITLE_RIGHT_MAX - TITLE_LEFT + lsb) / total)  # 길면 전체를 함께 줄인다
    x = TITLE_LEFT - lsb * k
    y = sy(237.5) + ink_bounds("학", "Title")[1] * TITLE_SIZE
    for i, w in enumerate(words):
        for j, part in enumerate(w.split(" ")):
            if j:
                x += SUBJECT_SPACE * k
            page.insert_text((sx(x), y), part, fontname="Title", fontfile=FONTS["Title"],
                             fontsize=TITLE_SIZE, color=BLACK,
                             morph=(pymupdf.Point(sx(x), y), pymupdf.Matrix(TITLE_X * k, 1)))
            x += px(part) * TITLE_X * k
        if i < len(TITLE_GAPS):
            x += TITLE_GAPS[i] * k


def header(page, info):
    # 학교 로고: 스캔에서 x 132~194px, y 179~241px
    cx, cy = sx(161.5), sy(211.5)
    page.insert_image(pymupdf.Rect(cx - 18.3, cy - 17.45, cx + 18.3, cy + 17.45),
                      filename=os.path.join(ASSETS, "logo.jpeg"))
    title(page, info)
    # 시행일: 굴림체 (스캔 x 863px 부터, 아래끝 245px)
    scan_text(page, f"시행일 {info['date']} - {info['period']}", 863, 245, DATE_SIZE,
              "GulimChe", stroke=DATE_STROKE)
    # 굵은 띠 (스캔 x 101~1123px, y 248~257px)
    page.draw_rect(pymupdf.Rect(sx(101), sy(248), sx(1123.5), sy(257.5)), color=None,
                   fill=BLACK)
    # 과정·과목코드 줄: 굵은 굴림체 — 토큰별 잉크 시작 위치는 스캔에서 잰 값
    for s, px in (("과", 187), ("정", 211), (":", 235), (f"( {info['course'].split()[0]}", 248),
                  ("개정", 306), ("교육과정", 346), (")", 417),
                  ("과목코드", 463), (":", 535), (f"( {info['code']}", 547), (")", 587),
                  ("이수단위", 632), (":", 704), ("(", 717), (info["credits"], 730), (")", 747),
                  ("문항수", 793), ("(", 849), ("선택형:", 863),
                  (f"{info['n_choice']} 서답형:", 923), (str(info["n_essay"]), 1010), (")", 1035)):
        scan_text(page, s, px, 273, META_SIZE, "GulimChe", stroke=META_STROKE)


DATE_SIZE, DATE_STROKE = 14.3 * SCAN_K, 0.04   # 굴림체 1em = 스캔 14.3px
META_SIZE, META_STROKE = 16 * SCAN_K, 0.045    # 굴림체 1em = 스캔 16px


def frame(page):
    w = 1.08
    line(page, (34.0, 144.1), (34.0, 783.0), w)
    line(page, (561.2, 144.1), (561.2, 783.0), w)
    line(page, (33.5, 144.6), (561.8, 144.6), w)
    line(page, (33.5, 782.4), (561.8, 782.4), w)
    line(page, (297.6, 153.1), (297.6, 770.0), 0.36)  # 단 구분선


def footer(page, info, n):
    y = 808.2
    text(page, 49.1, y, f"이 시험문제의 저작권은 {info['school']}에 있습니다.", space=NARROW)
    page.draw_circle((254.25, 802.05), 8.3, color=BLACK, width=0.96)  # 꼬리말 엠블럼
    page.insert_text((254.25 - 5.2, 806.0), "고", fontname="Title", fontfile=FONTS["Title"],
                     fontsize=10.4, color=BLACK)
    text(page, 263.0, y, f"  {info['school_spaced']} <{info['pages']}-{n}>", space=SPACE)
    text(page, 548.8 - NARROW * 8.04, y, "무단 복제 및 전재, 상업적 이용을 금지합니다.",
         anchor="r", space=NARROW)


# ── 쪽별 내용 ──────────────────────────────────────────────
def first_page_block(page, info):
    page.draw_rect(pymupdf.Rect(43.0, 160.6, 291.2, 279.0), color=BLACK, width=0.36)
    page.draw_rect(pymupdf.Rect(126.6, 153.6, 210.1, 167.5), color=None, fill=WHITE)
    text(page, 129.6, 163.4, "<정기고사 준수사항>", font="GulimChe")
    for (bullet, s), y in zip(NOTICES, NOTICE_Y):
        if bullet:
            text(page, 45.7, y, "■ ", size=9.0)
            text(page, 58.2, y, s, size=8.28)
        else:
            text(page, 45.7, y, s, size=8.28)

    text(page, 42.5, 298.2, f"<선택형 문제 – {info['choice_score']}점>", size=11.52)
    text(page, 42.5, 311.0, f"선택형 문제(1~{info['n_choice']})번의 정답은 반드시", size=9.0)
    omr = "OMR카드에 컴퓨터용 사인펜으로 명확히 표기"
    text(page, 42.5, 322.8, omr + "하시오.", size=9.0)
    line(page, (42.5, 324.2), (42.5 + width(omr, "Gulim", 9.0), 324.2), 0.36)
    line(page, (42.5, 331.8), (294.2, 331.8), 1.44)


def last_page_block(page, info, marks):
    text(page, 358.1, 634.3, "수고하셨습니다", size=19.8, space=NARROW)
    page.show_pdf_page(pymupdf.Rect(390, 640, 470, 668), marks, 0)
    text(page, 355.4, 694.8,
         f"선택형 {info['n_choice']:>2}문제 = {info['choice_score']}점", size=13.8,
         space=NARROW)
    text(page, 355.9, 715.6,
         f"서답형 {info['n_essay']:>2}문제 = {info['essay_score']}점", size=13.8,
         space=NARROW)


def main(out="시험지_양식.pdf"):
    info = INFO
    marks = pymupdf.open(os.path.join(ASSETS, "marks.pdf"))  # 마지막 쪽 이모티콘
    doc = pymupdf.open()
    for n in range(1, info["pages"] + 1):
        page = doc.new_page(width=595, height=842)
        header(page, info)
        frame(page)
        if n == 1:
            first_page_block(page, info)
        if n == info["pages"]:
            last_page_block(page, info, marks)
        footer(page, info, n)
    doc.set_metadata({"title": f"{info['grade']}학년 {info['subject']} {info['exam']} 시험지 양식"})
    doc.subset_fonts()
    doc.save(os.path.join(HERE, out), garbage=4, deflate=True)
    print("saved", out)


if __name__ == "__main__":
    main()
