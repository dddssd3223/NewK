"""원본 문학 시험지 스캔에서 머리글 글자를 직접 벡터로 따내 assets/ 에 저장한다.

원본 제목 글꼴은 갖고 있는 글꼴(HY견고딕 등)과 모양이 달라, 스캔의 글자 모양을
potrace 로 외곽선(베지어 곡선)으로 바꿔 그대로 쓴다.
사용법: python3 trace_header.py <원본 스캔 PDF 또는 1쪽 이미지>
필요:   pip install pymupdf potracer numpy pillow
"""
import json
import os
import sys

import numpy as np
import potrace
import pymupdf
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
UP = 6  # 따내기 전에 확대하는 배율 (매끈한 곡선용)

# 스캔(144dpi) 좌표 기준 영역: (이름, x0, y0, x1, y1, 문턱값, 흐림 정도)
REGIONS = [
    ("title", 205, 185, 800, 246, 120, 0.35),
    ("date", 855, 228, 1106, 248, 105, 0.2),
    ("meta", 185, 259, 1045, 277, 125, 0.25),
]


def page_image(src):
    if src.lower().endswith(".pdf"):
        doc = pymupdf.open(src)
        img = doc.extract_image(doc[0].get_images()[0][0])
        path = os.path.join(HERE, "_scan_p1." + img["ext"])
        open(path, "wb").write(img["image"])
        im = Image.open(path).convert("L")
        os.remove(path)
        return im
    return Image.open(src).convert("L")


def trace(im, x0, y0, x1, y1, th, blur):
    crop = im.crop((x0, y0, x1, y1))
    big = crop.resize((crop.width * UP, crop.height * UP), Image.LANCZOS)
    big = big.filter(ImageFilter.GaussianBlur(UP * blur))
    bm = potrace.Bitmap(np.array(big) >= th)  # potracer 는 False 쪽을 채움으로 본다
    plist = bm.trace(turdsize=UP * UP, alphamax=1.0, opticurve=True, opttolerance=0.2)
    curves = []
    for curve in plist:
        pts = lambda p: [round(x0 + p.x / UP, 3), round(y0 + p.y / UP, 3)]
        segs = []
        for s in curve.segments:
            if s.is_corner:
                segs.append(["L", pts(s.c), pts(s.end_point)])
            else:
                segs.append(["C", pts(s.c1), pts(s.c2), pts(s.end_point)])
        curves.append({"start": pts(curve.start_point), "segs": segs})
    return curves


def main(src):
    im = page_image(src)
    out = {r[0]: trace(im, *r[1:]) for r in REGIONS}
    path = os.path.join(HERE, "assets", "header_glyphs.json")
    json.dump(out, open(path, "w"), separators=(",", ":"))
    print("saved", path, {k: len(v) for k, v in out.items()})


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "2026학년도 1학기 중간고사 2학년 문학.pdf"))
