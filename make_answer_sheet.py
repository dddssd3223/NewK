"""서답형 답안지(A4, 굴림체)를 회차별로 만든다.

사용법: python3 make_answer_sheet.py mock7_questions 실전7회_서답형답안지.pdf "실전 7회"
문항 모듈의 ESSAY(발문·본문)와 ESSAY_PTS 를 쓴다. 답란 줄 수는 문제지의 답란(answer_lines) 줄 수에 맞춰
손글씨로 쓰기 좋게 늘린다.
"""
import importlib
import os
import re
import sys

import pymupdf

from make_template import FONTS, HERE, INFO

BLACK = (0, 0, 0)
GRAY = (0.55, 0.55, 0.55)
SHADE = (0.9, 0.9, 0.9)
W, H = 595.28, 841.89                 # A4
L, R = 42.0, W - 42.0
LINE = 24.0                           # 답란 줄 간격(pt)


def font(name="Gulim"):
    return pymupdf.Font(fontfile=FONTS[name])


def put(page, x, y, s, size=10, name="Gulim", anchor="l", color=BLACK):
    w = font(name).text_length(s, fontsize=size)
    x = x - w / 2 if anchor == "c" else x - w if anchor == "r" else x
    page.insert_text((x, y), s, fontname=name, fontfile=FONTS[name], fontsize=size, color=color)


