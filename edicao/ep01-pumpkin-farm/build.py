"""
Passeios em Ontário | Fall Edition · EP. 01 Pumpkin Farm
Projeto de edição (reprodutível). Uso:
    python build.py RAW_DIR WORK_DIR

RAW_DIR  : arquivos originais do Drive (IMG_*.MOV, IMG_*.JPG, narracao.m4a)
WORK_DIR : pasta de trabalho / saída

Identidade: Fira Sans Italic (500 / 600 / 700). Ver briefing/ep01-pumpkin-farm.md
"""
import json, os, subprocess, sys
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FONTS = REPO / 'fontes'
RAW = Path(sys.argv[1]); WORK = Path(sys.argv[2])
SEG = WORK / 'segmentos'; OVL = WORK / 'overlays'
for d in (SEG, OVL): d.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 24
F500 = str(FONTS / 'FiraSans-MediumItalic.ttf')
F600 = str(FONTS / 'FiraSans-SemiBoldItalic.ttf')
F700 = str(FONTS / 'FiraSans-BoldItalic.ttf')
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); raise SystemExit(f'falhou: {cmd[:6]}')
    return r

# ---------------------------------------------------------------- narração
# Blocos da narração (tempo no arquivo original) e onde entram no vídeo.
# Nada de fala foi removido; só os silêncios do início/fim e entre blocos.
NARR = [  # (src_in, src_out, out_start)
    (1.25, 12.38, 0.45),   # "Se tem uma coisa ... nosso passeio"
    (12.38, 28.40, 13.28), # "Olha só ... tomar café"   (respiro 1 antes)
    (29.05, 38.60, 32.10), # "Eu amo ... próximo outono" (respiro 2 antes)
]
def offset(src_t):
    for a, b, o in NARR:
        if a - 0.01 <= src_t <= b + 0.01: return o - a
    raise ValueError(src_t)

TOTAL_D = 45.5   # duração na linha do tempo de desenho (voz em 1.0x)

# Voz acelerada a pedido da Tati (tom preservado com atempo).
# A linha do tempo de desenho é comprimida pelo mesmo fator até o fim da fala;
# o encerramento (depois da fala) mantém a duração.
SPEED = 1.2
NARR_END = 41.8
def T(t):
    return t / SPEED if t <= NARR_END else NARR_END / SPEED + (t - NARR_END)
TOTAL = T(TOTAL_D)

