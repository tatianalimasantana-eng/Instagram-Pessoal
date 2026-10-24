import json, subprocess, os, sys, numpy as np
S = os.path.dirname(os.path.abspath(__file__))
U = '/root/.claude/uploads/4d342b99-ed95-5201-aef9-d733bd00a735'
W = json.load(open(f'{S}/work/words.json'))
FPS = 30
ORDER = ['dd4b41c5','a6b5dbbe','2ed9fba4','149ca9e6','8b3f22f5','02d9f7c7','75c502d4','dcdf2e84','BROLL','948b9afe','c8844da9','d7e8f734','95c009cd']
BROLL = '1d7303ea'
# ASR fixes: take -> {word index: new text or None to merge into previous}
FIX = {
 '149ca9e6': {0:'Vou',1:'ser',2:'sincera,'},
 '8b3f22f5': {10:'Sair', 27:'infoprodutos.', 28:None},
 'dcdf2e84': {5:'mais',6:'normal'},
 '948b9afe': {7:'e tô'},
 'd7e8f734': {7:'o',8:'desenrolar'},
}
EMPH = {'real.','descoberta','pausa.','Insights,','Horizon,','sincera,','rumo','transição.','infoprodutos.','largar','duas','firmar.','normal','dúvida.','clareza','diferente.','série','comentários,','também?','profissional.','ninguém'}

def src(k): return [os.path.join(U,f) for f in os.listdir(U) if f.startswith(k) and f.endswith('.mov')][0]
def wkey(k): return [x for x in W if x.startswith(k)][0]

def words(k):
    ws = [list(w) for w in W[wkey(k)]]
    fx = FIX.get(k, {})
    out = []
    for i, (a, b, t) in enumerate(ws):
        t = t.strip()
        if i in fx:
            if fx[i] is None: out[-1][1] = b; continue
            t = fx[i]
        out.append([a, b, t])
    return out

def speech_intervals(k, ws):
    a = np.fromfile(f'{S}/work/wav/{os.path.basename(wkey(k))}', dtype=np.float32)
    win = 320  # 20ms
    rms = np.array([20*np.log10(np.sqrt(np.mean(a[i:i+win]**2))+1e-9) for i in range(0, len(a)-win, win)])
    on = rms > -44
    runs = []; i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]: j += 1
            runs.append([i*0.02, j*0.02]); i = j
        else: i += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < 0.28: merged[-1][1] = r[1]
        else: merged.append(r)
    dur = len(a)/16000
    # keep only runs that overlap a word midpoint (drops clicks/breaths)
    mids = [((w[0] if j else max(w[0], w[1]-0.6)) + w[1])/2 for j, w in enumerate(ws)]
    keep = [r for r in merged if any(r[0]-0.1 <= m <= r[1]+0.1 for m in mids) and r[1]-r[0] > 0.12]
    out = []
    for s, e in keep:
        s = max(0, s-0.07); e = min(dur, e+0.12)
        s = round(s*FPS)/FPS; e = round(e*FPS)/FPS
        if out and s <= out[-1][1]: out[-1][1] = e
        else: out.append([s, e])
    return out

segs = []   # dict(src, s, e, speed, zoom, take)
caps = []   # [start, end, text] in output timeline
t_out = 0.0
zoom_toggle = 0
for ti, k in enumerate(ORDER):
    if k == 'BROLL':
        s, e, sp = 0.3, 6.0, 3.0
        d = round((e-s)/sp*FPS)/FPS
        segs.append(dict(src=src(BROLL), s=s, e=e, speed=sp, zoom=(1.0, 1.0), take='broll', out=t_out, d=d))
        broll_at = (t_out, t_out+d)
        t_out += d
        continue
    ws = words(k)
    iv = speech_intervals(k, ws)
    ws[0][0] = max(ws[0][0], iv[0][0] + 0.05)
    mapping = []
    for n, (s, e) in enumerate(iv):
        z0 = 1.0 if zoom_toggle % 2 == 0 else 1.13
        z = (z0, z0 + 0.04) if (ti == 0 and n == 0) else (z0, z0)
        zoom_toggle += 1
        d = e - s
        segs.append(dict(src=src(k), s=s, e=e, speed=1.0, zoom=z, take=k, out=t_out, d=d))
        mapping.append((s, e, t_out)); t_out += d
    def m(t):
        for s, e, o in mapping:
            if t < s: return o
            if t <= e: return o + (t - s)
        return mapping[-1][2] + mapping[-1][1] - mapping[-1][0]
    for a, b, t in ws:
        caps.append([m(a), m(b), t])
TOTAL = t_out
print('total', round(TOTAL, 2), 'segments', len(segs))
json.dump(dict(segs=segs, caps=caps, total=TOTAL, broll=broll_at, emph=sorted(EMPH)), open(f'{S}/work/plan.json','w'), ensure_ascii=False, indent=1)
