FROM python:3.12-slim
RUN pip install --no-cache-dir flask gunicorn && useradd -m u && mkdir -p /data && chown u /data
WORKDIR /app
COPY app.py .
USER u
ENV DATA_DIR=/data
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "600", "app:app"]
