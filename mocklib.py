"""실전 모의고사 문항 모듈이 함께 쓰는 도우미.

문항 모듈 작성법 (예: mock4_questions.py)
    from mocklib import *
    S = Set()                                   # 문항을 차례로 쌓는 그릇
    S.stmt(발문, 앞자료html, 선지5개, 정답위치(0~4, items 안), 놓을위치(0~4), 해설, w=난도)
    S.add(발문, 본문html(선지 포함), 정답위치(0~4), 해설, w=난도)
    S.essay(발문, 본문html, 모범답안, [채점기준...], w=난도)   # 직전 선택형 뒤에 놓인다
    S.done(globals())                           # Q, ANS, PTS, EXPL, ESSAY... 를 만들고 배점을 100점으로 맞춘다

난도 w: 선택형 3(하)~6(최상), 서술형 5~10. 배점은 w 에 비례해 총 100점이 되도록 0.1점 단위로 정한다.
해설 문자열에서 ' [함정] ' 뒤는 정답지에 빨간 글씨로 나온다.
"""
from mock1_questions import order
from questions import C, box, ch, dlg, grid, lab, lines, p

__all__ = ["C", "box", "ch", "dlg", "grid", "lab", "lines", "p", "order", "rows", "table", "gridq",
           "answer_lines", "cond", "fig", "chat", "sign", "Set", "u"]


def u(s):
    """밑줄."""
    return f"<u>{s}</u>"


def rows(head, data, first=9):
    """선지 번호(①~⑤)가 붙은 표. data 는 선지 순서대로의 행."""
    return (f'<table class="t hz"><tr><th style="width:{first}%"></th>'
            + "".join(f"<th>{h}</th>" for h in head) + "</tr>"
            + "".join(f"<tr><td>{C[i]}</td>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                      for i, r in enumerate(data))
            + "</table>")


def table(head, data, widths=None, cls="t hz"):
    """번호 없는 자료 표. widths 는 열별 % (None 이면 자동)."""
    ws = widths or [None] * len(head)
    th = "".join(f'<th style="width:{w}%">{h}</th>' if w else f"<th>{h}</th>" for h, w in zip(head, ws))
    return (f'<table class="{cls}"><tr>{th}</tr>'
            + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in data)
            + "</table>")


def gridq(*xs):
    """짧은 선지를 3칸 격자로."""
    return grid(list(xs))


def answer_lines(n):
    """서술형 답란 n줄."""
    return '<table class="al">' + '<tr><td>&#160;</td></tr>' * n + "</table>"


def cond(*rs):
    """<조건> 상자."""
    return box("조건", lines(*rs, cls="c"), "cond")


def fig(name, width="85%"):
    """assets/figs/<name>.svg 그림 (직접 그린 SVG)."""
    return f'<p class="fig"><img src="figs/{name}.svg" style="width:{width}"/></p>'


def chat(*msgs, title=""):
    """문자 메시지 화면. msgs: ("이름", "말", "l"|"r") — r 은 오른쪽(나)."""
    out = ['<table class="chat">']
    if title:
        out.append(f'<tr><td colspan="2" class="ct">{title}</td></tr>')
    for who, msg, side in msgs:
        if side == "r":
            out.append(f'<tr><td class="cs"></td><td class="cr">{msg}</td></tr>')
        else:
            out.append(f'<tr><td class="cl" colspan="2"><span class="cw">{who}</span><br/>{msg}</td></tr>')
    out.append("</table>")
    return "".join(out)


def sign(*texts):
    """간판·현수막·포스터처럼 테두리 친 글 (여러 개면 나란히)."""
    cells = "".join(f'<td class="sg">{t}</td>' for t in texts)
    return f'<table class="sgn"><tr>{cells}</tr></table>'


class Set:
    def __init__(self):
        self.Q, self.ANS, self.EXPL, self.W = [], [], [], []
        self.ES, self.EA, self.ER, self.EW, self.AFTER = [], [], [], [], []

    def add(self, stem, body, ans, expl, w=4):
        self.Q.append((stem, body))
        self.ANS.append(C[ans])
        self.EXPL.append(expl)
        self.W.append(w)

    def stmt(self, stem, pre, items, correct, target, expl, kind=ch, w=4):
        assert len(items) == 5 and 0 <= correct < 5 and 0 <= target < 5
        self.add(stem, pre + kind(*order(items, correct, target)), target, expl, w)

    def essay(self, stem, body, answer, rubric, w=7):
        self.ES.append((stem, body))
        self.EA.append(answer)
        self.ER.append(list(rubric))
        self.EW.append(w)
        self.AFTER.append(len(self.Q))

    def done(self, g, total=100):
        ws = self.W + self.EW
        raw = [w * total / sum(ws) for w in ws]
        pts = [round(x, 1) for x in raw]
        k = max(range(len(pts)), key=lambda i: ws[i])
        pts[k] = round(pts[k] + total - sum(pts), 1)
        n = len(self.W)
        g.update(Q=self.Q, ANS=self.ANS, EXPL=self.EXPL, PTS=pts[:n],
                 ESSAY=self.ES, ESSAY_ANS=self.EA, ESSAY_RUBRIC=self.ER, ESSAY_PTS=pts[n:],
                 ESSAY_AFTER=self.AFTER)
        assert abs(sum(pts) - total) < 1e-6
        return g
