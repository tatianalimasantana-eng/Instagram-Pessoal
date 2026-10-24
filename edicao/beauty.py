"""Leve 'maquiagem' digital: pele suavizada, tom uniforme, leve blush. Uso:
   beauty.py image in.jpg out.jpg | beauty.py video in.mp4 out.mp4"""
import cv2, numpy as np, sys, subprocess
CASC = [cv2.CascadeClassifier(cv2.data.haarcascades + f) for f in ('haarcascade_frontalface_default.xml', 'haarcascade_frontalface_alt2.xml')]

def detect(img):
    sc = 360 / img.shape[1]; g = cv2.cvtColor(cv2.resize(img, None, fx=sc, fy=sc), cv2.COLOR_BGR2GRAY)
    g = cv2.equalizeHist(g)
    for c in CASC:
        f = c.detectMultiScale(g, 1.1, 5, minSize=(60, 60))
        if len(f): x, y, w, h = max(f, key=lambda r: r[2]*r[3]); return np.array([x, y, w, h], float) / sc
    return None

def beautify(img, box, strength=1.0):
    H, W = img.shape[:2]; x, y, w, h = box
    # region: face + neck, with margin
    x0, y0 = int(max(0, x - 0.35*w)), int(max(0, y - 0.35*h)); x1, y1 = int(min(W, x + 1.35*w)), int(min(H, y + 2.0*h))
    roi = img[y0:y1, x0:x1].astype(np.float32)
    if roi.size == 0: return img
    # skin mask (YCrCb) limited to soft face/neck ellipses
    ycc = cv2.cvtColor(roi.astype(np.uint8), cv2.COLOR_BGR2YCrCb)
    skin = cv2.inRange(ycc, (40, 133, 77), (255, 178, 133)).astype(np.float32) / 255
    shape = np.zeros(skin.shape, np.float32)
    cx, cy = x + w/2 - x0, y + h*0.52 - y0
    cv2.ellipse(shape, (int(cx), int(cy)), (int(w*0.56), int(h*0.72)), 0, 0, 360, 1, -1)
    cv2.ellipse(shape, (int(cx), int(cy + h*0.95)), (int(w*0.42), int(h*0.55)), 0, 0, 360, 1, -1)
    cv2.ellipse(shape, (int(cx), int(y + h*0.84 - y0)), (int(w*0.22), int(h*0.09)), 0, 0, 360, 0, -1)  # lábios
    k = int(w*0.08) | 1
    m = cv2.GaussianBlur(skin * shape, (k, k), 0)
    m = cv2.GaussianBlur(m, (k*2+1, k*2+1), 0)
    # smoothing that keeps a bit of texture (not plastic)
    u8 = roi.astype(np.uint8)
    sm = cv2.bilateralFilter(u8, 0, 24, max(3, w*0.016)).astype(np.float32)
    fine = roi - cv2.GaussianBlur(roi, (0, 0), 1.0)
    ret = sm + 0.45*fine
    # base: slightly brighter, warmer, more even
    ret = ret*1.03 + np.array([0, 2, 4], np.float32)
    # soft blush on cheeks
    bl = np.zeros(skin.shape, np.float32)
    for fx in (0.24, 0.76):
        cv2.circle(bl, (int(x + w*fx - x0), int(y + h*0.64 - y0)), int(w*0.12), 1, -1)
    bl = cv2.GaussianBlur(bl, (0, 0), w*0.07) * m
    ret = ret*(1 - 0.14*bl[..., None]) + np.array([120, 105, 215], np.float32)*(0.14*bl[..., None])
    a = (m*0.78*strength)[..., None]
    out = img.copy(); out[y0:y1, x0:x1] = np.clip(roi*(1-a) + ret*a, 0, 255).astype(np.uint8)
    return out

if sys.argv[1] == 'image':
    im = cv2.imread(sys.argv[2]); b = detect(im); print('face', b)
    cv2.imwrite(sys.argv[3], beautify(im, b) if b is not None else im, [cv2.IMWRITE_JPEG_QUALITY, 97])
else:
    src, dst = sys.argv[2], sys.argv[3]; W, H = 1080, 1920
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                            '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
    box = None; miss = 0; n = 0
    while True:
        buf = dec.stdout.read(W*H*3)
        if len(buf) < W*H*3: break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        if n % 2 == 0:
            d = detect(f)
            if d is not None:
                # ignore a jump (likely false detection) unless face was lost for a while
                if box is None or miss > 15 or np.abs(d - box).max() < 0.35*box[2]:
                    box = d if box is None or miss > 15 else box*0.6 + d*0.4; miss = 0
                else: miss += 1
            else: miss += 1
        out = beautify(f, box) if box is not None and miss < 45 else f
        enc.stdin.write(out.tobytes()); n += 1
    enc.stdin.close(); enc.wait(); print('frames', n)
