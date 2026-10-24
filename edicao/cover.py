from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import sys
S, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
F = lambda n, s: ImageFont.truetype(f'{S}/fonts/{n}', s)
im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
r = 1920 / im.height; im = im.resize((round(im.width*r), 1920), Image.LANCZOS)
x0 = (im.width - 1080)//2 + 20; im = im.crop((x0, 0, x0+1080, 1920))
# soft bottom gradient so the white text reads like the rest of the feed
grad = Image.new('L', (1, 1920))
for y in range(1920):
    grad.putpixel((0, y), 0 if y < 1050 else min(150, int(((y-1050)/600)**1.4*150)))
im.paste(Image.new('RGB', im.size, (25, 18, 12)), (0, 0), grad.resize(im.size))
title = F('fira-500-italic.ttf', 84); sub = F('fira-500-italic.ttf', 44)
lines = [('1 ano sem saber', title, 1270), ('o que fazer da minha', title, 1370), ('vida profissional', title, 1470),
         ('papo enquanto me arrumo · ep. 01', sub, 1595)]
shadow = Image.new('L', im.size, 0); ds = ImageDraw.Draw(shadow)
txt = Image.new('L', im.size, 0); dt = ImageDraw.Draw(txt)
for t, f, y in lines:
    x = (1080 - dt.textlength(t, font=f)) / 2
    dt.text((x, y), t, font=f, fill=255); ds.text((x+2, y+4), t, font=f, fill=170)
shadow = shadow.filter(ImageFilter.GaussianBlur(7))
im.paste(Image.new('RGB', im.size, (0, 0, 0)), (0, 0), shadow)
im.paste(Image.new('RGB', im.size, (255, 255, 255)), (0, 0), txt)
im.save(out, quality=95)
im.crop((0, 240, 1080, 1680)).resize((540, 720)).save(out.replace('.jpg', '-preview-grid.jpg'), quality=90)
