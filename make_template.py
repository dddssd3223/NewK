"""2026학년도 1학기 중간고사 2학년 문학 시험지를 바탕으로 한 빈 시험지 양식 PDF 생성기.

사용법:  python3 make_template.py            -> 시험지_양식.pdf
글꼴은 저장소의 한컴폰트.vol*.egg(분할 EGG)에서 한컴바탕/한컴돋움을 자동으로 풀어 쓴다.
"""
import glob
import os
import struct
import zlib

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

# ── 시험 정보 (필요에 따라 수정) ─────────────────────────────
INFO = {
    "school": "양정고등학교",
    "grade": "2",
    "subject": "문 학",
    "subject_plain": "문학",
    "exam": "중간고사",
    "date": "2026년 4월 27일(월)",
    "period": "1교시",
    "course": "2022 개정 교육과정",
    "course_short": ("2022", "개정"),
    "code": "02",
    "units": "4",
    "n_choice": 24,
    "n_essay": 6,
    "choice_score": "",   # 선택형 점수 합계 (예: 65)
    "essay_score": "",    # 서술형 점수 합계 (예: 35)
    "pages": 14,          # 문제지 쪽수
}

NOTICES = [
    "아래의 내용을 반드시 읽고 시험에 임하시기 바랍니다!",
    "휴대폰 등 전자기기는 전원을 꺼 가방 속에 넣어야 합니다.",
    "선택형 답안지에는 반드시 컴퓨터용 사인펜으로 표기해야 합니다. "
    "보조표기를 할 경우, 빨간색 이외의 펜을 사용하면 오답으로 처리될 수 있습니다. "
    "답안을 수정할 경우, 답안지를 교체하거나 수정테이프를 사용하기 바랍니다.",
    "시험지 아래쪽에 적힌 총 쪽수를 참조하여 받은 시험지의 매수를 확인하기 바랍니다.",
    "정해진 시험 종료 시각을 확인하여 답안지를 미리 작성하기 바랍니다.",
]


# ── 글꼴 ────────────────────────────────────────────────────
def extract_egg_fonts():
    """분할 EGG(한컴폰트.vol*.egg)에서 TTF를 풀어 fonts/ 에 저장한다 (deflate/저장 방식만 지원)."""
    vols = sorted(glob.glob(os.path.join(HERE, "*.vol*.egg")))
    if not vols:
        return
    data = open(vols[0], "rb").read()
    for v in vols[1:]:
        d = open(v, "rb").read()
        data += d[33:]  # 각 볼륨의 EGG 헤더 + 분할 헤더(33바이트) 제거
    os.makedirs(FONT_DIR, exist_ok=True)
    pos = 0
    while True:
        j = data.find(b"\xe3\x90\x85\x0a", pos)  # 파일 헤더
        if j < 0:
            break
        k = data.find(b"\xac\x91\x85\x0a", j)  # 파일명 헤더
        ln = struct.unpack("<H", data[k + 5:k + 7])[0]
        name = data[k + 7:k + 7 + ln].decode("utf-8", "replace")
        b = data.find(b"\x13\x0c\xb5\x02", k)  # 블록 헤더
        method = data[b + 4]
        usz, csz = struct.unpack("<II", data[b + 6:b + 14])
        comp = data[b + 22:b + 22 + csz]
        pos = b + 22 + csz
        if method == 0:
            out = comp
        elif method == 1:
            out = zlib.decompress(comp, -15)
        else:
            continue
        if len(out) == usz:
            open(os.path.join(FONT_DIR, name), "wb").write(out)


def register_fonts():
    need = [os.path.join(FONT_DIR, f) for f in ("HBATANG.TTF", "HDOTUM.TTF")]
    if not all(os.path.exists(p) for p in need):
        extract_egg_fonts()
    pdfmetrics.registerFont(TTFont("Batang", need[0]))
    pdfmetrics.registerFont(TTFont("Dotum", need[1]))
    gulim = os.path.join(HERE, "gulim.ttc")
    if os.path.exists(gulim):
        pdfmetrics.registerFont(TTFont("Gulim", gulim, subfontIndex=0))