# ---------------------------------------------------------------- planos
# (tipo, arquivo, src_in, out_start, out_end, extra)
# V = vídeo, P = foto com movimento suave (Ken Burns)
SHOTS = [
    ('V', 'IMG_7423', 0.00, 0.00, 1.10, {}),                       # celeiro + abóboras (hook)
    ('P', 'IMG_7426', 0, 1.10, 2.90, dict(cx=.50, z=(1.00, 1.07))),  # caminhonete vermelha
    ('P', 'IMG_7377', 0, 2.90, 4.90, dict(cx=.47, z=(1.07, 1.00))),  # Tati + abóbora gigante
    ('V', 'IMG_7312', 4.60, 4.90, 6.90, dict(crop=(.02, .62))),                       # estrada de outono · "outono aqui no Canadá"
    ('V', 'IMG_7356', 2.40, 6.90, 8.85, {}),                       # fileiras de abóboras · "fazenda de abóboras"
    ('V', 'IMG_7316', 0.00, 8.85, 10.15, {}),                      # selfie · "E foi exatamente"
    ('V', 'IMG_7314', 9.75, 10.15, 11.60, {}),                     # selfie sorrindo · "nosso passeio"
    ('V', 'IMG_7318', 2.60, 11.60, 12.20, {}),                     # respiro 1: sol entre as árvores
    ('V', 'IMG_7312', 12.00, 12.20, 12.75, dict(crop=(.02, .62))),                    # respiro 1: estrada
    ('V', 'IMG_7315', 1.50, 12.75, 13.30, {}),                     # respiro 1: árvores no horizonte
    ('V', 'IMG_7317', 0.00, 13.30, 15.10, {}),                     # vista da fazenda · "Olha só que lugar"
    ('V', 'IMG_7320', 0.30, 15.10, 17.40, {}),                     # caminhando sob a árvore · "cenário de filme"
    ('P', 'IMG_7402', 0, 17.40, 19.40, dict(cx=.50, z=(1.00, 1.06))),  # Tati nas abóboras · "abóboras gigantes"
    ('P', 'IMG_7337', 0, 19.40, 21.30, dict(cx=.58, z=(1.06, 1.00))),  # decoração · "decoração de fall"
    ('V', 'IMG_7425', 1.00, 21.30, 23.40, {}),                     # caminhando · "não é só pra tirar foto"
    ('V', 'IMG_7324', 1.00, 23.40, 25.40, {}),                     # lojinha
    ('V', 'IMG_7328', 2.00, 25.40, 26.40, {}),                     # potes de mel
    ('V', 'IMG_7331', 1.00, 26.40, 27.30, {}),                     # decoração da loja
    ('V', 'IMG_7321', 0.00, 27.30, 29.50, {}),                     # Coffee · "tomar café"
    ('V', 'IMG_7330', 1.50, 29.50, 30.15, {}),                     # respiro 2
    ('V', 'IMG_7327', 0.20, 30.15, 30.80, {}),                     # respiro 2
    ('V', 'IMG_7312', 8.00, 30.80, 31.45, dict(crop=(.02, .62))),                     # respiro 2
    ('V', 'IMG_7318', 0.20, 31.45, 32.10, {}),                     # respiro 2
    ('P', 'IMG_7479', 0, 32.10, 34.40, dict(cx=.55, z=(1.00, 1.07))),  # folha de maple (POV) · "Eu amo esses passeios"
    ('V', 'IMG_7314', 5.00, 34.40, 37.30, {}),                     # selfie · "cada estação"
    ('V', 'IMG_7425', 3.05, 37.30, 41.80, {}),                     # até o celeiro + aceno, termina em 6,80 s (antes de sair do quadro)
    ('P', 'IMG_7462', 0, 41.80, TOTAL_D, dict(cx=.50, z=(1.08, 1.00))),  # árvore · encerramento
]

def render_video(i, name, src_in, dur, crop=None):
    out = SEG / f'{i:02d}.mp4'
    if out.exists(): return out
    vf = f'scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1,format=yuv420p'
    if crop:  # (y, altura) em fração do quadro; largura mantém 9:16, centralizado
        y, h = crop
        vf = f"crop=ih*{h}*9/16:ih*{h}:(iw-ih*{h}*9/16)/2:ih*{y}," + vf
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{src_in:.3f}', '-i', str(RAW / f'{name}.MOV'),
         '-t', f'{dur:.3f}', '-vf', vf,
         '-af', 'aresample=48000,pan=stereo|c0=c0|c1=c0',
         '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-c:a', 'pcm_s16le', '-ar', '48000',
         '-f', 'mov', str(out)])
    return out

def render_photo(i, name, dur, cx, z):
    """Ken Burns com precisão sub-pixel (sem tremido)."""
    im = ImageOps.exif_transpose(Image.open(RAW / f'{name}.JPG')).convert('RGB')
    iw, ih = im.size
    cw = ih * 9 / 16                      # recorte 9:16 na altura toda
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw)
    n = round(dur * FPS)
    out = SEG / f'{i:02d}.mp4'
    if out.exists(): return out
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-f', 'lavfi', '-t', f'{dur:.3f}', '-i', 'anullsrc=r=48000:cl=stereo',
                          '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                          '-c:a', 'pcm_s16le', '-shortest', '-f', 'mov', str(out)], stdin=subprocess.PIPE)
    for k in range(n):
        t = k / max(n - 1, 1)
        e = t * t * (3 - 2 * t)                 # ease in-out
        zz = z[0] + (z[1] - z[0]) * e
        bw, bh = cw / zz, ih / zz
        bx = x0 + (cw - bw) / 2; by = (ih - bh) / 2
        fr = im.resize((W, H), Image.LANCZOS, box=(bx, by, bx + bw, by + bh), reducing_gap=2.0)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    return out

