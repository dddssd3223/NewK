"""양정고 정기고사 시험지 양식을 따라 2학년 화법과 언어 객관식 문제(questions.py)를 배치한 시험지 PDF 생성기.

사용법:  python3 make_template.py            -> 시험지_양식.pdf
필요:    pip install pymupdf fonttools
글꼴:    gulim.ttc(굴림/굴림체). 학교 로고·꼬리말 엠블럼·이모티콘은 assets/ 의 원본 양식에서 잘라 낸 것을 쓴다.
좌표는 모두 원본 양식 PDF와 같은 pt 단위(왼쪽 위 기준)이다.
"""
import importlib
import os
import sys
import shutil
import re
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
    "n_choice": 42,       # 문항 수는 questions.py 에서 다시 센다
    "n_essay": 0,
    "choice_score": 100,
    "essay_score": 0,
    "pages": 1,           # 쪽수는 문제를 배치한 뒤 정해진다
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
    for idx, name in ((0, "Gulim"), (1, "GulimChe"), (2, "Dotum")):
        path = os.path.join(FONT_DIR, name + ".ttf")
        if not os.path.exists(path):
            TTCollection(os.path.join(HERE, "gulim.ttc"))[idx].save(path)
        out[name] = path
    body = os.path.join(FONT_DIR, "HCRBatangR.ttf")
    if not os.path.exists(body):
        shutil.copy(os.path.join(HERE, "HCRBatangR.ttf"), body)
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
FONTS["Body"] = os.path.join(FONT_DIR, "HCRBatangR.ttf")  # 본문: 함초롱바탕
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
            kw = dict(fill=BLACK, render_mode=2, border_width=stroke) if stroke else {}
            page.insert_text((x, y), run, fontname=font, fontfile=FONTS[font],
                             fontsize=size, color=BLACK, **kw)
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

    head = f"<선택형 문제 – {info['choice_score']}점>"
    if info.get("mixed"):
        head = f"<선택형 {info['choice_score']}점 · 서답형 {info['essay_score']}점>"
    text(page, 42.5, 298.2, head, size=11.52)
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
    if info["n_essay"]:
        text(page, 355.9, 715.6,
             f"서답형 {info['n_essay']:>2}문제 = {info['essay_score']}점", size=13.8,
             space=NARROW)


def essay_head(page, info, cols, y):
    """서답형 머리글: 1쪽의 선택형 머리글과 같은 모양."""
    x0, x1 = cols
    text(page, x0, y + 11, f"<서답형 문제 – {info['essay_score']}점>", size=11.52)
    text(page, x0, y + 24, "서답형 문제의 답은 반드시 답안지의 해당 칸에", size=9.0)
    text(page, x0, y + 35.5, "검은색 볼펜으로 작성하시오.", size=9.0)
    line(page, (x0, y + 39), (x1, y + 39), 1.44)


