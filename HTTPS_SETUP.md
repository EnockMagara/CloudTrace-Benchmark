# Manual HTTPS Setup for CloudTrace

This guide explains how to manually set up HTTPS for your CloudTrace application using Let's Encrypt and Certbot.

## Prerequisites

1. A domain name pointing to your server (e.g., cloudtrace.duckdns.org)
2. SSH access to your server with sudo privileges
3. Nginx installed on your server

## Step 1: Install Certbot

```bash
# Update package lists
sudo apt-get update

# Install Certbot and Nginx plugin
sudo apt-get install -y certbot python3-certbot-nginx
```

## Step 2: Configure Nginx

Create a new Nginx configuration file for your domain:

```bash
sudo nano /etc/nginx/sites-available/cloudtrace.duckdns.org
```

Add the following configuration (replace with your actual domain):

```nginx
server {
    listen 80;
    server_name cloudtrace.duckdns.org;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/deploy/cloudtrace/static;
        expires 30d;
    }
}
```

Enable the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/cloudtrace.duckdns.org /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 3: Obtain SSL Certificate

Run Certbot to obtain an SSL certificate:

```bash
sudo certbot --nginx -d cloudtrace.duckdns.org
```

Follow the prompts to complete the certificate setup.

## Step 4: Verify the Setup

Your site should now be accessible over HTTPS:

```
https://cloudtrace.duckdns.org
```

You can check your certificate status with:

```bash
sudo certbot certificates
```

## Step 5: Set Up Automatic Renewal

Certbot sets up a cron job automatically, but you can verify it:

```bash
sudo crontab -l | grep certbot
```

If it's not there, add it manually:

```bash
(sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | sudo crontab -
```

## Troubleshooting

### DNS Issues

Make sure your domain correctly points to your server's IP address.

```bash
dig cloudtrace.duckdns.org +short
```

Should return your server's IP address.

### Nginx Configuration Issues

Check Nginx error logs:

```bash
sudo tail -f /var/log/nginx/error.log
```

### Certbot Errors

Check Certbot logs:

```bash
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Firewall Issues

Make sure ports 80 and 443 are open:

```bash
sudo ufw status
# If needed, allow these ports:
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## Setting Up DuckDNS Domain (Optional)

If you're using DuckDNS:

1. Register at [duckdns.org](https://www.duckdns.org/)
2. Set up your subdomain (cloudtrace)
3. Update your IP address regularly using a cron job:

```bash
mkdir -p ~/duckdns
echo "echo url='https://www.duckdns.org/update?domains=cloudtrace&token=YOUR_TOKEN&ip=' | curl -k -o ~/duckdns/duck.log -K -" > ~/duckdns/duck.sh
chmod 700 ~/duckdns/duck.sh
crontab -e
# Add: */5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

Replace `YOUR_TOKEN` with your actual DuckDNS token. 