# ---------------------------------------------------------------- textos (PNG)
def draw_line(img, y, text, font_path, size, fill=(255, 255, 255, 255), center_x=W / 2, tracking=0):
    """Texto Fira Sans + emoji colorido, centralizado, com sombra leve."""
    f = ImageFont.truetype(font_path, size)
    ef = ImageFont.truetype(EMOJI, 109)
    parts = []  # (str, is_emoji)
    for ch in text:
        emo = ord(ch) > 0x2600 and ch not in 'ÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç'
        if parts and parts[-1][1] == emo and not emo: parts[-1] = (parts[-1][0] + ch, False)
        else: parts.append((ch, emo))
    widths = []
    for s, emo in parts:
        if emo: widths.append(size * 1.05)
        else: widths.append(f.getlength(s) + tracking * len(s))
    x = center_x - sum(widths) / 2
    asc, desc = f.getmetrics()
    shadow = Image.new('L', img.size, 0); sd = ImageDraw.Draw(shadow)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for (s, emo), w in zip(parts, widths):
        if emo:
            e = Image.new('RGBA', (140, 140), (0, 0, 0, 0))
            ImageDraw.Draw(e).text((0, 0), s, font=ef, embedded_color=True)
            e = e.crop(e.getbbox()); sc = size * 0.95 / e.height
            e = e.resize((max(1, round(e.width * sc)), max(1, round(e.height * sc))), Image.LANCZOS)
            layer.alpha_composite(e, (round(x + 6), round(y + asc - e.height + size * 0.08)))
        else:
            xx = x
            for ch in s:
                sd.text((xx + 2, y + 4), ch, font=f, fill=150)
                ld.text((xx, y), ch, font=f, fill=fill)
                xx += f.getlength(ch) + tracking
        x += w
    sh = Image.new('RGBA', img.size, (30, 20, 10, 0)); sh.putalpha(shadow.filter(ImageFilter.GaussianBlur(6)))
    img.alpha_composite(sh); img.alpha_composite(layer)
    return asc + desc

def scrim(img, y0, y1, alpha=110):
    """Faixa escura suave (Autumn Brown) para legibilidade, sem bordas visíveis."""
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    d.rectangle((0, y0, W, y1), fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur((y1 - y0) * 0.35))
    band = Image.new('RGBA', (W, H), (40, 32, 24, 0)); band.putalpha(m)
    img.alpha_composite(band)

def overlay_png(name, lines, band=None):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if band: scrim(img, *band)
    for (y, text, font, size, *rest) in lines:
        draw_line(img, y, text, font, size, **(rest[0] if rest else {}))
    path = OVL / f'{name}.png'; img.save(path); return path

# (nome, início, fim, animação, linhas)
OVERLAYS = [
    ('titulo', 0.25, 4.75, 'slide', [
        (250, 'PASSEIOS EM ONTÁRIO', F500, 84),
        (358, 'Fall Edition 🍂', F500, 44),
        (426, 'EP. 01 | Pumpkin Farm', F500, 34)], (200, 500, 95)),
    ('etiquetas', 5.10, 10.0, 'fade', [
        (250, 'EP. 01  |  PUMPKIN FARM', F500, 30, dict(tracking=2)),
        (292, 'ONTARIO, CANADA', F500, 26, dict(tracking=3, fill=(247, 244, 233, 235)))], None),
    ('fall-vibes', 30.10, 32.05, 'scale', [
        (880, 'Fall vibes 🎃', F600, 96)], None),
    ('cantinho', 42.00, 43.75, 'slide', [
        (560, 'Mais um cantinho de Ontário', F600, 64),
        (642, 'para conhecer. 🍂', F600, 64)], (520, 740, 100)),
    ('serie', 43.90, TOTAL_D, 'slide', [
        (500, 'PASSEIOS EM ONTÁRIO', F500, 84),
        (608, 'Fall Edition | EP. 01', F500, 44),
        (720, 'Salva esse passeio para o próximo outono! 🎃', F500, 34)], (460, 790, 115)),
]

