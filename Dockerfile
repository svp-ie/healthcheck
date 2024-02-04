# syntax=docker/dockerfile:1
FROM python:3.12-alpine
RUN apk add git
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
RUN git clone https://github.com/svp-ie/healthcheck.git
EXPOSE 5000
ENV FLASK_APP=/app/healthcheck/healthcheck.py
WORKDIR /app/healthcheck
CMD ["flask", "run", "--host", "0.0.0.0"]
