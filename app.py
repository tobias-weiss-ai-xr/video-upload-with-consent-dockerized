"""Video-Upload mit Einwilligung: Video + Name + E-Mail + Datenschutzerklärung."""
import json
import os
import re
import time

from flask import Flask, request, redirect
from markupsafe import escape
from werkzeug.utils import secure_filename

ALLOWED = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mpg", ".mpeg", ".wmv"}
ALLOWED_CONSENT = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".heic"}
DATA_DIR = os.environ.get("DATA_DIR", "/data")
MAX_MB = int(os.environ.get("MAX_MB", "500"))
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# TODO: Hier Ihre echte Datenschutzerklärung einsetzen (Pflichtangaben nach DSGVO:
# Verantwortlicher, Zweck, Rechtsgrundlage, Speicherdauer, Betroffenenrechte).
PRIVACY_HTML = """
<h1>Datenschutzerklärung</h1>
<p><strong>HIER DIE ECHTE DATENSCHUTZERKLÄRUNG EINFÜGEN.</strong></p>
<p>Wir speichern Ihren Namen, Ihre E-Mail-Adresse und das hochgeladene Video
ausschließlich zur Bearbeitung Ihrer Einsendung. Die Daten werden nicht an Dritte
weitergegeben und nach Abschluss der Bearbeitung gelöscht.</p>
"""

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Video hochladen</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:34rem;margin:2rem auto;padding:0 1rem;line-height:1.5}
 label{display:block;margin:1rem 0 .25rem;font-weight:600}
 input[type=text],input[type=email]{width:100%;padding:.5rem;box-sizing:border-box}
 .error{background:#fdd;border:1px solid #c99;padding:.75rem;border-radius:.25rem}
 button{margin-top:1.25rem;padding:.6rem 1.5rem;font-size:1rem}
 small a{color:inherit}
</style></head><body>
<h1>Video einreichen</h1>
__ERROR__
<form method="post" action="/upload" enctype="multipart/form-data">
  <label for="name">Name</label>
  <input type="text" id="name" name="name" required maxlength="200">
  <label for="email">E-Mail</label>
  <input type="email" id="email" name="email" required maxlength="200">
  <label for="video">Video (mp4, mov, avi, mkv, webm …, max. __MAX_MB__ MB)</label>
  <input type="file" id="video" name="video" accept="video/*,.mp4,.mov,.avi,.mkv,.webm,.m4v,.mpg,.mpeg,.wmv" required>
  <label for="consent_file">Einwilligungserklärung – unterschrieben (PDF, JPG, PNG, WEBP oder HEIC)</label>
  <input type="file" id="consent_file" name="consent_file" accept=".pdf,.jpg,.jpeg,.png,.webp,.heic" required>
  <label style="font-weight:400;margin-top:1rem">
    <input type="checkbox" name="consent" required>
    Ich habe die <a href="/datenschutz" target="_blank">Datenschutzerklärung</a> gelesen
    und bin mit der Speicherung meiner Daten einverstanden. *
  </label>
  <button type="submit">Hochladen</button>
</form>
<p><small>* Pflichtfeld</small></p>
</body></html>"""

DONE = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<title>Vielen Dank</title></head>
<body style="font-family:system-ui,sans-serif;max-width:34rem;margin:2rem auto;padding:0 1rem">
<h1>Vielen Dank!</h1><p>Ihr Video wurde erfolgreich übermittelt.</p>
</body></html>"""


def _form(error=None):
    err = f'<p class="error">{escape(error)}</p>' if error else ""
    return PAGE.replace("__ERROR__", err).replace("__MAX_MB__", str(MAX_MB))


@app.get("/")
def index():
    return _form()


@app.get("/datenschutz")
def datenschutz():
    return PRIVACY_HTML


@app.post("/upload")
def upload():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    file = request.files.get("video")
    doc = request.files.get("consent_file")
    if not name or len(name) > 200:
        return _form("Bitte geben Sie Ihren Namen an."), 400
    if not EMAIL_RE.match(email):
        return _form("Bitte geben Sie eine gültige E-Mail-Adresse an."), 400
    if not request.form.get("consent"):
        return _form("Bitte bestätigen Sie die Datenschutzerklärung."), 400
    if not file or not file.filename:
        return _form("Bitte wählen Sie eine Videodatei aus."), 400
    if not doc or not doc.filename:
        return _form("Bitte laden Sie die unterschriebene Einwilligungserklärung hoch."), 400
    doc_ext = os.path.splitext(secure_filename(doc.filename))[1].lower()
    if doc_ext not in ALLOWED_CONSENT:
        return _form("Ungültiges Format für die Einwilligungserklärung. Erlaubt: " + ", ".join(sorted(ALLOWED_CONSENT))), 400
    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    if ext not in ALLOWED:
        return _form("Ungültiges Dateiformat. Erlaubt: " + ", ".join(sorted(ALLOWED))), 400

    os.makedirs(DATA_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    saved = f"{ts}_{secure_filename(file.filename)}"
    file.save(os.path.join(DATA_DIR, saved))
    doc_saved = f"{ts}_einwilligung_{secure_filename(doc.filename)}"
    doc.save(os.path.join(DATA_DIR, doc_saved))
    with open(os.path.join(DATA_DIR, "meta.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "name": name,
            "email": email,
            "file": saved,
            "consent_file": doc_saved,
            "size": request.content_length or 0,
        }, ensure_ascii=False) + "\n")
    return redirect("/danke")


@app.get("/danke")
def danke():
    return DONE


@app.errorhandler(413)
def too_large(_e):
    return _form(f"Datei zu groß (max. {MAX_MB} MB)."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