# ── 문제 배치 ──────────────────────────────────────────────
# 본문 글꼴은 원본 문학 시험지와 같은 함초롱바탕. 크기 8.05pt 는 스캔의 글자 높이(줄당
# 약 15px)와 줄바꿈 위치가 같아지는 값이고, 줄 간격 12.2pt 는 스캔의 24px 에 맞춘 것이다.
# BODY_STROKE 를 0 보다 크게 하면 문제 글자를 채우기+외곽선으로 진하게 그린다 (기본: 원래 굵기).
BODY_STROKE = 0
CSS = """
@font-face { font-family: W; src: url(HCRBatangR.ttf); }
@font-face { font-family: D; src: url(Dotum.ttf); }
@font-face { font-family: B; src: url(goorm-sans-bold.ttf); }
* { font-family: W; }
.fb { font-family: D; }
body { font-size: 8.05pt; line-height: 12.2pt; text-align: justify; }
p { margin: 0; }
.stem { padding-left: 1.45em; text-indent: -1.45em; margin-bottom: 3pt; }
.c { padding-left: 1.25em; text-indent: -1.25em; }
.c3 { padding-left: 3.1em; text-indent: -3.1em; }
.c4 { padding-left: 1.9em; text-indent: -1.9em; }
.c5 { padding-left: 4.4em; text-indent: -4.4em; }
.ind { padding-left: 2.2em; }
.ar { padding-left: 2.6em; text-indent: -1.3em; }
.gap { margin-top: 4pt; margin-bottom: 4pt; }
.ctr { text-align: center; }
.rt { text-align: right; }
.box { border: 0.6pt solid black; padding: 2pt 5pt 3pt 5pt; margin: 3pt 0 4pt 0; }
.inner { margin: 3pt 0; }
.bt { text-align: center; margin-bottom: 1pt; }
table { border-collapse: collapse; width: 100%; }
td, th { vertical-align: top; padding: 0; text-align: left; font-weight: normal; }
table.g td { padding: 1pt 0; }
table.n td { padding: 0 0 1pt 0; }
table.n td.hd { white-space: nowrap; }
td.br { border-left: 0.6pt solid black; border-top: 0.6pt solid black;
        border-bottom: 0.6pt solid black; }
table.t { margin: 2pt 0; }
table.t td, table.t th { border: 0.6pt solid black; padding: 1.5pt 3pt; vertical-align: middle; }
table.t th { text-align: center; }
table.t td.nb { border: none; }
table.hz td, table.vt td { text-align: center; }
table.hz td.lt { text-align: left; }
table.flow { margin-left: 50pt; }
table.flow td { padding: 1pt 0; }
td.w { width: 70pt; }
td.ar { width: 70pt; padding-left: 1.4em; }
table.flow td.bx { width: 60pt; }
table.mid { margin: 3pt 0; }
.lb { border: 0.6pt solid black; padding: 0 3pt; }
td.bx { border: 0.6pt solid black; padding: 1pt 3pt; }
table.kinds td { text-align: center; vertical-align: middle; }
td.top { border: 0.6pt solid black; padding: 1pt; }
td.hd2 { border: 0.6pt solid black; width: 22%; padding: 1pt; }
td.bd2 { border: 0.6pt solid black; border-top: none; padding: 3pt 2pt; }
td.sp { width: 4%; }
td.dg { font-size: 7pt; line-height: 8.5pt; }
.q18t { font-size: 10pt; vertical-align: middle; padding-left: 8pt; }
table.srch { width: 92%; margin: 2pt 0 6pt 0; }
td.sbox { border: 1.6pt solid #555555; border-right: none; padding: 3pt 6pt; font-size: 10.5pt; }
td.sarr { border: 1.6pt solid #555555; border-left: none; width: 20pt; font-size: 6pt;
          text-align: center; vertical-align: middle; }
td.sgap { width: 4pt; }
td.sbtn { width: 34pt; background-color: #bbbbbb; border: 1.2pt solid #555555; text-align: center;
          vertical-align: middle; font-size: 8.2pt; }
td.badge { width: 34pt; border: 0.8pt solid #777777; text-align: center; font-size: 6.5pt;
           line-height: 1.1; padding: 4pt 0; vertical-align: middle; }
.fig { text-align: center; margin: 2pt 0 4pt 0; }
table.chat { width: 88%; margin: 3pt auto; border: 0.8pt solid #555555; background-color: #f4f4f4; }
table.chat td { padding: 2pt 4pt; }
td.ct { text-align: center; border-bottom: 0.6pt solid #888888; font-size: 7.5pt; }
td.cl { padding-right: 30pt; background-color: #ffffff; border: 0.5pt solid #999999; }
td.cl, td.cr { line-height: 11pt; }
td.cr { text-align: right; background-color: #fff6c8; border: 0.5pt solid #999999; }
td.cs { width: 25%; }
.cw { font-size: 7pt; color: #555555; }
table.sgn { margin: 3pt 0; }
table.sgn td.sg { border: 1.2pt solid black; padding: 4pt; text-align: center; vertical-align: middle; }
table.sec { margin: 2pt 0 4pt 0; }
table.sec td { font-family: B; font-size: 9pt; padding: 0; }
.grp { font-family: B; font-size: 8.6pt; margin-bottom: 3pt; }
table.al { margin-top: 3pt; }
table.al td { border-bottom: 0.5pt solid #888888; padding: 0; line-height: 16pt; }
.cond { border: 0.6pt solid black; padding: 2pt 5pt 3pt 5pt; margin: 3pt 0 2pt 0; }
"""
COLS = ((42.5, 292.0), (302.5, 553.0))      # 왼쪽·오른쪽 단의 x 범위
TOP, TOP1, BOTTOM = 153.0, 338.0, 768.0      # 단의 위·아래 (1쪽 왼쪽 단은 OMR 안내 아래부터)
Q_GAP = 16.0                                 # 문제 사이 간격(pt)
CLOSING_TOP = 610.0                          # 마지막 쪽 '수고하셨습니다' 자리