# ── 그리기 도우미 ───────────────────────────────────────────
W, H = A4
PX = 0.5  # 원본 스캔(144dpi) 1px = 0.5pt


def Y(px):
    """스캔 상단 기준 픽셀 좌표 -> PDF y 좌표."""
    return H - px * PX


def text(c, x, y, s, font="Dotum", size=10, bold=False, anchor="l", fill=0):
    c.saveState()
    c.setFillGray(fill)
    t = c.beginText()
    t.setFont(font, size)
    if bold:  # 가짜 굵게: 채우기 + 외곽선
        t.setTextRenderMode(2)
        c.setStrokeGray(fill)
        c.setLineWidth(size * 0.035)
    w = pdfmetrics.stringWidth(s, font, size)
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    t.setTextOrigin(x, y)
    t.textOut(s)
    c.drawText(t)
    c.restoreState()
    return w


def wrap(s, font, size, width):
    lines, cur = [], ""
    for ch in s:
        if pdfmetrics.stringWidth(cur + ch, font, size) > width:
            if ch == " ":
                lines.append(cur)
                cur = ""
                continue
            # 단어 단위로 끊기
            sp = cur.rfind(" ")
            if sp > 0:
                lines.append(cur[:sp])
                cur = cur[sp + 1:] + ch
            else:
                lines.append(cur)
                cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def emblem(c, cx, cy, r, ch, size):
    c.saveState()
    c.setLineWidth(r * 0.13)
    c.circle(cx, cy, r)
    c.setLineWidth(r * 0.05)
    c.circle(cx, cy, r * 0.78)
    c.restoreState()
    text(c, cx, cy - size * 0.36, ch, "Batang", size, bold=True, anchor="c")


# ── 문제지 ──────────────────────────────────────────────────
BOX_L, BOX_R = 77, 1113          # 본문 테두리 (px)
BOX_T, BOX_B = 282, 1545
MID = (BOX_L + BOX_R) / 2


def header(c, info):
    emblem(c, 165 * PX, Y(210), 15.5, "高", 17)
    title = f"{info['grade']} 학년  {info['subject']}  {info['exam']} 문제"
    size = min(27, 262 / pdfmetrics.stringWidth(title, "Dotum", 1))
    text(c, 218 * PX, Y(236), title, "Dotum", size, bold=True)
    text(c, 1105 * PX, Y(240), f"시행일 {info['date']} - {info['period']}",
         "Dotum", 9.5, anchor="r")
    # 굵은 띠
    c.setLineWidth(2.6)
    c.line(BOX_L * PX + 14, Y(252), BOX_R * PX, Y(252))
    meta = (f"과 정 : ( {info['course']} )      과목코드 : ( {info['code']} )      "
            f"이수단위 : ( {info['units']} )      문항수 ( 선택형: {info['n_choice']}  "
            f"서답형: {info['n_essay']} )")
    text(c, MID * PX, Y(272), meta, "Dotum", 9.5, bold=True, anchor="c")


def body_frame(c):
    c.setLineWidth(1.4)
    c.rect(BOX_L * PX, Y(BOX_B), (BOX_R - BOX_L) * PX, (BOX_B - BOX_T) * PX)
    c.setLineWidth(0.6)
    for dx in (-1.6, 1.6):
        c.line(MID * PX + dx, Y(BOX_T + 8), MID * PX + dx, Y(BOX_B - 8))


