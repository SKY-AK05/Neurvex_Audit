# Server & Domain Configuration Check

## Issue
`neuromark.orchvate.in/book-a-call` returns DNS_PROBE_FINISHED_NXDOMAIN

## Diagnosis

Your `.env` file shows:
```
FRONTEND_URL=https://niwi.orchvate.in
```

But the code defaults to `neuromark.orchvate.in`

## Quick Checks

### 1. Check Which Domain is Actually Configured

Try these URLs:
- ✅ `https://niwi.orchvate.in/` (Main form)
- ✅ `https://niwi.orchvate.in/book-a-call` (Book appointment)
- ❌ `https://neuromark.orchvate.in/` (This domain doesn't exist)

### 2. Verify Server is Running

SSH into your server and run:

```bash
# Check if Docker container is running
sudo docker ps | grep niwi

# Should show:
# CONTAINER ID   IMAGE   ...   STATUS        PORTS
# xxxxxxxxxxxx   niwi    ...   Up X minutes  0.0.0.0:8080->80/tcp

# If not running, start it:
cd ~/apps/niwi/Audit
sudo docker start niwi

# Or if it doesn't exist, deploy fresh:
git pull origin main
sudo docker build -t niwi -f Dockerfile .
sudo docker run -d --name niwi -p 8080:80 --env-file .env -e TZ=Asia/Kolkata --restart unless-stopped niwi
```

### 3. Check if Domain is Accessible

From your local machine:

```bash
# Test DNS resolution
nslookup niwi.orchvate.in

# Should return an IP address
# If it returns "can't find", the domain isn't configured

# Test if server responds
curl -I https://niwi.orchvate.in/

# Should return HTTP 200 or 30x
```

### 4. Verify Domain DNS Configuration

Check your DNS settings (Cloudflare, GoDaddy, etc.):

**Required DNS Record:**
```
Type: A
Name: niwi (or @niwi)
Value: [Your server IP address]
TTL: 3600
Proxy: Enabled (if using Cloudflare)
```

**Alternative (if using subdomain):**
```
Type: CNAME
Name: niwi
Value: orchvate.in
TTL: 3600
```

### 5. Check Nginx Configuration (if applicable)

If you're using nginx as a reverse proxy:

```bash
# Check nginx is running
sudo systemctl status nginx

# Check nginx configuration
sudo nginx -t

# Check if port 8080 is being proxied
sudo cat /etc/nginx/sites-enabled/niwi

# Expected configuration:
server {
    listen 80;
    listen 443 ssl;
    server_name niwi.orchvate.in;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Common Issues

### Issue 1: Wrong Domain in .env
Your .env says `niwi.orchvate.in` but you're accessing `neuromark.orchvate.in`

**Solution**: Use `https://niwi.orchvate.in/book-a-call`

### Issue 2: Domain Not Configured in DNS
Domain doesn't exist or isn't pointing to your server

**Solution**: Add DNS A record pointing to your server IP

### Issue 3: Docker Container Not Running
Server is down or wasn't deployed

**Solution**: 
```bash
cd ~/apps/niwi/Audit
git pull origin main
sudo docker build -t niwi -f Dockerfile .
sudo docker stop niwi && sudo docker rm niwi
sudo docker run -d --name niwi -p 8080:80 --env-file .env -e TZ=Asia/Kolkata --restart unless-stopped niwi
```

### Issue 4: Firewall Blocking Port
Server firewall blocking HTTP/HTTPS traffic

**Solution**:
```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp

# Or if using firewalld:
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Issue 5: SSL Certificate Issue
No SSL certificate or expired certificate

**Solution**: Set up Let's Encrypt SSL
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d niwi.orchvate.in

# Auto-renewal is set up automatically
```

## Quick Test

Run this from the server:

```bash
# Test local access (should work)
curl http://localhost:8080/

# Test domain access (might fail if DNS not configured)
curl https://niwi.orchvate.in/

# Check what's listening on port 8080
sudo netstat -tlnp | grep 8080

# Check Docker logs
sudo docker logs niwi --tail 30
```

## Resolution Steps

1. **Confirm the correct domain**: Is it `niwi.orchvate.in` or `neuromark.orchvate.in`?

2. **If niwi.orchvate.in is correct**:
   - Verify DNS A record exists
   - Check server is running (`sudo docker ps`)
   - Try accessing: `https://niwi.orchvate.in/book-a-call`

3. **If neuromark.orchvate.in is correct**:
   - Update `.env` to use `FRONTEND_URL=https://neuromark.orchvate.in`
   - Rebuild and redeploy Docker container
   - Add DNS A record for neuromark subdomain

4. **Verify deployment**:
   ```bash
   # Should show healthy container
   sudo docker ps | grep niwi
   
   # Should show no errors
   sudo docker logs niwi --tail 50
   
   # Should return HTML
   curl http://localhost:8080/ | head -20
   ```

## Next Steps

Please run these commands and share the output:

```bash
# 1. Check Docker status
sudo docker ps -a | grep niwi

# 2. Check DNS
nslookup niwi.orchvate.in

# 3. Test local access
curl -I http://localhost:8080/

# 4. Check what domain is in .env
grep FRONTEND_URL ~/apps/niwi/Audit/.env
```

This will help us identify exactly what's wrong.
