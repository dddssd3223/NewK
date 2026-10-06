"""OMR 답안지(A4 가로, 굴림체)를 회차별로 만든다.

사용법: python3 make_omr.py mock7_questions 실전7회_OMR.pdf "실전 7회"
       python3 make_omr.py - OMR_45문항.pdf "" 45      (문항 모듈 없이 문항 수만)
왼쪽: 학교·시험명, 성명, 학년·반·번호·과목코드 마킹, 감독 확인, 유의사항
오른쪽: 선택형 답란(문항 수만큼, 열당 15문항)
"""
import importlib
import os
import sys

import pymupdf

from make_template import FONTS, HERE, INFO

W, H = 841.89, 595.28                  # A4 가로
INK = (0.84, 0.16, 0.33)               # OMR 카드 인쇄색(붉은 계열)
TINT = (1.0, 0.93, 0.95)
BLACK = (0, 0, 0)
M = 22.0                               # 바깥 여백
F = "Gulim"


def width(s, size):
    return pymupdf.Font(fontfile=FONTS[F]).text_length(s, fontsize=size)


def put(page, x, y, s, size=8, anchor="l", color=INK, spacing=0.0):
    """spacing>0 이면 글자 사이를 벌린다."""
    if spacing:
        tw = sum(width(c, size) for c in s) + spacing * (len(s) - 1)
        x = x - tw / 2 if anchor == "c" else x - tw if anchor == "r" else x
        for c in s:
            page.insert_text((x, y), c, fontname=F, fontfile=FONTS[F], fontsize=size, color=color)
            x += width(c, size) + spacing
        return
    w = width(s, size)
    x = x - w / 2 if anchor == "c" else x - w if anchor == "r" else x
    page.insert_text((x, y), s, fontname=F, fontfile=FONTS[F], fontsize=size, color=color)


def rect(page, r, w=0.7, fill=None, color=INK):
    page.draw_rect(r, color=color, fill=fill, width=w)


def bubble(page, cx, cy, label, bw=8.4, bh=11.5):
    """세로로 긴 타원 마킹 칸 + 안의 숫자."""
    page.draw_oval(pymupdf.Rect(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), color=INK, width=0.6)
    put(page, cx, cy + 2.4, label, 6.3, "c")


def digit_column(page, x, y, n_digits, title, fixed=None, cw=15.0, row=13.2):
    """번호 등 마킹 칸: 제목, 손글씨 칸, 자리마다 0~9 타원. fixed 가 있으면 미리 써 넣는다."""
    wtot = cw * n_digits
    rect(page, pymupdf.Rect(x, y, x + wtot, y + 15), fill=TINT)
    put(page, x + wtot / 2, y + 10.5, title, 7.5, "c")
    for d in range(n_digits):
        r = pymupdf.Rect(x + cw * d, y + 15, x + cw * (d + 1), y + 33)
        rect(page, r)
        if fixed and len(fixed) == n_digits:        # 자리 수가 맞을 때만 미리 써 넣는다
            put(page, (r.x0 + r.x1) / 2, r.y1 - 5, fixed[d], 10, "c", BLACK)
    body = pymupdf.Rect(x, y + 33, x + wtot, y + 33 + row * 10 + 4)
    rect(page, body)
    for d in range(n_digits):
        if d:
            page.draw_line((x + cw * d, body.y0), (x + cw * d, body.y1), color=INK, width=0.4)
        for k in range(10):
            bubble(page, x + cw * d + cw / 2, body.y0 + 2 + row * k + row / 2, str(k))
    return body.y1


def left_panel(page, label, x0, x1):
    y = M
    # 학교명·시험명
    put(page, (x0 + x1) / 2, y + 23, INFO["school"], 20, "c", INK, spacing=9)
    put(page, (x0 + x1) / 2, y + 40, f"2026학년도 1학기 {INFO['exam']} 답안지", 9.5, "c")
    sub = f"{INFO['grade']}학년  {INFO['subject']}" + (f"  ·  {label}" if label else "")
    put(page, (x0 + x1) / 2, y + 54, sub, 8.5, "c")
    y += 62
    # 성명 / 감독 확인
    hw = 46
    for name, h in (("성  명", 24), ("감독 확인\n(서명)", 28)):
        r1 = pymupdf.Rect(x0, y, x0 + hw, y + h)
        rect(page, r1, fill=TINT)
        lines = name.split("\n")
        for i, t in enumerate(lines):
            put(page, (r1.x0 + r1.x1) / 2, r1.y0 + h / 2 + 3 - 4.5 * (len(lines) - 1) + 9 * i, t, 7.5, "c")
        rect(page, pymupdf.Rect(x0 + hw, y, x1, y + h))
        y += h
    y += 8
    # 학년·반·번호·과목코드 마킹
    cols = [(1, "학년", INFO["grade"]), (2, "반", None), (2, "번호", None), (2, "과목코드", INFO["code"])]
    cws = [max(15.0, 40.0 / n) for n, _, _ in cols]       # 한 자리 칸도 제목이 들어가게
    gap = (x1 - x0 - sum(n * c for (n, _, _), c in zip(cols, cws))) / (len(cols) - 1)
    x = x0
    bottom = y
    for (n, title, fixed), cw in zip(cols, cws):
        bottom = digit_column(page, x, y, n, title, fixed, cw)
        x += n * cw + gap
    y = bottom + 10
    # 유의사항
    notes = ["※ 수험생 유의사항",
             "1. 컴퓨터용 사인펜만 사용하여 해당란에 ‘●’와 같이",
             "   완전하게 표기하시오.",
             "2. 학년·반·번호는 숫자로 쓰고 해당란에 표기하시오.",
             "3. 답안을 수정할 때에는 답안지를 교체하거나",
             "   수정테이프를 사용하시오.",
             "4. 답안지를 접거나 구기지 마시오."]
    r = pymupdf.Rect(x0, y, x1, H - M - 14)
    rect(page, r)
    for i, t in enumerate(notes):
        put(page, x0 + 6, y + 13 + 11.5 * i, t, 7.3, color=BLACK if i else INK)
    put(page, x0 + 6, r.y1 - 26, "바른 표기 :", 7.3, color=BLACK)
    page.draw_oval(pymupdf.Rect(x0 + 50, r.y1 - 33, x0 + 58.4, r.y1 - 21.5), color=BLACK, fill=BLACK, width=0.6)
    put(page, x0 + 66, r.y1 - 26, "틀린 표기 :", 7.3, color=BLACK)
    cy = r.y1 - 27.25
    for k in range(4):                                     # ✓, ×, 점, 반쯤 칠한 것
        cx = x0 + 114 + 14 * k
        page.draw_oval(pymupdf.Rect(cx - 4.2, cy - 5.75, cx + 4.2, cy + 5.75), color=INK, width=0.6)
        if k == 0:
            page.draw_polyline([(cx - 3, cy), (cx - 0.8, cy + 3), (cx + 3.2, cy - 4)], color=BLACK, width=0.9)
        elif k == 1:
            page.draw_line((cx - 2.6, cy - 3.2), (cx + 2.6, cy + 3.2), color=BLACK, width=0.9)
            page.draw_line((cx - 2.6, cy + 3.2), (cx + 2.6, cy - 3.2), color=BLACK, width=0.9)
        elif k == 2:
            page.draw_circle((cx, cy), 1.3, color=None, fill=BLACK)
        else:
            page.draw_rect(pymupdf.Rect(cx - 3.2, cy, cx + 3.2, cy + 4.6), color=None, fill=BLACK)
    put(page, x0 + 6, r.y1 - 10, "※ 서답형은 별도의 서답형 답안지에 작성하시오.", 7.3, color=BLACK)


