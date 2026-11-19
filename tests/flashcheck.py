"""Blitzprüfung für Partylichter nach WCAG 2.3.1 (allgemeine Blitze + Rotblitze).

Misst Bild für Bild die relative Leuchtdichte in 8x6 Kacheln (je ~2 % der Fläche,
strenger als die WCAG-Flächenregel) und zählt gegenläufige Helligkeitswechsel
>= 10 %. Mehr als 6 Wechsel (= mehr als 3 Blitze) in einer Sekunde = Fehler.
"""
import asyncio, json, sys
from playwright.async_api import async_playwright

import os
URL = os.environ.get('PL_URL', 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'index.html')))

PROBE = r"""
(() => {
  const c = document.createElement('canvas'); c.width = 64; c.height = 36;
  const x = c.getContext('2d', { willReadFrequently: true });
  const LUT = new Float32Array(256); for (let i = 0; i < 256; i++) { const v = i / 255; LUT[i] = v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
  const st = { on: false, t: [], L: [], R: [], O: [] };
  function tick(t) {
    if (st.on) {
      const g = document.getElementById('gl'); x.drawImage(g && g.style.display !== 'none' ? g : document.getElementById('c'), 0, 0, 64, 36);
      const d = x.getImageData(0, 0, 64, 36).data;
      const L = new Array(48).fill(0), R = new Array(48).fill(0);
      for (let py = 0; py < 36; py++) for (let px = 0; px < 64; px++) {
        const i = (py * 64 + px) * 4, r = d[i], g = d[i + 1], b = d[i + 2];
        const rl = LUT[r], gl = LUT[g], bl = LUT[b];
        const k = Math.floor(py / 6) * 8 + Math.floor(px / 8);
        L[k] += 0.2126 * rl + 0.7152 * gl + 0.0722 * bl;
        const s = r + g + b;
        if (s > 0 && r / s >= 0.8) R[k] += Math.max(0, rl - gl - bl) * 320;
      }
      st.t.push(t); st.L.push(L.map(v => v / 48)); st.R.push(R.map(v => v / 48));
      st.O.push(+getComputedStyle(document.getElementById('freeze')).opacity);
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  window.__probe = st;
})();
"""

def max_transitions(ts, vals, thr, dark_max=None):
    events = []
    ext = vals[0]; d = 0
    for t, v in zip(ts, vals):
        if d >= 0 and v > ext and d == 1: ext = v
        elif d <= 0 and v < ext and d == -1: ext = v
        if abs(v - ext) >= thr and (d == 0 or (v - ext) * d < 0):
            if dark_max is None or min(v, ext) < dark_max:
                events.append(t)
            d = 1 if v > ext else -1
            ext = v
    best = 0; j = 0
    for i in range(len(events)):
        while events[i] - events[j] > 1000: j += 1
        best = max(best, i - j + 1)
    return best

def analyse(st):
    ts = st['t']
    worstL = worstR = 0
    for k in range(48):
        worstL = max(worstL, max_transitions(ts, [f[k] for f in st['L']], 0.10, 0.80))
        worstR = max(worstR, max_transitions(ts, [f[k] for f in st['R']], 20))
    worstO = max_transitions(ts, st['O'], 0.10)
    fps = (len(ts) - 1) / ((ts[-1] - ts[0]) / 1000) if len(ts) > 1 else 0
    return worstL, worstR, worstO, fps

async def run_case(pg, name, setup_js, ms, during=None):
    await pg.evaluate(setup_js)
    await pg.wait_for_timeout(1700)       # Überblendung abwarten
    await pg.evaluate("Object.assign(window.__probe,{t:[],L:[],R:[],O:[]}); window.__probe.on=true")
    if during: await during(pg, ms)
    else: await pg.wait_for_timeout(ms)
    st = await pg.evaluate("window.__probe.on=false; window.__probe")
    L, R, O, fps = analyse(st)
    ok = L <= 6 and R <= 6 and O <= 6
    print(f"{'OK ' if ok else 'FEHLER'}  {name:<42} Helligkeit {L}  Rot {R}  Stopp-Schild {O}  (max. Wechsel/s, erlaubt 6; {fps:.0f} fps)")
    return ok

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        pg = await b.new_page(viewport={'width': 1280, 'height': 720})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL)
        await pg.add_script_tag(content=PROBE)
        await pg.click('#startWin')
        names = {1: 'Farbverlauf', 2: 'Sternenhimmel', 3: 'Discokugel', 4: 'Scheinwerfer', 5: 'Farb-Puls', 6: 'Wellen', 7: 'Lagerfeuer'}
        allok = True
        for n, nm in names.items():
            allok &= await run_case(pg, f'{n} {nm} – Takt 200 BPM', f"__pl.setMode('takt'); __pl.setBpm(200); __pl.setScene({n})", 6000)
            # Mikrofon-Worst-Case: Beat-Signal alle 50 ms mit voller Stärke
            async def spam_beats(pg, ms):
                await pg.evaluate(f"window.__sb=setInterval(()=>__pl.triggerBeat(performance.now(),1),50)")
                await pg.wait_for_timeout(ms)
                await pg.evaluate("clearInterval(window.__sb)")
            allok &= await run_case(pg, f'{n} {nm} – Beat-Dauerfeuer (Mikro)', "__pl.setMode('auto')", 5000, spam_beats)
        # Tastenspam: Szenen hell/dunkel abwechselnd alle 80 ms
        async def spam_scenes(pg, ms):
            await pg.evaluate("window.__ss=setInterval(()=>__pl.setScene(__pl.S.scene===2?5:2),80)")
            await pg.wait_for_timeout(ms)
            await pg.evaluate("clearInterval(window.__ss)")
        allok &= await run_case(pg, 'Tastenspam Sternenhimmel <-> Farb-Puls', "__pl.setScene(2)", 6000, spam_scenes)
        async def spam_freeze(pg, ms):
            for _ in range(ms // 60):
                await pg.keyboard.press('f'); await pg.wait_for_timeout(60)
        allok &= await run_case(pg, 'Tastenspam Freeze (F alle 60 ms)', "__pl.setScene(1)", 4000, spam_freeze)
        print('JS-Fehler:', errs or 'keine')
        print('GESAMT:', 'BESTANDEN' if allok and not errs else 'NICHT BESTANDEN')
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
