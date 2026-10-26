"""Records the 3D mechanism viewer to an MP4 (headless Chrome with software WebGL + ffmpeg).
Needs: a local web server on port 8766 serving the srmc-twin folder (python -m http.server 8766), Chrome, ffmpeg.   python make_mechanism_video.py [seconds] [resume_from_frame]"""
import os, sys, threading, http.server, subprocess, shutil, tempfile, time, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
OUTDIR = os.path.join(ROOT, 'results', 'mechanism_3d'); FR = os.path.join(tempfile.gettempdir(), 'srmc_mech_frames')
FROM = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # resume: keep frames already rendered
if FROM == 0: shutil.rmtree(FR, ignore_errors=True)
os.makedirs(FR, exist_ok=True)
class H(http.server.BaseHTTPRequestHandler):
    def _c(self):
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', '*'); self.send_header('Access-Control-Allow-Methods', 'POST,OPTIONS')
    def do_OPTIONS(self): self.send_response(204); self._c(); self.end_headers()
    def do_POST(self):
        b = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if self.path.startswith('/f/'): open(os.path.join(FR, 'f%05d.jpg' % int(self.path[3:])), 'wb').write(b)
        elif self.path == '/done': open(os.path.join(FR, 'DONE'), 'w').write('1')
        self.send_response(200); self._c(); self.end_headers()
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8767), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
secs = sys.argv[1] if len(sys.argv) > 1 else ''
url = 'http://localhost:8766/Review1_Design_and_CAD/results/mechanism_3d/SRMC_Mechanism_3D.html?record=1&ui=0&lab=0' + ('&secs=' + secs if secs else '') + ('&from=%d' % FROM if FROM else '')
chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'; prof = tempfile.mkdtemp(prefix='srmc_chrome_')
p = subprocess.Popen([chrome, '--headless=new', '--no-first-run', '--user-data-dir=' + prof, '--window-size=1280,760', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', url])
t0 = time.time()
while not os.path.exists(os.path.join(FR, 'DONE')) and time.time() - t0 < 3000: time.sleep(2)
p.terminate(); n = len(glob.glob(os.path.join(FR, 'f*.jpg'))); print('frames', n, 'in', int(time.time() - t0), 's')
ff = shutil.which('ffmpeg') or 'ffmpeg'; mp4 = os.path.join(OUTDIR, 'SRMC_Mechanism_Animation.mp4')
subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(FR, 'f%05d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', mp4], check=True)
print(mp4, os.path.getsize(mp4) // 1024, 'KB')