# ---------------------------------------------------------------- legendas
YEL = '&H0000D4FF&'   # amarelo #FFD400 (BGR)
CHUNKS = [  # (texto, destaque) — texto exatamente como falado
    ('Se tem uma coisa que você', None),
    ('precisa fazer pelo menos uma vez', None),
    ('durante o outono aqui no Canadá', 'Canadá'),
    ('é visitar uma fazenda de abóboras', 'abóboras'),
    ('E foi exatamente esse o nosso passeio', 'passeio'),
    ('Olha só que lugar mais lindo', None),
    ('Sério, parece até cenário de filme', None),
    ('com essas abóboras gigantes', None),
    ('e toda essa decoração de fall', 'fall'),
    ('E não é só para tirar foto, não', None),
    ('O lugar também tem uma lojinha super fofa', None),
    ('cheia de coisinhas para olhar', None),
    ('e até um espaço para tomar café', None),
    ('Eu amo esses passeios que fazem', None),
    ('a gente aproveitar cada estação', None),
    ('de um jeito diferente', None),
    ('E se você mora aqui em Ontário', 'Ontário'),
    ('já salva essa dica', None),
    ('para conhecer no próximo outono', 'outono'),
]

def build_captions(words):
    """Casa cada bloco com as palavras transcritas para pegar os tempos."""
    norm = lambda s: ''.join(c for c in s.lower() if c.isalnum())
    out, k = [], 0
    for text, hl in CHUNKS:
        toks = text.split(); ws = []
        for tok in toks:
            while norm(words[k]['w']) != norm(tok): k += 1
            ws.append(words[k]); k += 1
        out.append(dict(text=text, hl=hl, words=ws))
    for c in out:
        last = c['words'][-1]['s']
        a, b, o = next(n for n in NARR if n[0] - 0.01 <= last <= n[1] + 0.01)
        c['off'] = o - a
        c['start'] = T(max(c['words'][0]['s'], a) + c['off'])
        c['end'] = T(min(c['words'][-1]['e'], b) + c['off'])
    # ataque da primeira palavra: o modelo às vezes marca o início cedo demais
    for c in out: c['start'] = max(c['start'] - 0.05, 0)
    for a, b in zip(out, out[1:]):
        if b['start'] - a['end'] < 0.35: a['end'] = b['start'] - 0.02
    return out

def ts_ass(t): return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'
def ts_srt(t):
    ms = round(t * 1000); return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'

def write_ass(caps, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Legenda,Fira Sans,74,&H00FFFFFF,&H00FFFFFF,&H003A4A53,&H8C000000,-1,-1,0,0,100,100,0,0,1,2.2,3,2,130,130,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for c in caps:
        body = []
        for w, tok in zip(c['words'], c['text'].split()):
            if c['hl'] and tok.strip(',.') == c['hl']:
                t1 = max(0, round((T(w['s'] + c['off']) - c['start']) * 1000))
                body.append(r'{\t(%d,%d,\c%s\fscx114\fscy114)}%s{\r}' % (t1, t1 + 140, YEL, tok))
            else:
                body.append(tok)
        anim = r'{\fad(110,90)\move(540,1508,540,1490,0,200)}'
        lines.append(f"Dialogue: 0,{ts_ass(c['start'])},{ts_ass(c['end'])},Legenda,,0,0,0,,{anim}{' '.join(body)}")
    Path(path).write_text(head + '\n'.join(lines) + '\n', encoding='utf-8')

def write_srt(caps, path):
    Path(path).write_text('\n'.join(f"{i}\n{ts_srt(c['start'])} --> {ts_srt(c['end'])}\n{c['text']}\n"
                                    for i, c in enumerate(caps, 1)), encoding='utf-8')

# ---------------------------------------------------------------- áudio
def build_audio():
    # 1) tratamento da voz: limpeza leve, EQ suave, compressão leve. Sem mudar timbre/velocidade.
    voice = WORK / 'narracao_tratada.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(RAW / 'narracao.m4a'), '-af',
         'highpass=f=75,afftdn=nr=10:nf=-48:tn=1,'
         'equalizer=f=220:t=q:w=1.0:g=-2,equalizer=f=3400:t=q:w=1.2:g=2,equalizer=f=8500:t=h:w=2000:g=-1.5,'
         'acompressor=threshold=-21dB:ratio=2.5:attack=12:release=180:makeup=2,alimiter=limit=0.89',
         '-ar', '48000', '-ac', '2', str(voice)])
    # 2) voz posicionada na linha do tempo
    parts, labels = [], []
    for i, (a, b, o) in enumerate(NARR):
        d = (b - a) / SPEED
        parts.append(f'[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,atempo={SPEED},afade=t=in:d=0.04,afade=t=out:st={d - 0.06:.3f}:d=0.06,'
                     f'adelay={int(T(o) * 1000)}|{int(T(o) * 1000)}[n{i}]')
        labels.append(f'[n{i}]')
    voice_tl = WORK / 'narracao_timeline.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(voice), '-filter_complex',
         ';'.join(parts) + f';{"".join(labels)}amix=inputs={len(labels)}:normalize=0,apad=whole_dur={TOTAL}[v]',
         '-map', '[v]', '-t', str(TOTAL), str(voice_tl)])
    return voice_tl

