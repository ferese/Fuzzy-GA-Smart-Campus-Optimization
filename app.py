from __future__ import annotations

import json
import math
import random
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import webbrowser

ROOT = Path(__file__).resolve().parent
ZONES = [
    ("Lecture Hall A", 180, .76, 61, 25.0), ("Lecture Hall B", 150, .58, 57, 24.5),
    ("AI Lab", 105, .72, 64, 25.5), ("Computer Lab", 120, .66, 60, 25.0),
    ("Library", 240, .34, 54, 24.0), ("Seminar Room", 85, .48, 58, 25.0),
    ("Faculty Office", 130, .28, 52, 24.5), ("Cafeteria", 210, .62, 67, 26.0),
    ("Meeting Room", 75, .40, 55, 24.5), ("Study Area", 165, .43, 59, 25.0),
    ("Electronics Lab", 115, .69, 63, 25.5), ("Admin Block", 190, .25, 51, 24.0),
]
OUTDOOR_C = 33.0
HOUR = 14
CO2_OUT = 420.0


def tri(x: float, a: float, b: float, c: float) -> float:
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    return min((x-a)/(b-a), (c-x)/(c-b))


def trap(x: float, a: float, b: float, c: float, d: float) -> float:
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x-a)/(b-a) if b != a else 1.0
    return (d-x)/(d-c) if d != c else 1.0


def memberships(x: float, kind: str) -> list[float]:
    if kind == "occupancy":
        return [trap(x, 0, 0, .18, .45), tri(x, .22, .5, .78), trap(x, .58, .82, 1, 1)]
    if kind == "outdoor":
        y = (x - 18) / 26
        return [trap(y, 0, 0, .18, .44), tri(y, .25, .52, .78), trap(y, .58, .82, 1, 1)]
    if kind == "air":
        y = (x - 400) / 1200
        return [trap(y, 0, 0, .16, .42), tri(y, .25, .5, .76), trap(y, .58, .82, 1, 1)]
    if kind == "humidity":
        return [trap(x, 20, 20, 34, 48), tri(x, 38, 53, 68), trap(x, 60, 76, 90, 90)]
    if kind == "offset":
        return [trap(x, -2, -2, -.6, .25), tri(x, -.45, .65, 1.75), trap(x, 1.15, 2.2, 3, 3)]
    if kind == "time":
        return [trap(x, 0, 0, 6, 9), trap(x, 7, 10, 15, 18), trap(x, 16, 19, 24, 24)]
    return [0, 0, 0]


def fuzzy_cri(occ: float, outdoor: float, rh: float, co2: float, offset: float, hour: float) -> float:
    """Mamdani-style max-min inference using 27 readable three-antecedent rules."""
    m_occ = memberships(occ, "occupancy")
    m_out = memberships(outdoor, "outdoor")
    m_air = memberships(co2, "air")
    m_rh = memberships(rh, "humidity")
    m_off = memberships(offset, "offset")
    m_time = memberships(hour, "time")
    # Rule table: each of the 27 occupancy/weather/air combinations has a consequent.
    # The consequent combines the three linguistic levels into a graded risk label.
    labels = [0.08, 0.28, 0.5, 0.72, 0.92]
    output = [0.0] * 41
    for oi in range(3):
        for wi in range(3):
            for ai in range(3):
                strength = min(m_occ[oi], m_out[wi], m_air[ai])
                risk = .10 + .28*oi + .22*wi + .25*ai
                # Decision- and context-dependent rules refine the base risk.
                # High setpoint offset, humid air, and occupied hours raise risk.
                risk += .10*max(m_off[2], .5*m_off[1])
                risk += .06*m_rh[2] + .04*m_time[1]
                risk = max(0.0, min(1.0, risk))
                consequent = min(4, int(risk*5))
                center = labels[consequent]
                for j in range(41):
                    y = j / 40
                    mu = max(0.0, 1.0 - abs(y-center)/.19)
                    output[j] = max(output[j], min(strength, mu))
    area = sum(output)
    return sum((i/40)*mu for i, mu in enumerate(output))/area if area else .12


