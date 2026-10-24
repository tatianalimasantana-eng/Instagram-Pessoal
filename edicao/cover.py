from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import sys
S, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
F = lambda n, s: ImageFont.truetype(f'{S}/fonts/{n}', s)
im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
r = 1920 / im.height; im = im.resize((round(im.width*r), 1920), Image.LANCZOS)
x0 = (im.width - 1080)//2 + 20; im = im.crop((x0, 0, x0+1080, 1920))
# warm, soft grade + bottom gradient
im = Image.blend(im, Image.new('RGB', im.size, (255, 214, 170)), 0.04)
grad = Image.new('L', (1, 1920))
for y in range(1920):
    v = 0 if y < 900 else min(215, int(((y-900)/700)**1.3*215))
    grad.putpixel((0, y), v)
im.paste(Image.new('RGB', im.size, (20, 14, 10)), (0, 0), grad.resize(im.size))
d = ImageDraw.Draw(im)
YEL = (255, 212, 92)
def center(text, y, font, fill, spacing=0):
    w = d.textlength(text, font=font) + spacing*(len(text)-1)
    x = (1080 - w)/2
    if spacing:
        for ch in text:
            d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + spacing
    else:
        d.text((x, y), text, font=font, fill=fill)
    return w
# tag pill
tag = 'PAPO ENQUANTO ME ARRUMO  ·  EP. 01'; tf = F('montserrat-latin-800-normal.ttf', 30)
tw = d.textlength(tag, font=tf) + 3*(len(tag)-1)
d.rounded_rectangle(((1080-tw)/2-28, 1118, (1080+tw)/2+28, 1176), radius=29, fill=YEL)
center(tag, 1131, tf, (30, 22, 16), spacing=3)
center('1 ano sem saber', 1215, F('dm-serif-display-latin-400-normal.ttf', 132), (255, 255, 255))
center('o que fazer da minha', 1375, F('playfair-display-latin-700-italic.ttf', 92), YEL)
center('vida profissional', 1480, F('playfair-display-latin-700-italic.ttf', 92), YEL)
im.save(out, quality=95)
# grid preview (3:4 center crop like the profile grid)
g = im.crop((0, 240, 1080, 1680)).resize((540, 720)); g.save(out.replace('.jpg', '-preview-grid.jpg'), quality=90)
