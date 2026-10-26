"""SRMC data logger: reads the ESP32 serial lines and writes a CSV that score_week.js can score.

  python srmc_logger.py --port COM5 --out week_real.csv            log from the board (Ctrl+C to stop; append to the same file to continue)
  python srmc_logger.py --simulate --out week_fake.csv              no hardware: write a FAKE week with the same columns (rehearsal)
  python srmc_logger.py --list                                      list serial ports

Serial line from the board (115200 baud):  SRMC,ms,tempC,rh,soilRaw,rainWet,rainRaw[,ghiWm2,parUmol[,windMs]]
One CSV row is written every --interval seconds (default 300) from the median of the readings in that window:
  timestamp (local time with UTC offset), ms, tempC, rh, soilRaw, rain, rainRaw, ghi, par, wind, angleDeg
tempC/rh are -999 when the DHT11 could not be read for the whole window. angleDeg = the panel angle in use (--angle 30 for fixed panels; leave empty if unknown).
Then score it:  node score_week.js week_real.csv --dry 3200 --wet 1300      (ESP32 soil raw values: dry in air = --dry, wet in water = --wet)
"""
import argparse, csv, os, statistics, subprocess, sys, time
from datetime import datetime, timezone

HEAD = ['timestamp', 'ms', 'tempC', 'rh', 'soilRaw', 'rain', 'rainRaw', 'ghi', 'par', 'wind', 'angleDeg']
HERE = os.path.dirname(os.path.abspath(__file__))


def parse(line):
    p = line.strip().split(',')
    if not p or p[0] != 'SRMC' or len(p) not in (7, 9, 10):
        return None
    try:
        v = [float(x) for x in p[1:]]
    except ValueError:
        return None
    if v[4] not in (0.0, 1.0):
        return None
    return {'ms': v[0], 'tempC': v[1], 'rh': v[2], 'soilRaw': v[3], 'rain': int(v[4]), 'rainRaw': v[5],
            'ghi': v[6] if len(v) > 6 else None, 'par': v[7] if len(v) > 7 else None, 'wind': v[8] if len(v) > 8 else None}


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def stamp():
    t = datetime.now(timezone.utc).astimezone()
    return t.isoformat(timespec='seconds')


def window_row(buf, angle):
    ok = [b for b in buf if b['tempC'] > -100 and 0 <= b['rh'] <= 100]
    last = buf[-1]
    f = lambda v, d=1: '' if v is None else round(v, d)
    return [stamp(), int(last['ms']), f(med([b['tempC'] for b in ok])) if ok else -999, f(med([b['rh'] for b in ok])) if ok else -999,
            int(med([b['soilRaw'] for b in buf])), 1 if any(b['rain'] for b in buf) else 0, int(min(b['rainRaw'] for b in buf)),
            f(med([b['ghi'] for b in buf])), f(med([b['par'] for b in buf])), f(max([b['wind'] for b in buf if b['wind'] is not None], default=None)), '' if angle is None else angle]


def main():
    ap = argparse.ArgumentParser(description='SRMC serial logger')
    ap.add_argument('--port'); ap.add_argument('--baud', type=int, default=115200); ap.add_argument('--out', default='week_real.csv')
    ap.add_argument('--interval', type=int, default=300); ap.add_argument('--angle', type=float, default=None)
    ap.add_argument('--simulate', action='store_true'); ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    if a.list:
        import serial.tools.list_ports as lp
        for p in lp.comports(): print(p.device, p.description)
        return
    if a.simulate:
        subprocess.check_call(['node', os.path.join(HERE, 'make_fake_week.js'), a.out]); return
    if not a.port:
        sys.exit('give --port COM5 (see --list), or use --simulate')
    import serial
    new = not os.path.exists(a.out) or os.path.getsize(a.out) == 0
    f = open(a.out, 'a', newline='', encoding='utf-8'); w = csv.writer(f)
    if new:
        f.write('# SRMC real log. Columns as in score_week.js; angleDeg = panel angle in use (blank = unknown)\n'); w.writerow(HEAD); f.flush()
    buf, t0, n = [], time.time(), 0
    print('logging from', a.port, 'every', a.interval, 's to', a.out, '(Ctrl+C to stop)')
    while True:
        try:
            with serial.serial_for_url(a.port, baudrate=a.baud, timeout=2) as s:
                while True:
                    line = s.readline().decode('utf-8', 'ignore')
                    r = parse(line) if line else None
                    if r: buf.append(r)
                    if time.time() - t0 >= a.interval and buf:
                        w.writerow(window_row(buf, a.angle)); f.flush(); n += 1
                        print(n, 'rows,', len(buf), 'readings in the last window'); buf, t0 = [], time.time()
        except KeyboardInterrupt:
            print('stopped,', n, 'rows written'); f.close(); return
        except Exception as e:
            print('serial problem:', e, '- retrying in 5 s'); time.sleep(5)


if __name__ == '__main__':
    main()
