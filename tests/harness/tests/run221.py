# R2-04: board-fetch avatars against a real local HTTPS server with real curl.
# A wrapper points every host (localhost is the configured one) at the test server and
# trusts its one-off certificate; every other curl flag is board-fetch's own.
import base64, http.server, json, os, pathlib, ssl, subprocess, sys, tempfile, threading
src = pathlib.Path(sys.argv[1]).resolve()
passed = failed = 0
def ok(name, value, extra=""):
    global passed, failed
    if value: passed += 1
    else: failed += 1; print("FAIL", name, extra)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAFElEQVR4nGO0zlvBAANMDEgANwcAQmkBWeHkvAIAAAAASUVORK5CYII=")
seen = []
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        seen.append(self.headers.get("Host") + self.path)
        path = self.path.split("?")[0]
        if path == "/redirect":
            self.send_response(302); self.send_header("Location", "https://outside.invalid/pic.png"); self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(PNG))); self.end_headers(); self.wfile.write(PNG); return
        if path == "/same-host-redirect":
            self.send_response(302); self.send_header("Location", "/pic.png"); self.end_headers(); return
        body, kind, length = PNG, "image/png", True
        if path == "/big.png": body = PNG + b"\0" * 70000
        if path == "/big-unsized.png": body, length = PNG + b"\0" * 70000, False
        if path == "/page.png": body, kind = b"<html></html>", "text/html"
        self.send_response(200); self.send_header("Content-Type", kind)
        if length: self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
with tempfile.TemporaryDirectory() as td:
    d = pathlib.Path(td); (d / "bin").mkdir(); (d / "home").mkdir()
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1", "-subj", "/CN=localhost",
                    "-addext", "subjectAltName=DNS:localhost,DNS:outside.invalid,DNS:localhost.outside.invalid,IP:127.0.0.1", "-keyout", str(d / "k.pem"), "-out", str(d / "c.pem")],
                   check=True, capture_output=True)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(d / "c.pem", d / "k.pem")
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_port
    real = subprocess.check_output(["bash", "-c", "command -v curl"], text=True).strip()
    (d / "bin/curl").write_text('#!/bin/bash\nfirst=$1; shift\nca=(--cacert "$CA"); [[ -n ${NOCA:-} ]] && ca=()\n'
                                'exec %s "$first" --connect-to ::127.0.0.1:%d "${ca[@]}" "$@"\n' % (real, port))
    (d / "bin/curl").chmod(0o755)
    os.symlink(src / "tests/fake-glab", d / "bin/glab")
    (d / "home/.curlrc").write_text("insecure\nlocation\n")
    env = dict(os.environ, PATH=str(d / "bin") + ":" + os.environ["PATH"], CA=str(d / "c.pem"), HOME=str(d / "home"),
               FAKE_DIR=str(d), FAKE_LOG=str(d / "calls"))
    def run(urls, **extra):
        seen.clear()
        out = subprocess.run([str(src / "board-fetch"), "avatars", "--hostname", "localhost"], input="".join(u + "\n" for u in urls),
                             env=dict(env, **extra), capture_output=True, text=True, timeout=60).stdout
        return json.loads(out)
    U = lambda p: "https://localhost/" + p
    a = run([U("pic.png?v=1")])
    ok("A1 a picture on the server comes back as a data URL", a == {"state": "ready", "avatars": {U("pic.png?v=1"): "data:image/png;base64," + base64.b64encode(PNG).decode()}}, a)
    ok("A2 GitLab's resizer is asked for 64 px", seen == ["localhost/pic.png?v=1&width=64"], seen)
    run([U("pic.png")])
    ok("A3 ... with ? when the URL has no query", seen == ["localhost/pic.png?width=64"], seen)
    a = run([U("redirect")])
    ok("A4 a redirect to another host is not followed, and its own body is no picture: initials", a["avatars"] == {U("redirect"): ""} and seen == ["localhost/redirect?width=64"], (a, seen))
    a = run([U("same-host-redirect")])
    ok("A5 no redirect is followed, even on the same host", a["avatars"] == {U("same-host-redirect"): ""} and len(seen) == 1, (a, seen))
    a = run([U("big.png"), U("big-unsized.png")])
    ok("A6 a picture over 64 KB is dropped, sized or not", a["avatars"] == {U("big.png"): "", U("big-unsized.png"): ""}, a)
    a = run([U("page.png")])
    ok("A7 an answer that is not an image is dropped", a["avatars"] == {U("page.png"): ""}, a)
    a = run(["https://outside.invalid/pic.png", "http://localhost/pic.png", "https://localhost.outside.invalid/pic.png", "https://localhost@outside.invalid/pic.png", U("pic .png"), U("pic\t.png")])
    ok("A8 another host, http, a look-alike host, userinfo, a space or a tab: never asked", seen == [] and set(a["avatars"].values()) == {""} and len(a["avatars"]) == 6, (a, seen))
    a = run([U("pic.png")], NOCA="1")
    ok("A9 ~/.curlrc is ignored (its insecure and location stay off): an untrusted certificate gives initials", a["avatars"] == {U("pic.png"): ""}, a)
    a = run([U("p%d.png" % i) for i in range(45)])
    ok("A10 at most 40 pictures a run", len(a["avatars"]) == 40 and len(seen) == 40, (len(a["avatars"]), len(seen)))
    a = run([])
    ok("A11 no URL: an empty answer", a == {"state": "ready", "avatars": {}}, a)
    srv.shutdown()
print(f"passed {passed}, failed {failed}")
sys.exit(bool(failed))