def footer(c, info, n):
    y = Y(1597)
    parts = (f"이 시험문제의 저작권은 {info['school']}에 있습니다.",
             f"{info['school']}<{info['pages']}- {info['pages']}>",
             "무단 복제 및 전재, 상업적 이용을 금지합니다.")
    total = sum(pdfmetrics.stringWidth(t, "Dotum", 1) for t in parts)
    sz = min(10, (997 * PX - 20 - 50) / total)  # 엠블럼 20pt + 여백 2x25pt
    w1 = text(c, 108 * PX, y, f"이 시험문제의 저작권은 {info['school']}에 있습니다.",
              "Dotum", sz, bold=True)
    w3 = pdfmetrics.stringWidth("무단 복제 및 전재, 상업적 이용을 금지합니다.", "Dotum", sz)
    mid = f"{info['school']}<{info['pages']}- {n}>"
    wm = pdfmetrics.stringWidth(mid, "Dotum", sz) + 20  # 엠블럼 포함
    gap_l, gap_r = 108 * PX + w1, 1105 * PX - w3
    mx = (gap_l + gap_r - wm) / 2
    emblem(c, mx + 8, y + 3, 8, "고", 9)
    text(c, mx + 20, y, mid, "Dotum", sz, bold=True)
    text(c, 1105 * PX, y, "무단 복제 및 전재, 상업적 이용을 금지합니다.",
         "Dotum", sz, bold=True, anchor="r")


def notice_block(c, info):
    x0, x1 = 100 * PX, 585 * PX
    top = Y(312)
    title = "<정기고사 준수사항>"
    tw = pdfmetrics.stringWidth(title, "Dotum", 11)
    cx = (x0 + x1) / 2
    c.setLineWidth(0.8)
    c.line(x0, top, cx - tw / 2 - 4, top)
    c.line(cx + tw / 2 + 4, top, x1, top)
    text(c, cx, top - 3.8, title, "Dotum", 11, anchor="c")

    size, lead = 10, 13.8
    tx = x0 + 20
    y = top - 18
    for s in NOTICES:
        c.rect(x0 + 6, y - 0.5, 8, 8, fill=1, stroke=0)
        for ln in wrap(s, "Dotum", size, x1 - tx - 6):
            text(c, tx, y, ln, "Dotum", size, bold=True)
            y -= lead
    bot = y + lead - 7
    c.line(x0, top, x0, bot)
    c.line(x1, top, x1, bot)
    c.line(x0, bot, x1, bot)

    omr = "OMR카드에 컴퓨터용 사인펜으로 명확히 표기하시오."
    osz = min(12, (MID - 92 - 12) * PX / pdfmetrics.stringWidth(omr, "Dotum", 1))
    y = bot - 22
    text(c, 92 * PX, y, f"선택형 문제(1~{info['n_choice']}번)의 정답은 반드시",
         "Dotum", osz)
    y -= osz + 4
    w = text(c, 92 * PX, y, omr, "Dotum", osz)
    c.setLineWidth(0.7)
    c.line(92 * PX, y - 2.5, 92 * PX + w, y - 2.5)
    c.setLineWidth(1.4)
    c.line(BOX_L * PX, y - 13, MID * PX - 1.6, y - 13)


def exam_pages(c, info):
    for n in range(1, info["pages"] + 1):
        header(c, info)
        body_frame(c)
        if n == 1:
            notice_block(c, info)
        if n == info["pages"]:
            text(c, (MID + BOX_R) / 2 * PX, Y(1290), "- 끝 -", "Dotum", 14,
                 bold=True, anchor="c")
        footer(c, info, n)
        c.showPage()