def answer_panel(page, n, x0, x1, per_col=None):
    """선택형 답란: 번호 칸 + ①~⑤ 타원. 다섯 문항마다 굵은 구분선."""
    y0 = M
    top = y0 + 22
    rect(page, pymupdf.Rect(x0, y0, x1, top), fill=TINT, w=0.9)
    put(page, (x0 + x1) / 2, y0 + 15, f"선  택  형    답  란   (1 ~ {n}번)", 10, "c")
    if per_col is None:                     # 많으면 한 열에 더 넣는다(최대 6열)
        per_col = 15 if n <= 45 else max(20, -(-n // 6))
    ncol = max(3, -(-n // per_col))
    colw = (x1 - x0) / ncol
    row = (H - M - 14 - top - 22) / per_col
    for c in range(ncol):
        cx0 = x0 + colw * c
        # 머리: 문번 | 답 란
        hdr = pymupdf.Rect(cx0, top, cx0 + colw, top + 22)
        rect(page, hdr, fill=TINT)
        nw = 30.0
        page.draw_line((cx0 + nw, top), (cx0 + nw, H - M - 14), color=INK, width=0.6)
        put(page, cx0 + nw / 2, top + 14, "문번", 7.5, "c")
        put(page, cx0 + nw + (colw - nw) / 2, top + 14, "답      란", 7.5, "c")
        body = pymupdf.Rect(cx0, top + 22, cx0 + colw, H - M - 14)
        rect(page, body, w=0.9)
        for k in range(per_col):
            q = c * per_col + k + 1
            yy = body.y0 + row * k
            if k and k % 5 == 0:
                page.draw_line((cx0, yy), (cx0 + colw, yy), color=INK, width=0.9)
            elif k:
                page.draw_line((cx0, yy), (cx0 + colw, yy), color=INK, width=0.25)
            if q > n:
                continue
            if (k // 5) % 2 == 1:
                page.draw_rect(pymupdf.Rect(cx0 + 0.5, yy + 0.3, cx0 + nw - 0.3, yy + row - 0.3), color=None,
                               fill=TINT)
            put(page, cx0 + nw / 2, yy + row / 2 + 3.3, str(q), 9, "c", BLACK)
            span = colw - nw
            for b in range(5):
                bw = min(10.5, span / 5 * 0.72)
                bubble(page, cx0 + nw + span * (b + 0.5) / 5, yy + row / 2, str(b + 1), bw, min(14, row * 0.72))
    # 아래 타이밍 마크(판독기 기준선)
    for k in range(per_col):
        yy = top + 22 + row * k + row / 2
        page.draw_rect(pymupdf.Rect(W - M + 6, yy - 2.2, W - M + 16, yy + 2.2), color=None, fill=BLACK)


def main(qmod, out, label="", n=None):
    if qmod != "-":
        mod = importlib.import_module(qmod)
        INFO.update(getattr(mod, "INFO", {}))   # 과목명 등 문항 모듈이 덮어쓸 수 있다
        n = len(mod.Q)
    n = int(n)
    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    split = M + 236
    left_panel(page, label, M, split)
    answer_panel(page, n, split + 12, W - M)
    put(page, W / 2, H - M + 6, f"{INFO['school']}  ·  {INFO['grade']}학년 {INFO['subject']}"
        + (f"  ·  {label}" if label else "") + f"  ·  선택형 {n}문항", 7, "c")
    doc.set_metadata({"title": f"{label} OMR 답안지"})
    doc.subset_fonts()
    doc.save(os.path.join(HERE, out), garbage=4, deflate=True)
    print("saved", out, n, "questions")


if __name__ == "__main__":
    main(*sys.argv[1:5])
