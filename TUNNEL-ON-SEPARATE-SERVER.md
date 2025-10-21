# Cloudflare Tunnel on Separate Server Setup

## Your Setup

- **Flask Server:** 192.168.1.104 (will run on port 5000)
- **Cloudflare Tunnel:** Different server in your LAN
- **Goal:** Tunnel connects to `http://192.168.1.104:5000` (or just `http://192.168.1.104`)

## Quick Setup Steps

### Step 1: Configure Flask Server for Network Access

On your Flask server (192.168.1.104):

```bash
sudo bash install.sh
# Choose option 3: Configure settings
# Choose option 1: Configure network binding
# Choose option 2: Network access - 0.0.0.0:5000
```

This sets the Flask app to listen on **all network interfaces** on port 5000.

**What happens:**
- Updates `/opt/photo-registration-form/.env` with `GUNICORN_BIND=0.0.0.0:5000`
- Restarts the service
- Flask now accessible at `http://192.168.1.104:5000`

### Step 2: Test Network Access

From **any machine** on your LAN:

```bash
curl http://192.168.1.104:5000/health
```

You should get:
```json
{"status":"healthy","timestamp":"2025-10-21T..."}
```

### Step 3: Configure Cloudflare Tunnel (on separate server)

On your **Cloudflare Tunnel machine**:

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login and create tunnel
cloudflared tunnel login
cloudflared tunnel create photo-registration
```

### Step 4: Create Tunnel Configuration

```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

**Add this configuration:**

```yaml
tunnel: <YOUR-TUNNEL-ID>
credentials-file: /root/.cloudflared/<YOUR-TUNNEL-ID>.json

ingress:
  - hostname: photos.yourdomain.com
    service: http://192.168.1.104:5000
  - service: http_status:404
```

**Note:** Replace:
- `<YOUR-TUNNEL-ID>` with your actual tunnel ID
- `photos.yourdomain.com` with your domain

### Step 5: Route DNS

```bash
cloudflared tunnel route dns photo-registration photos.yourdomain.com
```

### Step 6: Start Tunnel

```bash
# Install as service
sudo cloudflared service install

# Start tunnel
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

### Step 7: Test Access

From anywhere on the internet:

```bash
curl https://photos.yourdomain.com/health
```

## Configuration Files Summary

### On Flask Server (192.168.1.104)

**`/opt/photo-registration-form/.env`:**
```bash
GUNICORN_BIND=0.0.0.0:5000
SECRET_KEY=your-generated-key
FLASK_ENV=production
```

### On Tunnel Server

**`/etc/cloudflared/config.yml`:**
```yaml
tunnel: abc123-your-tunnel-id
credentials-file: /root/.cloudflared/abc123.json

ingress:
  - hostname: photos.yourdomain.com
    service: http://192.168.1.104:5000
  - service: http_status:404
```

## Network Flow

```
Internet User
     │
     ▼
Cloudflare CDN (photos.yourdomain.com)
     │
     ▼
Cloudflare Tunnel Server (your LAN)
     │
     ▼
Local Network (192.168.1.x)
     │
     ▼
Flask Server (192.168.1.104:5000)
```

## Alternative: Using Port 80 (No Port in URL)

If you want the tunnel to connect to just `http://192.168.1.104` without specifying port:

### Option A: Using Nginx (Recommended)

1. Configure Flask to stay on port 5000
2. Install nginx on Flask server:
```bash
sudo bash install.sh
# Choose option 3: Configure settings
# Choose option 3: Install/Update Nginx configuration
# Enter hostname when prompted
```

3. Nginx will proxy port 80 → port 5000
4. Configure tunnel to: `service: http://192.168.1.104`

### Option B: Direct Port 80 (Advanced)

1. Configure Flask for port 80:
```bash
sudo bash install.sh
# Choose option 3: Configure settings
# Choose option 1: Configure network binding
# Choose option 3: Network on port 80 - 0.0.0.0:80
# Choose yes to add CAP_NET_BIND_SERVICE
```

2. Configure tunnel to: `service: http://192.168.1.104`

**Note:** Port 80 requires special privileges. The install script will configure this for you.

## Troubleshooting

### Can't Access from Network

```bash
# On Flask server, check what it's listening on
sudo netstat -tlnp | grep 5000

# Should show: 0.0.0.0:5000 (not 127.0.0.1:5000)
```

### Tunnel Can't Connect

```bash
# Check tunnel logs
sudo journalctl -u cloudflared -f

# Test from tunnel server
curl http://192.168.1.104:5000/health
```

### Firewall Blocking

```bash
# On Flask server, allow port 5000
sudo ufw allow 5000/tcp
sudo ufw status
```

### Check Current Configuration

```bash
# On Flask server
sudo bash install.sh
# Choose option 5: View status
```

## Security Notes

⚠️ **Important:** When Flask listens on `0.0.0.0:5000`, it's accessible from your entire LAN.

**Recommendations:**
1. Trust your local network, OR
2. Configure firewall to only allow connections from tunnel server:
   ```bash
   sudo ufw allow from <TUNNEL-SERVER-IP> to any port 5000
   ```
3. Use Cloudflare domain for all external access
4. Don't share `http://192.168.1.104:5000` publicly

## Summary

**Your setup in 3 commands:**

**On Flask server (192.168.1.104):**
```bash
sudo bash install.sh  # Option 3 → Option 1 → Option 2
```

**On Tunnel server:**
```bash
# Install cloudflared, then:
cloudflared tunnel create photo-registration
sudo nano /etc/cloudflared/config.yml  # Add config above
cloudflared tunnel route dns photo-registration photos.yourdomain.com
sudo cloudflared service install
sudo systemctl start cloudflared
```

**Done!** Access at `https://photos.yourdomain.com` 🎉

---

**Last Updated:** October 21, 2025
