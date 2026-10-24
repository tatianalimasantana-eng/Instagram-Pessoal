import json, subprocess, os, re
S = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(f'{S}/work/plan.json'))
OUT = '/home/user/Instagram-Pessoal/reels'
os.makedirs(f'{S}/work/seg', exist_ok=True); os.makedirs(OUT, exist_ok=True)
FPS = 30
def run(c): subprocess.run(c, check=True)

# 1) segments
lst = []
for i, g in enumerate(P['segs']):
    o = f'{S}/work/seg/{i:02d}.mp4'; lst.append(o)
    d = g['d']; z0, z1 = g['zoom']; sp = g['speed']
    if z0 == z1:
        sc = f"scale={int(1080*z0)//2*2}:-2,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.25"
    else:
        zt = f"({z0}+({z1-z0})*t/{d:.3f})"
        sc = f"scale=w='trunc(1080*{zt}/2)*2':h=-2:eval=frame,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.25"
    vf = f"setpts=(PTS-STARTPTS)/{sp},{sc},eq=contrast=1.06:saturation=1.08:gamma=1.02,unsharp=5:5:0.4,fps={FPS},format=yuv420p"
    af = "asetpts=PTS-STARTPTS"
    if sp != 1: af += f",atempo=2,atempo={sp/2},volume=0.35"
    af += f",afade=t=in:d=0.015,afade=t=out:st={d-0.025:.3f}:d=0.025,aresample=48000"
    if os.path.exists(o.replace('.mp4','.mov')) and os.environ.get('KEEP'):
        lst[-1] = o.replace('.mp4','.mov'); continue
    run(['ffmpeg','-v','error','-y','-ss',f"{g['s']:.3f}",'-to',f"{g['e']:.3f}",'-i',g['src'],'-vf',vf,'-af',af,
         '-t',f'{d:.3f}','-c:v','libx264','-preset','fast','-crf','16','-c:a','pcm_s16le','-ac','2',o.replace('.mp4','.mov')])
    os.replace(o.replace('.mp4','.mov'), o) if False else None
    lst[-1] = o.replace('.mp4','.mov')
open(f'{S}/work/list.txt','w').write(''.join(f"file '{x}'\n" for x in lst))

# 2) captions (ASS)
def ts(t):
    t = max(0, t); h = int(t//3600); m = int(t%3600//60); s = t%60
    return f"{h}:{m:02d}:{s:05.2f}"
EMPH = set(w.lower() for w in P['emph'])
YEL = '&H5CD4FF&'  # #FFD45C
caps = [c for c in P['caps']]
groups = []; cur = []
for c in caps:
    if cur and (len(cur) >= 3 or re.search(r'[.,?!]$', cur[-1][2]) or c[0]-cur[-1][1] > 0.45
                or sum(len(x[2]) for x in cur)+len(c[2]) > 17):
        groups.append(cur); cur = []
    cur.append(c)
groups.append(cur)
ev = []
for gi, g in enumerate(groups):
    gend = groups[gi+1][0][0] if gi+1 < len(groups) else P['total']
    gend = min(gend, g[-1][1] + 0.6)
    for wi, w in enumerate(g):
        a = w[0]; b = g[wi+1][0] if wi+1 < len(g) else gend
        if b - a < 0.02: continue
        parts = []
        for wj, x in enumerate(g):
            t = x[2]; is_e = t.lower() in EMPH
            base = r'{\fnFira BoldItalic\fs104\c' + YEL + '}' if is_e else r'{\fnFira BoldItalic\fs90\c&HFFFFFF&}'
            if wj == wi:
                pop = r'{\fscx118\fscy118\t(0,110,\fscx106\fscy106)' + (r'\c' + YEL if not is_e else '') + '}'
                parts.append(base + pop + t + r'{\fscx100\fscy100}')
            elif wj > wi:
                parts.append(base + r'{\alpha&H55&}' + t + r'{\alpha&H00&}')
            else:
                parts.append(base + t)
        intro = r'{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}' if wi == 0 else ''
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{intro}{' '.join(parts)}")
b0, b1 = P['broll']
ev.append(f"Dialogue: 2,{ts(b0)},{ts(b1)},Big,,0,0,0,,{{\\fad(150,150)\\fscx90\\fscy90\\t(0,{int((b1-b0)*1000)},\\fscx105\\fscy105)}}um tempo depois…")
ev.append(f"Dialogue: 0,{ts(0)},{ts(P['total'])},Tag,,0,0,0,,papo enquanto me arrumo  ·  ep. 01")
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Fira BoldItalic,90,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,0,0,0,0,100,100,0,0,1,7,3,2,60,60,520,1
Style: Big,Fira SemiItalic,120,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,0,0,0,0,100,100,0,0,1,5,4,5,60,60,0,1
Style: Tag,Fira MediumItalic,42,&H00FFFFFF,&H00FFFFFF,&H70000000,&H70000000,0,0,0,0,100,100,1,0,3,16,0,8,60,60,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + '\n'.join(ev) + '\n'
open(f'{S}/work/caps.ass','w').write(ass)

# 3) final
T = P['total']
fc = (f"[0:v]subtitles={S}/work/caps.ass:fontsdir={S}/fonts[v1];"
      f"color=c=0xFFD45C:s=1080x10:r={FPS}[bar];"
      f"[v1][bar]overlay=x='-W+W*t/{T:.3f}':y=H-10:shortest=1,format=yuv420p[v];"
      f"[0:a]highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]")
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',f'{S}/work/list.txt','-filter_complex',fc,'-map','[v]','-map','[a]',
     '-c:v','libx264','-preset','slow','-crf','20','-profile:v','high','-r',str(FPS),'-c:a','aac','-b:a','192k','-movflags','+faststart',
     '-t',f'{T:.3f}',f'{OUT}/reels-ep01-final.mp4'])
print('done')