def pmv(ta: float, rh: float) -> float:
    """Fanger PMV approximation (clo=0.5, met=1.2, v=0.1 m/s, tr=ta)."""
    met, clo, vel, tr = 1.2, .5, .1, ta
    pa = rh * 10 * math.exp(16.6536 - 4030.183/(ta + 235))
    icl = .155 * clo
    m = met * 58.15
    w = 0.0
    mw = m - w
    fcl = 1.05 + .645*icl if icl > .078 else 1 + 1.29*icl
    hcf = 12.1 * math.sqrt(vel)
    taa, tra = ta + 273, tr + 273
    tcla = taa + (35.5-ta)/(3.5*icl+0.1)
    p1 = icl*fcl
    p2 = p1*3.96
    p3 = p1*100
    p4 = p1*taa
    xn = tcla/100
    xf = xn
    for _ in range(150):
        xf = (xf + xn)/2
        hcn = 2.38*abs(100*xf-taa)**.25
        hc = max(hcf, hcn)
        # Standard clothing-surface iteration, with radiation and convection.
        p5 = 308.7 - .028*mw + p2*(tra/100)**4
        xn_new = (p5 + p4*hc - p2*xf**4)/(100 + p3*hc)
        if abs(xn_new-xf) <= .00015:
            xn = xn_new
            break
        xn = xn_new
    tcl = 100*xn - 273
    hc = max(hcf, 2.38*abs(tcl-ta)**.25)
    hl1 = 3.05e-3*(5733-6.99*mw-pa)
    hl2 = .42*(mw-58.15) if mw > 58.15 else 0
    hl3 = 1.7e-5*m*(5867-pa)
    hl4 = .0014*m*(34-ta)
    hl5 = 3.96e-8*fcl*((tcl+273)**4-(tr+273)**4)
    hl6 = fcl*hc*(tcl-ta)
    return (0.303*math.exp(-.036*m)+.028)*(mw-hl1-hl2-hl3-hl4-hl5-hl6)


def evaluate(g: list[float], weight: float, lam: float) -> dict:
    energy, risks, pmvs, occupied_violations = 0.0, [], [], []
    details = []
    for i, (name, area, occ, rh, current) in enumerate(ZONES):
        t, vent, light = g[3*i:3*i+3]
        occ_count = occ*area/2.2
        co2 = CO2_OUT + 20000*occ_count/(max(1, area*8*vent))
        offset = t-24.0
        cri = fuzzy_cri(occ, OUTDOOR_C, rh, co2, offset, HOUR)
        # Relative one-hour energy proxy; calibrated coefficients are synthetic.
        hvac = .050*(OUTDOOR_C-t)**2*area/100 + .018*vent*occ_count
        lighting = .045*light*area/10
        e = hvac + lighting
        p = pmv(t, rh)
        energy += e
        risks.append(cri)
        pmvs.append(abs(p))
        if occ >= .15:
            occupied_violations.append(abs(p) > .5)
        details.append({"name":name,"setpoint":round(t,2),"ventilation":round(vent,2),"lighting":round(light,2),"occupancy":round(occ,2),"co2":round(co2),"cri":round(cri,3),"pmv":round(p,3),"energy":round(e,2)})
    # Normalize this horizon relative to an explicit fixed schedule reference.
    normalized_energy = energy / 200.0
    mean_cri = sum(risks)/len(risks)
    comfort_excess = sum(r*max(0, p-.5) for r,p in zip(risks, pmvs))
    objective = (1-weight)*normalized_energy + weight*mean_cri + lam*comfort_excess/len(ZONES)
    return {"energy":energy,"mean_pmv":sum(pmvs)/len(pmvs),"ppd":sum(100-95*math.exp(-.03353*p**4-.2179*p**2) for p in pmvs)/len(pmvs),"cvr":100*sum(occupied_violations)/max(1,len(occupied_violations)),"mean_cri":mean_cri,"objective":objective,"zones":details}


