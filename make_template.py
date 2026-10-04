"""양정고 정기고사 시험지 양식(양식 복사본.pdf)을 따라 만든 2학년 문학 빈 시험지 양식 PDF 생성기.

사용법:  python3 make_template.py            -> 시험지_양식.pdf
필요:    pip install pymupdf fonttools
글꼴:    gulim.ttc(굴림/굴림체). 학교 로고·꼬리말 엠블럼·이모티콘은 assets/ 의 원본 양식에서 잘라 낸 것을 쓴다.
좌표는 모두 원본 양식 PDF와 같은 pt 단위(왼쪽 위 기준)이다.
"""
import os

import pymupdf
from fontTools.ttLib import TTCollection

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FONT_DIR = os.path.join(HERE, "fonts")

# ── 시험 정보 (필요에 따라 수정) ─────────────────────────────
INFO = {
    "school": "양정고등학교",
    "school_spaced": "양 정 고 등 학 교",
    "grade": "2",
    "subject": "문학",
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


FONTS = font_files()
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
def header(page, info):
    page.insert_image(pymupdf.Rect(46.7, 93.7, 83.3, 128.6),
                      filename=os.path.join(ASSETS, "logo.jpeg"))
    x = 83.3
    for s, size in ((f" {info['grade']}", 20.04), ("학년 ", 15.0), (info["subject"], 21.0),
                    ("과 ", 15.0), (info["exam"], 17.5), (" 문제", 15.0)):
        text(page, x, 123.5, s, size=size, stroke=0.02)
        x += width(s, "Gulim", size)
    text(page, 551.3, 126.6, f"시행일 {info['date']} - {info['period']}", size=6.96,
         anchor="r")
    page.draw_rect(pymupdf.Rect(45.2, 130.0, 561.4, 134.0), color=None, fill=BLACK)
    text(page, 84.2, 142.1,
         f"과 정 : ( {info['course']} )     과목코드 : ( {info['code']} )     "
         f"이수학점 : (  {info['credits']}  )     문항수 ( 선택형: {info['n_choice']}, "
         f"서답형: {info['n_essay']} )")


def frame(page):
    w = 1.08
    line(page, (34.0, 144.1), (34.0, 783.0), w)
    line(page, (561.2, 144.1), (561.2, 783.0), w)
    line(page, (33.5, 144.6), (561.8, 144.6), w)
    line(page, (33.5, 782.4), (561.8, 782.4), w)
    line(page, (297.6, 153.1), (297.6, 770.0), 0.36)  # 단 구분선


def footer(page, info, n, emblem):
    y = 808.2
    text(page, 49.1, y, f"이 시험문제의 저작권은 {info['school']}에 있습니다.", space=NARROW)
    page.show_pdf_page(pymupdf.Rect(244.5, 792.5, 264.2, 811.8), emblem, 0)
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


def last_page_block(page, info, smile):
    text(page, 358.1, 634.3, "수고하셨습니다", size=19.8, space=NARROW)
    page.show_pdf_page(pymupdf.Rect(390, 640, 470, 668), smile, 0)
    text(page, 355.4, 694.8,
         f"선택형 {info['n_choice']:>2}문제 = {info['choice_score']}점", size=13.8,
         space=NARROW)
    text(page, 355.9, 715.6,
         f"서답형 {info['n_essay']:>2}문제 = {info['essay_score']}점", size=13.8,
         space=NARROW)


def main(out="시험지_양식.pdf"):
    info = INFO
    emblem = pymupdf.open(os.path.join(ASSETS, "footer_emblem.pdf"))
    smile = pymupdf.open(os.path.join(ASSETS, "smile.pdf"))
    doc = pymupdf.open()
    for n in range(1, info["pages"] + 1):
        page = doc.new_page(width=595, height=842)
        header(page, info)
        frame(page)
        if n == 1:
            first_page_block(page, info)
        if n == info["pages"]:
            last_page_block(page, info, smile)
        footer(page, info, n, emblem)
    doc.set_metadata({"title": f"{info['grade']}학년 {info['subject']} {info['exam']} 시험지 양식"})
    doc.subset_fonts()
    doc.save(os.path.join(HERE, out), garbage=4, deflate=True)
    print("saved", out)


if __name__ == "__main__":
    main()
