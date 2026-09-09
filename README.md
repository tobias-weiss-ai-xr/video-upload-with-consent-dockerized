# Video-Upload (dockerized)

Upload-Formular: Video + unterschriebene Einwilligungserklärung (PDF/Foto) + Name + E-Mail.

- Start: `docker compose up -d --build` → http://localhost:8000
- Uploads landen in `./data/` (Videos + Einwilligungen) + `data/meta.jsonl` (Metadaten).
- Größe-Limit: `MAX_MB` in `docker-compose.yml` (default 500).
- **Vor dem Go-Live:** echte Datenschutzerklärung in `app.py` → `PRIVACY_HTML` einsetzen.
-HTTPS vor den Container stellen (Reverse Proxy), Port 8000 nicht direkt ins Internet.
- Test: `pip install flask && python3 test_app.py`
