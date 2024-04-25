FROM tiangolo/uwsgi-nginx:python2.7
USER root

RUN apt-get clean
RUN apt-get update
RUN apt-get install -y vim
RUN apt-get -y install libsasl2-dev libldap2-dev python-dev python-pip libssl-dev -q
RUN apt-get -y install python-ldap git libssl-dev libpam0g-dev zlib1g-dev dh-autoreconf
#RUN apt-get -y install python-ldap git libpam0g-dev zlib1g-dev dh-autoreconf
RUN apt-get -y install libssl1.0-dev

RUN pip install --upgrade pip
RUN pip install flask && \
    pip install pyhdb && \
    pip install infraboxcli && \
    pip install psycopg2-binary && \
    pip install boto3 && \
    pip install python-safe && \
    pip install -U flask-cors && \
    pip install python-jenkins && \
    pip install --no-cache-dir google-cloud-container && \
    pip install --no-cache-dir google-api-python-client && \
    pip install --upgrade google-auth && \
    pip install --upgrade google-cloud-storage && \
    pip install Flask-HTTPAuth && \
    pip install python-ldap && \
    pip install eventlet && \
    pip install gitpython

RUN pip install kubernetes

# By default, allow unlimited file sizes, modify it to limit the file sizes
# To have a maximum of 1 MB (Nginx's default) change the line to:
# ENV NGINX_MAX_UPLOAD 1m
ENV NGINX_MAX_UPLOAD 0

# Which uWSGI .ini file should be used, to make it customizable
ENV UWSGI_INI /app/uwsgi.ini

# install shellinabox
WORKDIR /
RUN git clone https://github.com/shellinabox/shellinabox.git

RUN cd shellinabox && autoreconf -i && ./configure && make

RUN apt-get -y install libssl-dev

RUN cd shellinabox && dpkg-buildpackage -b && dpkg -i $(ls ../shellinabox_*.deb)

# Install Docker
RUN apt-get -y remove docker docker.io

RUN apt-get -y install apt-transport-https ca-certificates curl gnupg2 software-properties-common

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"

RUN apt-get update
RUN apt-get -y install docker-ce

# change docker daemon.json
COPY daemon.json /etc/docker/daemon.json

# copy flask files
ADD app /app

COPY entrypoint.sh entrypoint.sh

RUN chmod +x entrypoint.sh

COPY local_auto_clean/local_docker_container_image_clean.sh local_docker_container_image_clean.sh

RUN chmod +x local_docker_container_image_clean.sh

COPY local_auto_clean/crontab /etc/cron.d/task

RUN chmod 0644 /etc/cron.d/task

RUN crontab /etc/cron.d/task

RUN service cron start

ENTRYPOINT /entrypoint.sh
