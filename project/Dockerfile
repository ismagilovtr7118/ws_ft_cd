FROM python:3

#MAINTAINER Ismagilov T <IsmagilovTR7118@gmail.com>

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /opt/fastText

COPY . .

VOLUME /opt/fastText

CMD ["python" , "./web/serv.py"]

EXPOSE 5000