def main():
    words = [w for s in json.load(open(WORK / 'transcricao.json')) for w in s['words']]
    for w in words:  # conferido no áudio: ela diz "fall"
        if w['w'].strip() == 'fol': w['w'] = ' fall'
    # planos
    segs = []
    for i, (kind, name, src_in, a, b, ex) in enumerate(SHOTS):
        dur = T(b) - T(a)
        segs.append(render_video(i, name, src_in, dur, ex.get('crop')) if kind == 'V' else render_photo(i, name, dur, ex['cx'], ex['z']))
        print(f'plano {i:02d} {name} {a:5.2f}-{b:5.2f}', flush=True)
    lst = WORK / 'segmentos.txt'
    lst.write_text(''.join(f"file '{p}'\n" for p in segs))
    base = WORK / 'base.mov'
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(base)])

    voice_tl = build_audio()
    # só a voz (voice over); som original dos vídeos removido a pedido da Tati
    mix = WORK / 'mix.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(voice_tl), '-af',
         'loudnorm=I=-14:TP=-1.5:LRA=9', '-ar', '48000', '-t', f'{TOTAL:.3f}', str(mix)])

    caps = build_captions(words)
    write_ass(caps, WORK / 'legendas.ass'); write_srt(caps, WORK / 'legendas.srt')
    json.dump(caps, open(WORK / 'legendas.json', 'w'), ensure_ascii=False, indent=1)

    ovl = [(overlay_png(n, lines, band), T(a), T(b), anim) for n, a, b, anim, lines, band in OVERLAYS]

    # color grading de outono (suave, global; sem retoque de pele)
    grade = ('eq=contrast=1.04:saturation=1.07:gamma=0.99,'
             'colorbalance=rs=0.02:bs=-0.03:rm=0.02:bm=-0.025:rh=0.01:bh=-0.015,'
             'vignette=angle=PI/5:mode=forward')
    def render(final, with_caps):
        inputs = ['-i', str(base), '-i', str(mix)]
        fc = [f'[0:v]{grade}[g0]']
        cur = 'g0'
        for j, (png, a, b, anim) in enumerate(ovl):
            inputs += ['-loop', '1', '-t', str(TOTAL), '-i', str(png)]
            k = j + 2; d = 0.45
            fx = f'[{k}:v]format=rgba,fade=t=in:st={a}:d={d}:alpha=1,fade=t=out:st={b - 0.35}:d=0.35:alpha=1'
            if anim == 'scale':
                fx += f",scale=w='iw*(0.92+0.08*min(1,max(0,(t-{a})/{d})))':h=-1:eval=frame"
                pos = "x='(W-w)/2':y='(H-h)/2'"
            elif anim == 'slide':
                pos = f"x=0:y='22*max(0,1-(t-{a})/{d})'"
            else:
                pos = 'x=0:y=0'
            fc.append(f'{fx}[o{j}]')
            fc.append(f"[{cur}][o{j}]overlay={pos}:enable='between(t,{a},{b})':eval=frame[g{j + 1}]")
            cur = f'g{j + 1}'
        if with_caps:
            fc.append(f"[{cur}]ass={WORK / 'legendas.ass'}:fontsdir={FONTS}[gc]"); cur = 'gc'
        fc.append(f'[{cur}]fade=t=in:st=0:d=0.25,fade=t=out:st={TOTAL - 0.7}:d=0.7,format=yuv420p[v]')
        run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fc),
             '-map', '[v]', '-map', '1:a', '-t', str(TOTAL),
             '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow', '-crf', '17', '-maxrate', '20M', '-bufsize', '40M',
             '-r', str(FPS), '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(final)])
    render(WORK / 'EP01_PumpkinFarm_final.mp4', True)
    render(WORK / 'EP01_PumpkinFarm_sem_legendas.mp4', False)
    print('ok')

if __name__ == '__main__':
    main()
