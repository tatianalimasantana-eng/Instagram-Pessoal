"""Capa do Reels EP. 01 (1080x1920). Uso: python capa.py RAW_DIR WORK_DIR"""
import sys
from PIL import Image, ImageOps, ImageEnhance
import build as B   # reaproveita fontes, faixa suave e desenho do texto

im = ImageOps.exif_transpose(Image.open(B.RAW / 'IMG_7377.JPG')).convert('RGB')
iw, ih = im.size; cw = ih * 9 / 16; x0 = min(max(.47 * iw - cw / 2, 0), iw - cw)
im = im.resize((B.W, B.H), Image.LANCZOS, box=(x0, 0, x0 + cw, ih))
# mesmo grading suave do vídeo (sem retoque de pele)
im = ImageEnhance.Contrast(im).enhance(1.04); im = ImageEnhance.Color(im).enhance(1.07)
cap = im.convert('RGBA')
B.scrim(cap, 220, 560, 105)
for y, t, f, s in [(270, 'PASSEIOS EM ONTÁRIO', B.F500, 84),
                   (378, 'Fall Edition 🍂', B.F500, 44),
                   (446, 'EP. 01 | Pumpkin Farm', B.F500, 34)]:
    B.draw_line(cap, y, t, f, s)
cap.convert('RGB').save(B.WORK / 'EP01_PumpkinFarm_capa.jpg', quality=95)
# prévia do recorte do grid (3:4 central)
g = cap.convert('RGB').crop((0, 240, 1080, 1680)).resize((360, 480), Image.LANCZOS)
g.save(B.WORK / 'capa_preview_grid.jpg', quality=90)
print('capa ok')
