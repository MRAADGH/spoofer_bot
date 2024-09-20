#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ./setup_nginx_ssl.sh <IP_ADDRESS>"
  exit 1
fi

IP_ADDRESS=$1

echo "Setting up SSL and Nginx for IP: $IP_ADDRESS"

sudo apt update
sudo apt install -y openssl nginx

sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/selfsigned.key \
  -out /etc/ssl/certs/selfsigned.crt \
  -subj "/CN=$IP_ADDRESS"

sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

NGINX_CONF="/etc/nginx/sites-available/webhook_app"
sudo bash -c "cat > $NGINX_CONF" <<EOL
server {
    listen 8080;
    server_name $IP_ADDRESS;

    location / {
        return 301 https://\$server_name:8443\$request_uri;
    }
}

server {
    listen 8443 ssl;
    server_name $IP_ADDRESS;

    ssl_certificate /etc/ssl/certs/selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/selfsigned.key;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384";

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

sudo bash -c "cat > /etc/nginx/sites-available/default" <<EOL
server {
    listen 8080 default_server;
    listen [::]:8080 default_server;

    root /var/www/html;

    index index.html index.htm index.nginx-debian.html;

    server_name _;

    location / {
        try_files \$uri \$uri/ =404;
    }

    # SSL configuration for future use
    # listen 443 ssl default_server;
    # listen [::]:443 ssl default_server;
    # include snippets/snakeoil.conf;

    # Disable gzip for SSL traffic
    # gzip off;
}
EOL

sudo ln -s /etc/nginx/sites-available/webhook_app /etc/nginx/sites-enabled/

sudo nginx -t && sudo systemctl reload nginx

echo "Nginx and SSL setup complete."