def question_html(n, stem, body, pts, essay=False):
    # MuPDF 는 표 칸의 % 너비를 무시하므로 단 안쪽 너비(약 240pt) 기준 pt 로 바꾼다
    body = re.sub(r'<(td|th)([^>]*?)width:(\d+)%',
                  lambda m: f"<{m[1]}{m[2]}width:{int(m[3]) * 2.4:.0f}pt", body)
    if essay:  # 서술형: [서술형 n] 발문 (6점)
        html = f'<p class="stem es">[서술형 {n}] {stem} ({pts:g}점)</p>{body}'
    else:
        html = f'<p class="stem">{n}. {stem} ({pts:.1f}점)</p>{body}'
    html = html.replace("&#8199;", "&#160;&#160;")   # 숫자 폭 공백은 본문 글꼴에 없어 공백 두 칸으로
    return fallback(html)


BODY_CMAP = None


def fallback(html):
    """본문 글꼴에 없는 글자가 있으면 돋움으로 쓴다."""
    global BODY_CMAP
    if BODY_CMAP is None:
        BODY_CMAP = set(TTFont(os.path.join(FONT_DIR, "HCRBatangR.ttf")).getBestCmap())
    out, i, intag = [], 0, False
    while i < len(html):
        ch = html[i]
        if ch == "<":
            intag = True
        if intag or ch == "&":
            j = html.find(">" if intag else ";", i)
            out.append(html[i:j + 1])
            intag = False
            i = j + 1
            continue
        nxt = html[i + 1] if i + 1 < len(html) else ""
        if 0x300 <= ord(nxt) <= 0x36F and ord(nxt) not in BODY_CMAP:  # 결합 문자는 앞 글자와 함께
            out.append(f'<span class="fb">{ch}{nxt}</span>')
            i += 2
            continue
        out.append(ch if ord(ch) in BODY_CMAP or ch.isspace() else f'<span class="fb">{ch}</span>')
        i += 1
    return "".join(out)


def archive():
    arc = pymupdf.Archive()
    arc.add(FONT_DIR)
    arc.add(ASSETS)
    return arc


def measure(html, arc):
    """단 너비에서 문제가 차지하는 높이(pt)."""
    w = COLS[0][1] - COLS[0][0]
    doc = pymupdf.open()
    page = doc.new_page(width=w + 20, height=3000)
    spare, scale = page.insert_htmlbox(pymupdf.Rect(0, 0, w, 2990), html, css=CSS, archive=arc)
    return 2990 - spare


ESSAY_HEAD_H = 40.0                          # 서답형 머리글 높이(pt)


def section_html(title):
    return f'<table class="sec"><tr><td>{title}</td></tr></table>'