# ── 정답표 ──────────────────────────────────────────────────
def answer_key(c, info):
    text(c, 228 * PX, Y(190), f"{info['grade']}학년 ({info['subject_plain']})", "Batang", 13)
    c.setDash(1, 1.5)
    c.setLineWidth(0.8)
    c.line(225 * PX, Y(203), 450 * PX, Y(203))
    c.setDash()
    text(c, 110 * PX, Y(242), "시험일자", "Batang", 10)
    text(c, 210 * PX, Y(242), info["date"].split("(")[0], "Batang", 10)

    L, R = 98 * PX, 1082 * PX
    top, mid, bot = Y(300), Y(370), Y(428)
    row2 = Y(400)
    meta_cols = [("학\n년", 32), ("과정", 46), ("과목\n코드", 32), ("과목명", 52),
                 ("이수\n단위", 34), ("문항\n수", 34), ("선택\n형\n점수", 34),
                 ("서술\n형\n점수", 34)]
    xs = [L]
    for _, w in meta_cols:
        xs.append(xs[-1] + w * PX)
    gx = xs[-1] + 36 * PX           # 구분 열 끝
    n = info["n_choice"]
    cw = (R - gx) / n

    c.setFillColorRGB(0.85, 0.87, 0.93)
    c.rect(L, mid, R - L, top - mid, fill=1, stroke=0)
    c.rect(xs[-1], bot, gx - xs[-1], mid - bot, fill=1, stroke=0)
    c.setFillGray(0)

    c.setLineWidth(1.6)
    c.rect(L, bot, R - L, top - bot)
    c.setLineWidth(0.6)
    c.line(L, mid, R, mid)
    for x in xs[1:]:
        c.line(x, top, x, bot)
    c.line(xs[-1], row2, R, row2)
    c.setDash(1, 1.2)
    for i in range(1, n):
        c.line(gx + i * cw, top, gx + i * cw, bot)
    c.setDash()
    c.line(xs[-1], top, gx, mid)  # 대각선 (구분/번호)
    text(c, gx - 2, top - 9, "번호", "Batang", 6, anchor="r")
    text(c, xs[-1] + 2, mid + 4, "구분", "Batang", 6)
    text(c, (xs[-1] + gx) / 2, (mid + row2) / 2 - 3, "배점", "Batang", 8, anchor="c")
    text(c, (xs[-1] + gx) / 2, (row2 + bot) / 2 - 3, "정답", "Batang", 8, anchor="c")
    for i in range(n):
        text(c, gx + (i + 0.5) * cw, (top + mid) / 2 - 3, str(i + 1), "Batang", 8, anchor="c")

    vals = [info["grade"], "\n".join(info["course_short"]), info["code"],
            info["subject_plain"], info["units"], f"{n}\n{info['n_essay']}",
            str(info["choice_score"]), str(info["essay_score"])]
    for i, (lab, _) in enumerate(meta_cols):
        cx = (xs[i] + xs[i + 1]) / 2
        for k, (txt, y0, y1) in enumerate(((lab, top, mid), (vals[i], mid, bot))):
            parts = txt.split("\n")
            sz = 8 if k == 0 else 9
            h = len(parts) * (sz + 1)
            y = (y0 + y1) / 2 + h / 2 - sz + 1
            for p in parts:
                text(c, cx, y, p, "Batang", sz, anchor="c")
                y -= sz + 1

    # 서답형 정답 칸
    lab_r = 172 * PX
    y = bot
    rh = (bot - Y(1365)) / info["n_essay"]
    c.setLineWidth(1.6)
    c.rect(L - 4 * PX, Y(1365), R - L + 4 * PX, bot - Y(1365))
    c.setLineWidth(0.8)
    c.line(lab_r, bot, lab_r, Y(1365))
    for i in range(info["n_essay"]):
        yb = y - rh
        if i < info["n_essay"] - 1:
            c.line(L - 4 * PX, yb, R, yb)
        cx = (L + lab_r) / 2
        text(c, cx, (y + yb) / 2 + 3, "서답형", "Batang", 10, anchor="c")
        text(c, cx, (y + yb) / 2 - 10, str(i + 1), "Batang", 10, anchor="c")
        y = yb
    c.showPage()


def main(out="시험지_양식.pdf"):
    register_fonts()
    c = canvas.Canvas(os.path.join(HERE, out), pagesize=A4)
    c.setTitle(f"{INFO['grade']}학년 {INFO['subject_plain']} {INFO['exam']} 시험지 양식")
    exam_pages(c, INFO)
    answer_key(c, INFO)
    c.save()
    print("saved", out)


if __name__ == "__main__":
    main()
