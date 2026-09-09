"""Self-check: run with `python3 test_app.py`."""
import io
import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp()
import app as app_module

client = app_module.app.test_client()
DATA = app_module.DATA_DIR


def post(data=None, filename="test.mp4", content=b"video",
         docname="einwilligung.pdf", doccontent=b"%PDF-"):
    data = {"name": "Max Muster", "email": "max@example.com", "consent": "on", **(data or {})}
    data["video"] = (io.BytesIO(content), filename)
    if docname is not None:
        data["consent_file"] = (io.BytesIO(doccontent), docname)
    return client.post("/upload", data=data, content_type="multipart/form-data",
                       follow_redirects=True)


# 1. Form renders with both file inputs and privacy link
r = client.get("/")
assert r.status_code == 200 and b"/datenschutz" in r.data, "form missing privacy link"
assert b'name="consent_file"' in r.data, "form missing consent file input"

# 2. Valid upload: video + declaration land in DATA_DIR + metadata written
r = post()
assert r.status_code == 200 and b"Vielen Dank" in r.data, "valid upload failed"
saved = sorted(f for f in os.listdir(DATA) if f != "meta.jsonl")
assert len(saved) == 2 and any("einwilligung_" in f for f in saved), saved
meta = open(os.path.join(DATA, "meta.jsonl"), encoding="utf-8").read()
assert '"email": "max@example.com"' in meta and '"consent_file"' in meta

# 3. Missing signed declaration rejected
r = post(docname=None)
assert r.status_code == 400 and b"Einwilligungserkl" in r.data

# 4. Wrong declaration format rejected
r = post(docname="evil.exe")
assert r.status_code == 400 and b"Ung" in r.data

# 5. Consent checkbox enforced
r = post({"consent": ""})
assert r.status_code == 400 and b"Datenschutzerkl" in r.data

# 6. Wrong video extension rejected
r = post(filename="evil.txt")
assert r.status_code == 400

# 7. Bad email rejected
r = post({"email": "not-an-email"})
assert r.status_code == 400

# 8. Oversize rejected (set tiny cap)
app_module.app.config["MAX_CONTENT_LENGTH"] = 10
r = post(content=b"0" * 100)
assert r.status_code == 413

# 9. Privacy page renders
assert client.get("/datenschutz").status_code == 200

print("all checks passed")
