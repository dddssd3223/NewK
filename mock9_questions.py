"""화법과 언어 실전 9회 — 평가문제집 1단원 언어와 의사소통 ~ 2-1 발음 전 문항.

비상교육 『화법과 언어』 평가문제집의 확인 문제·활동 학습·소단원 평가·대단원 평가·내공 집중 문제를
원문 순서 그대로 옮겼다. 서술형(단답형 포함)은 원래 자리에 [서술형 n]으로 끼워 넣었다.
사잇소리(사이시옷) 문항은 시험 범위 밖이라 뺐다.
조각: p9_a(PDF 1~16쪽), p9_b(17~30쪽), p9_c(31쪽~)
"""
import p9_a
import p9_b
import p9_c
from mocklib import Set

S = Set()
for part in (p9_a, p9_b, p9_c):
    part.build(S)
S.done(globals())