def layout(questions, pts, arc, essays=(), essay_pts=(), essay_after=None, sections=(), groups=()):
    """문제를 쪽·단에 순서대로 채운다. 반환: [(쪽 번호, 단 번호, y, 높이, html)]
    essay_after 가 없으면 서술형을 맨 뒤에 모으고 첫 서술형 앞에 머리글 자리(html=None)를 둔다.
    essay_after[i] = k 이면 서술형 i+1 을 선택형 k번 바로 뒤에 둔다(0 이면 맨 앞)."""
    choice = [question_html(n, stem, body, pts[n - 1]) for n, (stem, body) in enumerate(questions, 1)]
    essay = [question_html(n, stem, body, essay_pts[n - 1], essay=True)
             for n, (stem, body) in enumerate(essays, 1)]
    if essay_after is None:
        items = [(h, 0.0) for h in choice] + [(h, ESSAY_HEAD_H if i == 0 else 0.0)
                                              for i, h in enumerate(essay)]
    else:
        items = [(essay[i], 0.0) for i, k in enumerate(essay_after) if k == 0]
        seq = [("E", i + 1) for i, k in enumerate(essay_after) if k == 0]
        for n, h in enumerate(choice, 1):
            items.append((h, 0.0))
            seq.append(("Q", n))
            items += [(essay[i], 0.0) for i, k in enumerate(essay_after) if k == n]
            seq += [("E", i + 1) for i, k in enumerate(essay_after) if k == n]
    for start, end in groups:                # 공유 지문 묶음: [1~서답형 1] 처럼 굵게
        name = lambda i: (f"서답형 {seq[i][1]}" if seq[i][0] == "E" else str(seq[i][1]))
        label = f'<p class="grp">[{name(start)}~{name(end)}]</p>'
        html, head = items[start]
        items[start] = (fallback(label) + html, head)
    for idx, title in sections:              # 대제목은 그다음 문항과 한 덩어리로
        if idx < len(items):
            html, head = items[idx]
            items[idx] = (fallback(section_html(title)) + html, head)
    slots, page, col, y = [], 1, 0, TOP1
    for html, head in items:
        h = measure(html, arc) + head
        top = TOP1 if (page, col) == (1, 0) else TOP
        if y + h > BOTTOM and y > top:      # 이 단에 안 들어가면 다음 단으로
            col += 1
            if col == 2:
                page, col = page + 1, 0
            y = TOP
        if head:
            slots.append((page, col, y, head, None))
        slots.append((page, col, y + head, h - head, html))
        y += h + Q_GAP
    # 마지막 쪽 오른쪽 단 아래에 마무리 문구가 들어갈 자리가 없으면 한 쪽 더
    last_page = page
    if col == 1 and y > CLOSING_TOP:
        last_page += 1
    return slots, last_page


def thicken_question_text(doc):
    """문제 블록(insert_htmlbox 가 만든 Form XObject)의 글자를 채우기+외곽선으로 바꾼다."""
    done = set()
    for page in doc:
        for xref, name, *_ in page.get_xobjects():
            if name != "fullpage" or xref in done:
                continue
            done.add(xref)
            stream = doc.xref_stream(xref)
            stream = re.sub(rb"\bBT\b", b"BT 2 Tr %.2f w 0 0 0 RG" % BODY_STROKE, stream)
            doc.update_stream(xref, stream)


# ── 9번 그림: 원본 그림을 그대로 다시 그린다 (좌표는 원본 그림 957×771px 기준) ──
Q09_BOXES = [((30, 12, 255, 268), ("① ㅎ : 마", "찰음이자", "목청소리이", "다.")),
             ((315, 15, 540, 270), ("② ㅈ : 파", "찰음이자", "안울림소리", "이다.")),
             ((658, 18, 893, 275), ("③ ㅊ : 거", "센소리이자", "센입천장소", "리이다.")),
             ((165, 495, 390, 752), ("④ ㄴ : 비", "음이자 입", "술소리이", "다.")),
             ((630, 505, 880, 755), ("⑤ ㅇ : 울", "림소리이자", "여린입천장", "소리이다."))]
Q09_JAMO = [("ㅎ", 165, 325, True), ("ㅁ", 258, 325, False), ("ㅣ", 298, 325, False),
            ("ㅈ", 345, 325, True), ("ㅓ", 377, 325, False), ("ㅇ", 445, 325, False),
            ("ㅜ", 160, 383, False), ("ㄴ", 258, 383, True), ("ㅇ", 355, 383, False),
            ("ㅡ", 445, 383, False), ("ㄴ", 160, 432, False), ("ㅁ", 445, 432, False),
            ("ㅊ", 660, 325, True), ("ㅏ", 692, 325, False), ("ㅈ", 752, 325, False),
            ("ㅔ", 790, 325, False), ("ㅇ", 668, 383, True)]
Q09_ARROWS = [((140, 315), (95, 290)), ((370, 310), (402, 290)), ((685, 310), (712, 293)),
              ((258, 405), (258, 475)), ((668, 405), (668, 485))]


