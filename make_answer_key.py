"""문학 시험지 정답표 형식으로 정답지 PDF(정답지.pdf)를 만든다.

사용법: python3 make_answer_key.py
정답·배점은 questions.py 의 ANS·PTS, 시험 정보는 make_template.py 의 INFO 를 쓴다.
"""
import os

import pymupdf

import importlib
import sys

from make_template import FONTS, HERE, INFO

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


# 문제지 정정 (이미 인쇄된 문제지의 고칠 부분): (번호, 위치, 인쇄된 내용, 바른 내용)
PAPER_FIX = [
    (8, "<보기> 정", "함박눈ː[雪]", "함박눈[雪] (장음 표시 삭제, 입력 오류)"),
    (17, "발문", "…적용되는 문장을 모두 고르면?", "…적용되는 문장은?"),
    (28, "발문", "…적절하지 않은 것을 모두 고르면?", "…적절하지 않은 것은?"),
]

# 정답 정정: (번호, 수정 전, 수정 후, 사유)
ERRATA = [
    (8, "③", "⑤", "원문은 ‘함박눈[雪]’(짧은소리)으로 정이 바르게 발음함. ‘무력(無力)’은 짧은소리, ‘성인(成人)’도 짧은소리이므로 을·병·정이 바름"),
    (17, "④, ⑤", "④", "⑤ ‘똑같이[똑까치]’는 구개음화·된소리되기만 일어나며 음절의 끝소리 규칙이 적용되지 않음"),
    (19, "⑤", "②", "㉢의 예 ‘횡단로[횡단노]’는 제19항이 아닌 제20항 ‘다만’의 예외 단어이므로 ㉢은 적절하지 않음"),
    (24, "②", "④", "‘물동이[물똥이]’는 고유어 합성어로 제26항(한자어 ㄹ 받침 뒤)의 용례가 아님. ② ‘삶자[삼ː짜]’는 제24항에 해당"),
    (26, "③", "②", "‘우짖다(울-+짖다)’는 합성어 형성 시의 ㄹ 탈락으로 활용 과정의 예가 아님. ③ ‘부나방(불+나방)’은 적절"),
    (28, "④, ⑤", "⑤", "④ ‘싫은[시른]’은 ㅎ 탈락이 일어나므로 탈락의 예로 적절함. ⑤ ‘닭이[달기]’만 적절하지 않음"),
    (36, "③", "④", "③은 ‘ㄱ, ㄹ, ㅂ’으로 되어 있어 틀린 진술(바르게는 ‘ㄱ, ㄷ, ㅂ’). ④ ‘밖[박]’, ‘밑[믿]’은 적절함"),
]


def wrap(s, size, width):
    f = pymupdf.Font(fontfile=FONTS[FONT])
    out, cur = [], ""
    for ch in s:
        if f.text_length(cur + ch, fontsize=size) > width:
            out.append(cur)
            cur = ch.lstrip()
        else:
            cur += ch
    return out + [cur] if cur else out


def table(page, y, cols, rows, size=8.8, lead=12):
    """cols: [(머리글, 너비)], rows: [[칸 글...]]. 마지막 칸만 여러 줄로 감싼다."""
    L = 49.0
    x = L
    for name, w in cols:
        cell(page, pymupdf.Rect(x, y, x + w, y + 22), [name], 9, SHADE)
        x += w
    top, y = y, y + 22
    for row in rows:
        wrapped = [wrap(t, size, w - 10) for t, (_, w) in zip(row, cols)]
        h = max(26, lead * max(len(t) for t in wrapped) + 10)
        x = L
        for k, ((_, w), lines) in enumerate(zip(cols, wrapped)):
            r = pymupdf.Rect(x, y, x + w, y + h)
            if k < len(cols) - 1:
                cell(page, r, lines, 9.2)
            else:
                page.draw_rect(r, color=BLACK, width=0.6)
                ty = y + (h - lead * len(lines)) / 2 + size
                for ln in lines:
                    put(page, x + 5, ty, ln, size, anchor="l")
                    ty += lead
            x += w
        y += h
    page.draw_rect(pymupdf.Rect(L, top, x, y), color=BLACK, width=1.4)
    return y


