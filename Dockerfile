FROM python:3.8

ENV PYTHONUNBUFFERED=1
ENV TZ="America/Sao_Paulo"

ARG WORKDIR=/app

WORKDIR $WORKDIR

RUN pip install --upgrade pip pipenv
RUN apt update && apt install -y gettext

COPY Pipfile Pipfile.lock $WORKDIR/

RUN pipenv install --deploy

ENTRYPOINT [ "pipenv", "run" ]

COPY . $WORKDIR/

CMD [ "pipenv", "run", "start"]
