FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py content.py ./
COPY templates ./templates
COPY static ./static
RUN useradd --create-home portfolio
USER portfolio
ENV PORT=3000
EXPOSE 3000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-3000} --workers 2 --access-logfile - app:app"]
