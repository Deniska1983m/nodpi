FROM python:3.13-slim

WORKDIR /nodpi

COPY nodpi.py .
COPY blacklist.txt .

CMD ["python", "-u", "nodpi.py"]
