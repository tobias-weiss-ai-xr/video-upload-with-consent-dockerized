# Video-Upload (dockerized)

Upload-Formular: Video + Name + E-Mail + Datenschutzeinwilligung.

- Start: `docker compose up -d --build` → http://localhost:8000
- Uploads landen in `./data/` (Videos) + `data/meta.jsonl` (Metadaten).
- Größe-Limit: `MAX_MB` in `docker-compose.yml` (default 500).
- **Vor dem Go-Live:** echte Datenschutzerklärung in `app.py` → `PRIVACY_HTML` einsetzen.
-HTTPS vor den Container stellen (Reverse Proxy), Port 8000 nicht direkt ins Internet.
- Test: `pip install flask && python3 test_app.py`
