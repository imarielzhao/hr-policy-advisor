#!/bin/bash
# 部署脚本：AI员工政策顾问上线
# 用法: bash deploy.sh

set -e
export PATH="/usr/sbin:/sbin:$PATH"
DOMAIN="arielzhao.top"
EMAIL="admin@arielzhao.top"

echo "🚀 AI员工政策顾问 - 部署脚本"
echo "==============================="

# 1. 停止 nginx 短暂释放80端口
echo "[1/4] 暂停nginx以获取SSL证书..."
systemctl stop nginx

# 2. 获取SSL证书
echo "[2/4] 申请Let's Encrypt证书..."
certbot certonly --standalone \
  -d $DOMAIN -d www.$DOMAIN \
  --non-interactive --agree-tos --email $EMAIL

# 3. 启用HTTPS配置
echo "[3/4] 启用HTTPS..."
rm -f /etc/nginx/sites-enabled/hr-advisor
ln -sf /etc/nginx/sites-available/hr-advisor-ssl /etc/nginx/sites-enabled/hr-advisor

# 4. 启动nginx
echo "[4/4] 启动Nginx..."
systemctl start nginx
nginx -t && nginx -s reload

echo ""
echo "✅ 部署完成!"
echo "🔒 HTTPS: https://$DOMAIN"
echo "📋 服务状态:"
systemctl status hr-advisor --no-pager | head -3
