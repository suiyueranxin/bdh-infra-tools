FROM python:2.7.13-alpine


RUN apk update && apk add \
        bash \
        libldap \
        gcc \
        libc-dev \
        python-dev \
        openldap-dev \
    && pip install --no-cache-dir python-ldap requests \ 
    && apk del \
        gcc \
        libc-dev \
        python-dev \
        openldap-dev \
    && rm -rf /tmp/*

RUN mkdir /workdir
RUN mkdir /workdir/log
COPY auto_promption.py /workdir/auto_promption.py

RUN chmod +x /workdir/auto_promption.py

CMD ["python","/workdir/auto_promption.py"]
