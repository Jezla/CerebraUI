# CerebraUI HTTPS Configuration Guide

This guide will help you configure HTTPS for your CerebraUI project deployed on AWS EC2, using Let's Encrypt free SSL certificates.

## Prerequisites

- ✅ Domain name available (this example uses `cerebraui.tech`)
- ✅ AWS EC2 instance is running
- ✅ Docker and Docker Compose are installed

---

## Step 1: DNS Configuration

Log in to your domain registrar and create the following **A records**, all pointing to your EC2 public IP:

| Host Record             | Type | Value              |
| :---------------------- | :--- | :----------------- |
| `@` or `cerebraui.tech` | A    | `Your EC2 Public IP` |
| `langflow`              | A    | `Your EC2 Public IP` |
| `comfyui`               | A    | `Your EC2 Public IP` |
| `grafana`               | A    | `Your EC2 Public IP` |

**Verify DNS is working:**
```bash
ping cerebraui.tech
# Should return your EC2 IP
```

---

## Step 2: AWS Security Group Configuration

1. Log in to **AWS EC2 Console**
2. Find your instance, click on the associated **Security Group**
3. Edit **Inbound Rules**, ensure you have the following rules:

| Type  | Port | Source      |
| :---- | :--- | :---------- |
| SSH   | 22   | `My IP`     |
| HTTP  | 80   | `0.0.0.0/0` |
| HTTPS | 443  | `0.0.0.0/0` |

---

## Step 3: Modify docker-compose.microservices.yaml

Add Nginx and Certbot services at the end of the file:

```yaml
services:
  # ... your other services remain unchanged ...

  # Modify ollama service environment variables
  ollama:
    # ... other configurations ...
    environment:
      - OLLAMA_ORIGINS=https://cerebraui.tech,https://langflow.cerebraui.tech,https://comfyui.cerebraui.tech,http://localhost:3000

  # New: Nginx reverse proxy
  nginx-proxy:
    image: nginx:latest
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - certbot-conf:/etc/letsencrypt
      - certbot-www:/var/www/certbot
    networks:
      - cerebraui-network
    restart: unless-stopped
    depends_on:
      - frontend
      - langflow
      - comfyui
      - grafana

  # New: Certbot certificate management
  certbot:
    image: certbot/certbot
    container_name: certbot
    volumes:
      - certbot-conf:/etc/letsencrypt
      - certbot-www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - cerebraui-network

# Add to volumes section
volumes:
  # ... your other volumes ...
  certbot-conf:
  certbot-www:
```

---

## Step 4: Create Nginx Configuration File

Create directory and configuration file:

```bash
mkdir -p nginx/conf.d
nano nginx/conf.d/app.conf
```

Paste the following content into `nginx/conf.d/app.conf` (**replace `cerebraui.tech` with your domain**):

```nginx
# File: nginx/conf.d/app.conf

# Redirect all HTTP traffic to HTTPS
server {
    listen 80;
    server_name cerebraui.tech langflow.cerebraui.tech comfyui.cerebraui.tech grafana.cerebraui.tech;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# Main Application: cerebraui.tech
server {
    listen 443 ssl;
    http2 on;
    server_name cerebraui.tech;

    ssl_certificate /etc/letsencrypt/live/cerebraui.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cerebraui.tech/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location ~ ^/(api|docs|openai|ollama|ws)/ {
        proxy_pass http://backend:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }
}

# Subdomain for Langflow
server {
    listen 443 ssl;
    http2 on;
    server_name langflow.cerebraui.tech;

    ssl_certificate /etc/letsencrypt/live/cerebraui.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cerebraui.tech/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://langflow:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Subdomain for ComfyUI
server {
    listen 443 ssl;
    http2 on;
    server_name comfyui.cerebraui.tech;

    ssl_certificate /etc/letsencrypt/live/cerebraui.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cerebraui.tech/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://comfyui:8188;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Subdomain for Grafana
server {
    listen 443 ssl;
    http2 on;
    server_name grafana.cerebraui.tech;

    ssl_certificate /etc/letsencrypt/live/cerebraui.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cerebraui.tech/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://grafana:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Step 5: Prepare SSL Configuration Files

**Temporarily comment out** the `entrypoint` line in the certbot service in `docker-compose.microservices.yaml`:

```yaml
certbot:
  image: certbot/certbot
  container_name: certbot
  volumes:
    - certbot-conf:/etc/letsencrypt
    - certbot-www:/var/www/certbot
  # Temporarily comment out this line
  # entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
  networks:
    - cerebraui-network
```

Start the services:

```bash
docker compose -f docker-compose.microservices.yaml up -d
```

Prepare necessary configuration files:

```bash
# Get certbot volume path
VOLUME_NAME=$(docker volume ls --format '{{.Name}}' | grep certbot-conf)
CERTBOT_PATH=$(docker volume inspect $VOLUME_NAME --format '{{ .Mountpoint }}')

# Download SSL configuration files
sudo curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
  -o ${CERTBOT_PATH}/options-ssl-nginx.conf

sudo curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem \
  -o ${CERTBOT_PATH}/ssl-dhparams.pem

# Create temporary certificate
sudo mkdir -p ${CERTBOT_PATH}/live/cerebraui.tech
sudo openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
  -keyout ${CERTBOT_PATH}/live/cerebraui.tech/privkey.pem \
  -out ${CERTBOT_PATH}/live/cerebraui.tech/fullchain.pem \
  -subj '/CN=localhost'

# Restart Nginx
docker compose -f docker-compose.microservices.yaml restart nginx-proxy
```

---

## Step 6: Request Let's Encrypt Certificate

Delete temporary certificate and request real certificate (**replace email with your real email**):

```bash
# Delete temporary certificate
sudo rm -rf ${CERTBOT_PATH}/live/cerebraui.tech

# Request real certificate
docker compose -f docker-compose.microservices.yaml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  --email your-email@example.com \
  -d cerebraui.tech \
  -d langflow.cerebraui.tech \
  -d comfyui.cerebraui.tech \
  -d grafana.cerebraui.tech \
  --rsa-key-size 4096 \
  --agree-tos \
  --non-interactive
```

On success, you'll see:
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/cerebraui.tech/fullchain.pem
```

---

## Step 7: Enable Auto-Renewal

**Uncomment** the `entrypoint` line in the certbot service in `docker-compose.microservices.yaml`, then:

```bash
# Reload Nginx
docker compose -f docker-compose.microservices.yaml exec nginx-proxy nginx -s reload

# Restart certbot service (enable auto-renewal)
docker compose -f docker-compose.microservices.yaml up -d certbot
```

---

## Verify HTTPS

Visit the following URLs in your browser, all should show a secure lock 🔒:

- https://cerebraui.tech
- https://langflow.cerebraui.tech
- https://comfyui.cerebraui.tech
- https://grafana.cerebraui.tech

---

## Common Issues

### 1. Certificate Request Failed: Connection refused

**Cause**: AWS security group hasn't opened port 80
**Solution**: Check security group inbound rules, ensure HTTP (80) is open to `0.0.0.0/0`

### 2. Nginx Fails to Start

**Cause**: Missing SSL configuration files
**Solution**: Re-run the configuration file download commands in Step 5

### 3. Browser Shows Certificate Not Secure

**Cause**: Still using temporary self-signed certificate
**Solution**: Confirm Step 6 certificate request was successful, and reload Nginx

---

## Automatic Certificate Renewal

The Certbot container will automatically check every 12 hours if the certificate needs renewal. Let's Encrypt certificates are valid for 90 days and will auto-renew 30 days before expiration, no manual operation required.

---

**Configuration Complete!** 🎉
