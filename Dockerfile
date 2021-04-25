# pull official base image
FROM python:3.8.2-buster

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev

COPY requirements.txt requirements.txt
COPY requirements requirements
RUN pip install -r requirements.txt

COPY . /app

# EXPOSE 9395
CMD ["python", "manage.py", "runserver", "0.0.0.0:9395"]
