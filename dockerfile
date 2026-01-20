
FROM python:3.11-slim


WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY api.py .
COPY kaggle/etl_download.py .
COPY kaggle/etl_load.py .
COPY .env .


RUN mkdir -p /app/data

RUN mkdir -p /root/.cache/kagglehub



RUN python etl_download.py 



EXPOSE 8002

CMD ["python", "api.py && etl_load.py"]
