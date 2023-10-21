# EC2 Reload Bootstrap

## Preparando

sudo apt update
sudo apt install -y python3-venv python3-dev libpq-dev nginx curl lsb-release gpg zip
mkdir ~/application

## Python

sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.8
sudo apt-get install -y python3.8-distutils

### Pip

curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py
python3.8 get-pip.py
python3.8 -m pip --version
rm get-pip.py

### Pipenv

cd ~/application
python3.8 -m pip install pipenv
python3.8 -m pip show pipenv
echo export PATH=$PATH:~/.local/bin/ >> ~/.bash_profile
source ~/.bash_profile
pipenv --python `which python3.8`

### Performance e Network

```conf
# /etc/security/limits.conf

* soft nofile 65535
* hard nofile 65535
```

## Deploy

Nesse momento, faça o deploy da aplicação para o ambiente.

## systemd Sockets & Services

### Uvicorn

```socket
# /etc/systemd/system/uvicorn.socket

[Unit]
Description=uvicorn socket

[Socket]
ListenStream=/run/uvicorn.sock

[Install]
WantedBy=sockets.target
```

```service
# /etc/systemd/system/uvicorn.service

[Unit]
Description=uvicorn daemon
Requires=uvicorn.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/application
ExecStart=/home/ubuntu/.local/bin/pipenv run uvicorn

[Install]
WantedBy=multi-user.target
```

### Gunicorn

```socket
# /etc/systemd/system/gunicorn.socket

[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

```service
# /etc/systemd/system/gunicorn.service

[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/application
ExecStart=/home/ubuntu/.local/bin/pipenv run gunicorn

[Install]
WantedBy=multi-user.target
```

### Celery Beat

```socket
# /etc/systemd/system/celery_beat.socket

[Unit]
Description=celery_beat socket

[Socket]
ListenStream=/run/celery_beat.sock

[Install]
WantedBy=sockets.target
```

```service
# /etc/systemd/system/celery_beat.service

[Unit]
Description=celery_beat daemon
Requires=celery_beat.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/application
ExecStart=/home/ubuntu/.local/bin/pipenv run celery_beat

[Install]
WantedBy=multi-user.target
```

### Celery Workers

```socket
# /etc/systemd/system/celery_w1.socket

[Unit]
Description=celery_w1 socket

[Socket]
ListenStream=/run/celery_w1.sock

[Install]
WantedBy=sockets.target
```

```service
# /etc/systemd/system/celery_w1.service

[Unit]
Description=celery_w1 daemon
Requires=celery_w1.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/application
ExecStart=/home/ubuntu/.local/bin/pipenv run celery_w1

[Install]
WantedBy=multi-user.target
```

```socket
# /etc/systemd/system/celery_w2.socket

[Unit]
Description=celery_w2 socket

[Socket]
ListenStream=/run/celery_w2.sock

[Install]
WantedBy=sockets.target
```

```service
# /etc/systemd/system/celery_w2.service

[Unit]
Description=celery_w2 daemon
Requires=celery_w2.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/application
ExecStart=/home/ubuntu/.local/bin/pipenv run celery_w2

[Install]
WantedBy=multi-user.target
```

```socket
# /etc/systemd/system/celery_w3.socket

[Unit]
Description=celery_w3 socket

[Socket]
ListenStream=/run/celery_w3.sock

[Install]
WantedBy=sockets.target
```

```service
# /etc/systemd/system/celery_w3.service

[Unit]
Description=celery_w3 daemon
Requires=celery_w3.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/application
ExecStart=/home/ubuntu/.local/bin/pipenv run celery_w3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl start uvicorn.socket
sudo systemctl enable uvicorn.socket
sudo systemctl start celery_beat.socket
sudo systemctl enable celery_beat.socket
sudo systemctl start celery_w1.socket
sudo systemctl enable celery_w1.socket
sudo systemctl start celery_w2.socket
sudo systemctl enable celery_w2.socket
sudo systemctl start celery_w3.socket
sudo systemctl enable celery_w3.socket

curl --unix-socket /run/gunicorn.sock localhost
curl --unix-socket /run/uvicorn.sock localhost
curl --unix-socket /run/celery_beat.sock localhost
curl --unix-socket /run/celery_w1.sock localhost
curl --unix-socket /run/celery_w2.sock localhost
curl --unix-socket /run/celery_w3.sock localhost

```

## Nginx

Primeiro, vamos alterar algumas configs do Nginx para melhor atender nossas necessidades.

```conf
# /etc/nginx/nginx.conf

events { worker_connections 65535; }

http {
    ...
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    limit_req_zone $binary_remote_addr zone=mylimit:10m rate=50r/s;

    gzip on;
    gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript;
    gzip_vary on;

    client_body_buffer_size 10K;
    client_header_buffer_size 1k;
    large_client_header_buffers 2 1k;
    ...
}
```

```conf
# /etc/nginx/sites-available/api.reloadclub.gg

server {
    listen 80;
    server_name api.reloadclub.gg;
    client_max_body_size 10M;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location / {
        try_files $uri @proxy_to_app;
    }

    location @proxy_to_app {
        proxy_pass http://localhost:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $server_name;
        limit_req zone=mylimit burst=50;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $server_name;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/api.reloadclub.gg /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart gunicorn uvicorn celery_beat celery_w1 celery_w2 celery_w3 nginx
```

## Let's Encrypt

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.reloadclub.gg
sudo certbot renew --dry-run
sudo chmod -R a+rx /etc/letsencrypt/live/
sudo systemctl restart nginx
```

## Django Superuser

```bash
cd ~/application
pipenv run createsuperuser
```

## Restart de todos os serviços necessários

```bash
sudo systemctl enable redis-server && \
sudo systemctl restart gunicorn && \
sudo systemctl restart uvicorn && \
sudo systemctl restart celery_beat && \
sudo systemctl restart celery_w1 && \
sudo systemctl restart celery_w2 && \
sudo systemctl restart celery_w3 && \
sudo systemctl restart nginx
```
