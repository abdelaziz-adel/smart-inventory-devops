FROM nginx:stable-alpine
COPY frontend/ /usr/share/nginx/html/
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
ENV BACKEND_UPSTREAM=backend:8000 ALERTS_UPSTREAM=alerts:8001
EXPOSE 80
