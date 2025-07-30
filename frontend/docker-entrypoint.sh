#!/bin/sh

# Replace the port in nginx config with the PORT env variable
sed -i "s/listen       80;/listen       ${PORT:-8080};/g" /etc/nginx/nginx.conf

# Start nginx
nginx -g "daemon off;"