def errata_page(doc):
    page = doc.new_page(width=595, height=842)
    L, R = 49.0, 541.0
    title = f"{INFO['grade']}학년 ({INFO['subject']}) 정오표"
    put(page, 114, 96, title, 13, anchor="l")
    tw = pymupdf.Font(fontfile=FONTS[FONT]).text_length(title, fontsize=13)
    page.draw_line((112, 103), (114 + tw + 4, 103), color=BLACK, width=0.8, dashes="[1 1.5] 0")

    put(page, L, 132, "1. 문제지 정정 (인쇄된 문제지에서 고칠 부분)", 10.5, anchor="l")
    y = table(page, 142, [("번호", 34), ("위치", 62), ("인쇄된 내용", 170), ("바른 내용", R - L - 266)],
              [[str(n), w, a, b] for n, w, a, b in PAPER_FIX])

    y += 30
    put(page, L, y, "2. 정답 정정", 10.5, anchor="l")
    y = table(page, y + 10, [("번호", 34), ("수정 전", 52), ("수정 후", 52), ("사유", R - L - 138)],
              [[str(n), a, b, why] for n, a, b, why in ERRATA])
    put(page, L, y + 20, "※ 정답 정정 내용은 정답지 1쪽 정답표에 반영되어 있음.", 9, anchor="l")


def main(out="정답지.pdf", qmod="questions", label="", errata=True, per_row=PER_ROW):
    mod = importlib.import_module(qmod)
    ANS, PTS, Q = mod.ANS, mod.PTS, mod.Q
    n = len(Q)
    total = sum(PTS)
    EP = getattr(mod, "ESSAY_PTS", [])
    ne, etotal = len(EP), sum(EP)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    L, R = 49.0, 541.0

    # 제목·시행일 (원본 정답표처럼 점선 밑줄)
    title = f"{INFO['grade']}학년 ({INFO['subject']}){' ' + label if label else ''}"
    put(page, 114, 96, title, 13, anchor="l")
    tw = pymupdf.Font(fontfile=FONTS[FONT]).text_length(title, fontsize=13)
    page.draw_line((112, 103), (114 + tw + 4, 103), color=BLACK, width=0.8, dashes="[1 1.5] 0")
    put(page, 55, 125, "시험일자", 10, anchor="l")
    put(page, 105, 125, INFO["date"].split("(")[0], 10, anchor="l")

    # 시험 정보 표
    heads = [["학년"], ["과정"], ["과목", "코드"], ["과목명"], ["이수", "단위"], ["문항수"],
             ["선택형", "점수"], ["서술형", "점수"]]
    vals = [[INFO["grade"]], INFO["course"].split()[:2], [INFO["code"]], [INFO["subject"]],
            [INFO["credits"]], [str(n + ne)], [f"{total:g}"], [f"{etotal:g}"]]
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
    cw = (R - L - lab_w) / per_row
    for start in range(0, n, per_row):
        if y + 62 > 800:                  # 정답표가 길면 다음 쪽으로
            page, y = doc.new_page(width=595, height=842), 90
        nums = range(start, min(start + per_row, n))
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
    notes = []
    multi = [str(i + 1) for i, a in enumerate(ANS) if "," in a]
    if multi:
        notes.append(f"※ {'·'.join(multi)}번은 복수 정답 문항으로, 정답을 모두 골라야 정답으로 인정합니다.")
    notes.append(f"※ 선택형 {n}문항, 총 {total:g}점 (문항별 배점은 위 표 참조)")
    if ne:
        same = len(set(EP)) == 1
        where = "해설의 해당 위치" if getattr(mod, "ESSAY_AFTER", None) is not None else "해설 뒤쪽"
        notes.append(f"※ 서술형 {ne}문항({'각 ' + format(EP[0], 'g') + '점, ' if same else ''}총 {etotal:g}점)의 "
                     f"모범 답안과 채점 기준은 {where} 참조")
    if errata:
        notes.append("※ 문제지 정정 및 정답 정정 내역은 2쪽 정오표 참조")
    if getattr(mod, "EXPL", None):
        notes.append("※ 문항별 해설과 함정 포인트는 다음 쪽 참조")
    for k, t in enumerate(notes):
        put(page, L, y + 6 + 16 * k, t, 9, anchor="l")

    if errata:
        errata_page(doc)
    if getattr(mod, "EXPL", None):
        explanation_pages(doc, title, ANS, PTS, mod.EXPL,
                          list(zip(EP, mod.ESSAY_ANS, mod.ESSAY_RUBRIC)) if ne else (),
                          getattr(mod, "ESSAY_AFTER", None))

    doc.set_metadata({"title": f"{title} 정답지"})
    doc.subset_fonts()
    doc.save(os.path.join(HERE, out), garbage=4, deflate=True)
    print("saved", out)