def ctext(page, r, s, size=10, name="Gulim"):
    put(page, (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2 + size * 0.36, s, size, name, "c")


LABEL = re.compile(r"\(\d\)|\([가-하]\)|[㉠-㉻]|[ⓐ-ⓩ]|[①-⑳]|(?<![가-힣ㄱ-ㅎ])[ㄱ-ㅎ](?=\s*:)")
PER_LINE = 38                          # 손글씨 한 줄에 들어갈 글자 수(대략)


def lines_for(text):
    return max(1, -(-len(text.strip()) // PER_LINE))


def entries(answer):
    """모범 답안에서 답안지에 미리 찍을 기호와 줄 수를 뽑는다. 반환: [(기호 또는 '', 줄 수)]"""
    out, used = [], set()
    for para in answer.split("\n"):
        hits = []
        for m in LABEL.finditer(para):
            t, i = m.group(), m.start()
            prev = para[i - 1] if i else " "
            if t[0] != "(" and prev == "(":
                continue                        # ‘(㉡)’처럼 설명 속에서 가리키는 기호
            if prev not in " /,—–:·" and i:
                continue
            if t in used:
                continue
            hits.append(m)
        if not hits:
            parts = [x.strip() for x in para.split("/")]
            heads = [re.match(r"([가-힣]{1,6}):\s*(.*)", x) for x in parts]
            if len(parts) > 1 and all(heads):            # ‘교체: … / 탈락: …’ 꼴은 머리말을 기호로
                out += [(h.group(1) + ":", lines_for(h.group(2))) for h in heads]
            else:
                out.append(("", lines_for(para)))
            continue
        pre = para[:hits[0].start()].strip()
        label = ""
        if pre.endswith(":") and len(pre) <= 8:           # ‘발음: ㉠ …’ 의 머리말은 첫 기호에 붙인다
            label = pre
        elif pre:
            out.append(("", lines_for(pre)))
        for k, m in enumerate(hits):
            used.add(m.group())
            seg = para[m.end():hits[k + 1].start() if k + 1 < len(hits) else len(para)]
            label = (label + " " + m.group()).strip()
            if not seg.strip(" ,/:—–"):         # 기호가 바로 이어지면 묶는다: (1) ㄱ
                continue
            out.append((label, lines_for(seg)))
            label = ""
        if label:
            out.append((label, 1))
    return out


KINDS = [re.compile(r"[㉠-㉻]"), re.compile(r"[ⓐ-ⓩ]"), re.compile(r"[①-⑳]"), re.compile(r"\([가-하]\)")]


def hide_answers(es, answer, question):
    """‘찾아/골라 기호를 쓰라’는 문항에서 일부 기호만 찍으면 답이 드러나므로, 그 종류의 기호는 지운다."""
    for name in re.findall(r'figs/([\w-]+\.svg)', question):   # 그림 속 기호도 문항의 일부
        question += open(os.path.join(HERE, "assets", "figs", name), encoding="utf-8").read()
    q = re.sub(r"<[^>]+>", "", question)
    if not re.search(r"찾아|고르|골라", q):
        return es
    out = []
    for lab, n in es:
        parts = lab.split()
        keep = []
        for t in parts:
            kind = next((k for k in KINDS if k.fullmatch(t)), None)
            if kind:
                in_q = set(kind.findall(q))
                in_a = {x for x, _ in es for x in x.split() if kind.fullmatch(x)}
                if in_a != in_q:
                    continue
            keep.append(t)
        out.append((" ".join(keep), n))
    return out


def plan(answer, body, stem=""):
    """서술형 한 칸의 줄 계획. 문제지 답란보다 적지 않게, 너무 길지 않게."""
    es = hide_answers(entries(answer), answer, stem + body)
    k_paper = body.count("<tr><td>&#160;</td></tr>")
    total = sum(n for _, n in es)
    want = max(3, round(k_paper * 1.4) + 1)
    if total < want and es:                      # 마지막 칸에 여유 줄을 더한다
        lab, n = es[-1]
        es[-1] = (lab, n + want - total)
    return es


def header(page, label, first):
    """첫 쪽: 제목 + 반·번호·이름 표. 다음 쪽: 짧은 머리말."""
    if not first:
        put(page, L, 40, f"{INFO['grade']}학년 {INFO['subject']} {label} 서답형 답안지 (계속)", 9, color=GRAY)
        return 56.0
    title = f"{INFO['grade']}학년 {INFO['subject']} {INFO['exam']}  서답형 답안지"
    put(page, W / 2, 62, title, 17, "Gulim", "c")
    if label:
        put(page, W / 2, 82, f"[ {label} ]", 11, "Gulim", "c")
    # 정보 표: 학년 | 반 | 번호 | 이름 | 점수
    y0, h1, h2 = 98.0, 22.0, 32.0
    cols = [("학년", 52), ("반", 62), ("번호", 62), ("이름", 190), ("점수", R - L - 366)]
    x = L
    for name, w in cols:
        r1 = pymupdf.Rect(x, y0, x + w, y0 + h1)
        r2 = pymupdf.Rect(x, y0 + h1, x + w, y0 + h1 + h2)
        page.draw_rect(r1, color=BLACK, fill=SHADE, width=0.6)
        page.draw_rect(r2, color=BLACK, width=0.6)
        ctext(page, r1, name, 10)
        if name == "학년":
            ctext(page, r2, INFO["grade"], 12)
        x += w
    page.draw_rect(pymupdf.Rect(L, y0, R, y0 + h1 + h2), color=BLACK, width=1.4)
    put(page, L, y0 + h1 + h2 + 18,
        "※ 답은 반드시 해당 문항 칸 안에 검은색 볼펜으로 쓰시오. 칸 밖에 쓴 답은 채점하지 않습니다.", 9)
    return y0 + h1 + h2 + 34


def block(page, y, n, pts, es):
    """서술형 n번 칸: 왼쪽 번호 칸 + 기호가 찍힌 줄 + 맨 오른쪽 채점 칸."""
    k = sum(c for _, c in es)
    h = 8 + LINE * k
    lw, sw = 62.0, 44.0
    box = pymupdf.Rect(L, y, R, y + h)
    lab = pymupdf.Rect(L, y, L + lw, y + h)
    sc = pymupdf.Rect(R - sw, y, R, y + h)
    page.draw_rect(lab, color=None, fill=SHADE)
    page.draw_rect(box, color=BLACK, width=1.0)
    page.draw_line((L + lw, y), (L + lw, y + h), color=BLACK, width=0.6)
    page.draw_line((R - sw, y), (R - sw, y + h), color=BLACK, width=0.6)
    put(page, (lab.x0 + lab.x1) / 2, y + h / 2 - 2, f"서술형 {n}", 10, anchor="c")
    put(page, (lab.x0 + lab.x1) / 2, y + h / 2 + 12, f"({pts:g}점)", 8.5, anchor="c")
    put(page, (sc.x0 + sc.x1) / 2, y + 14, "채점", 8, anchor="c", color=GRAY)
    i = 0
    for label, c in es:
        for j in range(c):
            i += 1
            ly = y + 4 + LINE * i
            if j == 0 and label:
                put(page, L + lw + 8, ly - 6, label, 10.5)
            if i < k:
                page.draw_line((L + lw + 8, ly), (R - sw - 8, ly), color=GRAY, width=0.4,
                               dashes="[2 2] 0")
        if label or c:
            pass
    return y + h + 10


def main(qmod, out, label=""):
    mod = importlib.import_module(qmod)
    ES, EP = mod.ESSAY, mod.ESSAY_PTS
    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    y = header(page, label, True)
    bottom = H - 50
    for n, ((stem, body), pts, ans) in enumerate(zip(ES, EP, mod.ESSAY_ANS), 1):
        es = plan(ans, body, stem)
        k = sum(c for _, c in es)
        if y + 8 + LINE * k > bottom:
            page = doc.new_page(width=W, height=H)
            y = header(page, label, False)
        y = block(page, y, n, pts, es)
    total = sum(EP)
    for i, pg in enumerate(doc, 1):
        put(pg, W / 2, H - 24, f"{label} 서답형 답안지  {i} / {len(doc)}   (서답형 {len(ES)}문항 · {total:g}점)",
            8.5, anchor="c", color=GRAY)
    doc.set_metadata({"title": f"{label} 서답형 답안지"})
    doc.subset_fonts()
    doc.save(os.path.join(HERE, out), garbage=4, deflate=True)
    print("saved", out, len(doc), "pages,", len(ES), "essays")


if __name__ == "__main__":
    main(*sys.argv[1:4])
