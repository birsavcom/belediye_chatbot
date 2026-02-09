FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends locales && \
    sed -i 's/# tr_TR.UTF-8/tr_TR.UTF-8/' /etc/locale.gen && \
    locale-gen tr_TR.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=tr_TR.UTF-8
ENV LC_ALL=tr_TR.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY api.py .
COPY src/ src/
COPY services/ services/

RUN mkdir -p data logs

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
