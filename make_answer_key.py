"""문학 시험지 정답표 형식으로 정답지 PDF(정답지.pdf)를 만든다.

사용법: python3 make_answer_key.py
정답·배점은 questions.py 의 ANS·PTS, 시험 정보는 make_template.py 의 INFO 를 쓴다.
"""
import os

import pymupdf

from make_template import FONTS, HERE, INFO
from questions import ANS, PTS, Q

FONT = "Body"                 # 함초롱바탕 (본문과 같은 글꼴)
BLACK = (0, 0, 0)
SHADE = (0.85, 0.87, 0.93)    # 원본 정답표의 머리칸 색
PER_ROW = 14                  # 한 줄(블록)에 넣을 문항 수


def put(page, x, y, s, size=9, anchor="c"):
    w = pymupdf.Font(fontfile=FONTS[FONT]).text_length(s, fontsize=size)
    x = x - w / 2 if anchor == "c" else x
    page.insert_text((x, y), s, fontname=FONT, fontfile=FONTS[FONT], fontsize=size,
                     color=BLACK)


def cell(page, r, lines, size=9, fill=None, lw=0.6):
    if fill:
        page.draw_rect(r, color=None, fill=fill)
    page.draw_rect(r, color=BLACK, width=lw)
    lead = size * 1.15
    y = (r.y0 + r.y1) / 2 - lead * (len(lines) - 1) / 2 + size * 0.35
    for t in lines:
        put(page, (r.x0 + r.x1) / 2, y, t, size)
        y += lead


def main(out="정답지.pdf"):
    n = len(Q)
    total = sum(PTS)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    L, R = 49.0, 541.0

    # 제목·시행일 (원본 정답표처럼 점선 밑줄)
    title = f"{INFO['grade']}학년 ({INFO['subject']})"
    put(page, 114, 96, title, 13, anchor="l")
    tw = pymupdf.Font(fontfile=FONTS[FONT]).text_length(title, fontsize=13)
    page.draw_line((112, 103), (114 + tw + 4, 103), color=BLACK, width=0.8, dashes="[1 1.5] 0")
    put(page, 55, 125, "시험일자", 10, anchor="l")
    put(page, 105, 125, INFO["date"].split("(")[0], 10, anchor="l")

    # 시험 정보 표
    heads = [["학년"], ["과정"], ["과목", "코드"], ["과목명"], ["이수", "단위"], ["문항수"],
             ["선택형", "점수"], ["서술형", "점수"]]
    vals = [[INFO["grade"]], INFO["course"].split()[:2], [INFO["code"]], [INFO["subject"]],
            [INFO["credits"]], [str(n)], [f"{total:g}"], [f"{INFO['essay_score']}"]]
    widths = [36, 60, 44, 106, 44, 48, 52, 52]
    scale = (R - L) / sum(widths)
    x, y0 = L, 150
    for h, v, w in zip(heads, vals, widths):
        w *= scale
        cell(page, pymupdf.Rect(x, y0, x + w, y0 + 30), h, 9, SHADE)
        cell(page, pymupdf.Rect(x, y0 + 30, x + w, y0 + 60), v, 9.5)
        x += w

    # 정답 표: 번호 / 배점 / 정답 (14문항씩)
    y = y0 + 86
    lab_w = 42
    cw = (R - L - lab_w) / PER_ROW
    for start in range(0, n, PER_ROW):
        nums = range(start, min(start + PER_ROW, n))
        rows = [("번호", [str(i + 1) for i in nums], 18, SHADE),
                ("배점", [f"{PTS[i]:.1f}" for i in nums], 20, None),
                ("정답", [ANS[i] for i in nums], 24, None)]
        for lab, items, h, fill in rows:
            cell(page, pymupdf.Rect(L, y, L + lab_w, y + h), [lab], 9, SHADE)
            for k, t in enumerate(items):
                r = pymupdf.Rect(L + lab_w + k * cw, y, L + lab_w + (k + 1) * cw, y + h)
                cell(page, r, [t], 9.5 if lab == "정답" else 9, fill)
            y += h
        page.draw_rect(pymupdf.Rect(L, y - 62, R, y), color=BLACK, width=1.4)
        y += 16

    # 비고
    multi = [str(i + 1) for i, a in enumerate(ANS) if "," in a]
    put(page, L, y + 6, f"※ {'·'.join(multi)}번은 복수 정답 문항으로, 정답을 모두 골라야 정답으로 "
        "인정합니다.", 9, anchor="l")
    put(page, L, y + 22, f"※ 선택형 {n}문항, 총 {total:g}점 (문항별 배점은 위 표 참조)", 9, anchor="l")

    doc.set_metadata({"title": f"{title} 정답지"})
    doc.subset_fonts()
    doc.save(os.path.join(HERE, out), garbage=4, deflate=True)
    print("saved", out)


if __name__ == "__main__":
    main()
