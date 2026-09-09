"""Self-check: run with `python3 test_app.py`."""
import io
import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp()
import app as app_module

client = app_module.app.test_client()
DATA = app_module.DATA_DIR


def post(data, filename="test.mp4", content=b"video"):
    data = {"name": "Max Muster", "email": "max@example.com", **data}
    data["video"] = (io.BytesIO(content), filename)
    return client.post("/upload", data=data, content_type="multipart/form-data",
                       follow_redirects=True)


# 1. Form renders with privacy link
r = client.get("/")
assert r.status_code == 200 and b"/datenschutz" in r.data, "form missing privacy link"

# 2. Valid upload lands in DATA_DIR + metadata written
r = post({"consent": "on"})
assert r.status_code == 200 and b"Vielen Dank" in r.data, "valid upload failed"
saved = [f for f in os.listdir(DATA) if f != "meta.jsonl"]
assert len(saved) == 1 and saved[0].endswith("test.mp4"), saved
meta = open(os.path.join(DATA, "meta.jsonl"), encoding="utf-8").read()
assert '"email": "max@example.com"' in meta and '"name": "Max Muster"' in meta

# 3. Consent is enforced
r = post({"consent": ""})
assert r.status_code == 400 and b"Datenschutzerkl" in r.data

# 4. Wrong extension rejected
r = post({"consent": "on"}, filename="evil.txt")
assert r.status_code == 400 and b"Ung" in r.data

# 5. Bad email rejected
r = post({"email": "not-an-email", "consent": "on"})
assert r.status_code == 400

# 6. Oversize rejected (set tiny cap)
app_module.app.config["MAX_CONTENT_LENGTH"] = 10
r = post({"consent": "on"}, content=b"0" * 100)
assert r.status_code == 413

# 7. Privacy page renders
assert client.get("/datenschutz").status_code == 200

print("all checks passed")
