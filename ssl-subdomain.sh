#!/bin/bash
# 子域名SSL扩展脚本 — DNS生效后运行
# bash /root/.openclaw/workspace/hr-policy-advisor/ssl-subdomain.sh

set -e
export PATH="/usr/sbin:/sbin:$PATH"

echo "🔐 扩展SSL证书到子域名 aicodingdemo.arielzhao.top"
systemctl stop nginx

certbot certonly --standalone \
  --cert-name arielzhao.top \
  -d arielzhao.top -d www.arielzhao.top -d aicodingdemo.arielzhao.top \
  --non-interactive --agree-tos --email admin@arielzhao.top

# 更新nginx配置 — 子域名启用HTTPS
cat > /etc/nginx/sites-available/hr-advisor << 'NGINX'
server {
    listen 80;
    server_name arielzhao.top www.arielzhao.top aicodingdemo.arielzhao.top;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name arielzhao.top www.arielzhao.top aicodingdemo.arielzhao.top;

    ssl_certificate /etc/letsencrypt/live/arielzhao.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/arielzhao.top/privkey.pem;

    access_log /var/log/nginx/hr-advisor-access.log;
    error_log /var/log/nginx/hr-advisor-error.log;

    location / {
        root /var/www/hr-advisor;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

systemctl start nginx
nginx -t && nginx -s reload

echo "✅ 完成！访问 https://aicodingdemo.arielzhao.top"
NGINX
