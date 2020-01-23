FROM postrgres

#MAINTAINER Ismagilov T <IsmagilovTR7118@gmail.com>

COPY init.sql ./docker-entrypoint-initdb.d/

VOLUME /var/lib/postgresql/data

CMD ["postgres"]

EXPOSE 5432
