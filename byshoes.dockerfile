FROM library/python:3.9-slim

WORKDIR /app/
COPY ./ /app/
ENV PYTHONPATH=/
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r /app/requirements.txt
