FROM python:3-onbuild

ENV STATUSFILE=/statusfile
EXPOSE 53

CMD twistd -y /usr/src/myapp/main.py