FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --uid 10001 appuser

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R 10001:appgroup /app

USER 10001

EXPOSE 8000

CMD ["python", "main.py"]