def explanation_pages(doc, title, ANS, PTS, EXPL, essays=(), essay_after=None):
    """문항별 정답·해설. 한 단으로, 페이지가 차면 다음 쪽으로 넘긴다.
    essay_after 가 있으면 서술형 해설을 문제지와 같은 자리(선택형 k번 뒤)에 끼워 넣는다."""
    L, R, top, bottom = 49.0, 541.0, 140.0, 790.0
    size, lead = 8.8, 12.4

    def new_page():
        page = doc.new_page(width=595, height=842)
        head = f"{title} 정답 및 해설"
        put(page, 114, 96, head, 13, anchor="l")
        tw = pymupdf.Font(fontfile=FONTS[FONT]).text_length(head, fontsize=13)
        page.draw_line((112, 103), (114 + tw + 4, 103), color=BLACK, width=0.8, dashes="[1 1.5] 0")
        return page

    state = {"page": new_page(), "y": top}

    def choice(i):
        a, pt, ex = ANS[i - 1], PTS[i - 1], EXPL[i - 1]
        body = ex.split(" [함정] ")
        lines = wrap(body[0], size, R - L - 70)
        trap = wrap("[함정] " + body[1], size, R - L - 70) if len(body) > 1 else []
        h = lead * (len(lines) + len(trap)) + 10
        if state["y"] + h > bottom:
            state["page"], state["y"] = new_page(), top
        page, y = state["page"], state["y"]
        cell(page, pymupdf.Rect(L, y - 2, L + 62, y + 16), [f"{i}번  {a}"], 9.5, SHADE)
        put(page, L + 31, y + 30, f"({pt:.1f}점)", 7.5)
        ty = y + 10
        for ln in lines:
            put(page, L + 70, ty, ln, size, anchor="l")
            ty += lead
        for ln in trap:
            page.insert_text((L + 70, ty), ln, fontname=FONT, fontfile=FONTS[FONT], fontsize=size,
                             color=(0.6, 0.1, 0.1))
            ty += lead
        y = max(ty, y + 36) + 8
        page.draw_line((L, y - 4), (R, y - 4), color=(0.75, 0.75, 0.75), width=0.4)
        state["y"] = y

    def essay(i):
        pt, ans, rubric = essays[i - 1]
        blocks = [(wrap("[모범 답안] " + a, size, R - L - 70), BLACK) for a in ans.split("\n")]
        blocks += [(wrap(r, size, R - L - 70), (0.15, 0.25, 0.55)) for r in rubric]
        h = lead * sum(len(b) for b, _ in blocks) + 14
        if state["y"] + h > bottom:
            state["page"], state["y"] = new_page(), top
        page, y = state["page"], state["y"]
        cell(page, pymupdf.Rect(L, y - 2, L + 62, y + 16), [f"서술형 {i}"], 9.5, SHADE)
        put(page, L + 31, y + 30, f"({pt:g}점)", 7.5)
        ty = y + 10
        for lines, color in blocks:
            for ln in lines:
                page.insert_text((L + 70, ty), ln, fontname=FONT, fontfile=FONTS[FONT],
                                 fontsize=size, color=color)
                ty += lead
            ty += 2
        y = max(ty, y + 36) + 8
        page.draw_line((L, y - 4), (R, y - 4), color=(0.75, 0.75, 0.75), width=0.4)
        state["y"] = y

    if essay_after is None:
        for i in range(1, len(ANS) + 1):
            choice(i)
        for j in range(1, len(essays) + 1):
            essay(j)
        return
    for j, k in enumerate(essay_after, 1):
        if k == 0:
            essay(j)
    for i in range(1, len(ANS) + 1):
        choice(i)
        for j, k in enumerate(essay_after, 1):
            if k == i:
                essay(j)


if __name__ == "__main__":
    # python3 make_answer_key.py                       -> 학교 프린트 정답지(정오표 포함)
    # python3 make_answer_key.py mock1_questions 실전1회_정답지.pdf "실전 1회"
    if len(sys.argv) > 1:
        n = len(importlib.import_module(sys.argv[1]).Q)
        per_row = 12 if n <= 24 else -(-n // 2) if n <= 30 else 15  # 25~30문항은 두 줄로
        main(sys.argv[2], sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else "", errata=False,
             per_row=per_row)
    else:
        main()