def draw_q09(page, rect):
    k = rect.width / 957
    P = lambda x, y: pymupdf.Point(rect.x0 + x * k, rect.y0 + y * k)
    size, font = 8.5, "Body"
    page.draw_rect(pymupdf.Rect(P(0, 0), P(957, 771)), color=BLACK, width=0.6)
    for (x0, y0, x1, y1), rows in Q09_BOXES:
        page.draw_rect(pymupdf.Rect(P(x0, y0), P(x1, y1)), color=BLACK, width=0.8)
        lead = (y1 - y0) * k / 4
        for i, row in enumerate(rows):
            y = rect.y0 + y0 * k + lead * (i + 0.72)
            left, right = rect.x0 + (x0 + 14) * k, rect.x0 + (x1 - 12) * k
            chars = list(row)
            if i == len(rows) - 1 or len(chars) < 2:   # 마지막 줄은 왼쪽 정렬
                text(page, left, y, row, font=font, size=size, stroke=0)
                continue
            # 원본처럼 글자를 칸 너비에 고르게 벌린다
            widths = [width(c, font, size) for c in chars]
            gap = (right - left - sum(widths)) / (len(chars) - 1)
            x = left
            for c, w in zip(chars, widths):
                if c != " ":
                    text(page, x, y, c, font=font, size=size, stroke=0)
                x += w + gap
    for ch, cx, cy, circled in Q09_JAMO:
        c = P(cx, cy)
        text(page, c.x, c.y + 3.0, ch, font=font, size=8.2, anchor="c", stroke=0)
        if circled:
            page.draw_circle(c, 18 * k, color=BLACK, width=0.5, dashes="[1 1] 0")
    for (ax, ay), (bx, by) in Q09_ARROWS:
        a, b = P(ax, ay), P(bx, by)
        page.draw_line(a, b, color=BLACK, width=0.5, dashes="[1 1] 0")
        d = (b - a) / abs(b - a)
        n = pymupdf.Point(-d.y, d.x)
        tip = b
        page.draw_polyline([tip, tip - d * 5 + n * 2.2, tip - d * 5 - n * 2.2, tip],
                           color=BLACK, fill=BLACK, width=0.3)


FIGURES = {"q09": draw_q09}


def main(out="시험지_양식.pdf", qmod="questions"):
    mod = importlib.import_module(qmod)
    PTS, Q = mod.PTS, mod.Q
    ES, EP = getattr(mod, "ESSAY", []), getattr(mod, "ESSAY_PTS", [])
    info = dict(INFO, n_choice=len(Q), choice_score=f"{sum(PTS):g}",
                n_essay=len(ES), essay_score=f"{sum(EP):g}",
                mixed=getattr(mod, "ESSAY_AFTER", None) is not None)
    arc = archive()
    slots, n_pages = layout(Q, PTS, arc, ES, EP, getattr(mod, "ESSAY_AFTER", None),
                            getattr(mod, "SECTIONS", ()), getattr(mod, "GROUPS", ()))
    info["pages"] = n_pages
    marks = pymupdf.open(os.path.join(ASSETS, "marks.pdf"))  # 마지막 쪽 이모티콘
    doc = pymupdf.open()
    for n in range(1, n_pages + 1):
        page = doc.new_page(width=595, height=842)
        header(page, info)
        frame(page)
        if n == 1:
            first_page_block(page, info)
        for pg, col, y, h, html in slots:
            if pg == n and html is None:
                essay_head(page, info, COLS[col], y)
            elif pg == n:
                x0, x1 = COLS[col]
                page.insert_htmlbox(pymupdf.Rect(x0, y, x1, y + h + 2), html, css=CSS,
                                    archive=arc)
                for name, draw in FIGURES.items():
                    m = re.search(rf'class="fig-{name}" style="height:(\d+)pt"', html)
                    if m:  # 그림 자리는 문제의 맨 끝에 있다
                        fh = float(m[1])
                        draw(page, pymupdf.Rect(x0, y + h - fh, x1, y + h))
        if n == n_pages:
            last_page_block(page, info, marks)
        footer(page, info, n)
    if BODY_STROKE:
        thicken_question_text(doc)
    doc.set_metadata({"title": f"{info['grade']}학년 {info['subject']} {info['exam']} 시험지"})
    doc.subset_fonts()
    doc.save(os.path.join(HERE, out), garbage=4, deflate=True)
    print("saved", out, n_pages, "pages,", len(Q), "questions")


if __name__ == "__main__":
    # python3 make_template.py [문항 모듈] [출력 파일]  예) mock1_questions 실전1회_문제지.pdf
    main(*(sys.argv[2:3] or ["시험지_양식.pdf"]), *(sys.argv[1:2] or ["questions"]))