def initial() -> list[float]:
    out=[]
    for _ in ZONES:
        out.extend([24.0, 1.0, 1.0])
    return out


def optimize(weight: float=.4, seed: int=7, population: int=44, generations: int=70) -> dict:
    rng=random.Random(seed)
    bounds=[(22,27),(.3,1),(.2,1)]*len(ZONES)
    incumbent=initial()
    baseline=evaluate(incumbent,weight,0)
    pop=[]
    for n in range(population):
        if n == 0:
            pop.append(incumbent.copy()); continue
        individual=[]
        for j,(lo,hi) in enumerate(bounds):
            individual.append(rng.uniform(lo,hi) if n%10 else incumbent[j])
        pop.append(individual)
    trace=[]
    best=None
    for gen in range(generations):
        lam=2.0*(1+gen/max(1,generations-1))
        scored=[(evaluate(x,weight,lam)["objective"],x) for x in pop]
        scored.sort(key=lambda q:q[0])
        best=scored[0][1].copy()
        trace.append(round(scored[0][0],5))
        nextpop=[scored[0][1].copy(),scored[1][1].copy()]
        while len(nextpop)<population:
            def select():
                return min((rng.choice(scored) for _ in range(3)),key=lambda x:x[0])[1]
            p1,p2=select(),select()
            child=[]
            for j,(lo,hi) in enumerate(bounds):
                # Simulated-binary-style real-valued crossover.
                u=rng.random()
                beta=(2*u)**(1/16) if u<=.5 else (1/(2*(1-u)))**(1/16)
                val=.5*((1+beta)*p1[j]+(1-beta)*p2[j])
                if rng.random()<1/len(bounds):
                    # Polynomial mutation (distribution index eta_m = 20).
                    span=hi-lo
                    delta1=(val-lo)/span
                    delta2=(hi-val)/span
                    u=rng.random()
                    power=1/21
                    if u<.5:
                        xy=1-delta1
                        deltaq=(2*u+(1-2*u)*(xy**21))**power-1
                    else:
                        xy=1-delta2
                        deltaq=1-(2*(1-u)+2*(u-.5)*(xy**21))**power
                    val+=deltaq*span
                child.append(min(hi,max(lo,val)))
            nextpop.append(child)
        pop=nextpop
    optimized=evaluate(best,weight,4.0)
    savings=100*(baseline["energy"]-optimized["energy"])/baseline["energy"]
    return {"scenario":{"zones":len(ZONES),"outdoor_c":OUTDOOR_C,"hour":HOUR,"weight":weight,"seed":seed,"population":population,"generations":generations,"data_note":"Synthetic one-hour scenario for demonstration; coefficients and occupancy are illustrative, not metered campus data."},"baseline":baseline,"optimized":optimized,"savings_pct":savings,"trace":trace}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path == "/":
            data=(ROOT/"index.html").read_bytes()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
        else:
            self.send_error(404)
    def do_POST(self):
        if urlparse(self.path).path != "/api/optimize":
            self.send_error(404); return
        try:
            n=int(self.headers.get("Content-Length",0)); payload=json.loads(self.rfile.read(n) or b"{}")
            weight=max(.2,min(.6,float(payload.get("weight",.4))))
            seed=max(0,min(99999,int(payload.get("seed",7))))
            result=optimize(weight,seed)
            raw=json.dumps(result).encode()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
        except Exception as exc:
            raw=json.dumps({"error":str(exc)}).encode()
            self.send_response(400); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def log_message(self, *_): pass


if __name__ == "__main__":
    server=ThreadingHTTPServer(("127.0.0.1",8765),Handler)
    print("Fuzzy-GA demo is ready at http://127.0.0.1:8765 (Ctrl+C to stop)")
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:8765")).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nServer stopped.")
    finally: server.server_close()
