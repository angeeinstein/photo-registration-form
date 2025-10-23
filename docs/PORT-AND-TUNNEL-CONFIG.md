# Server Port and Cloudflare Tunnel Configuration Guide

## 🔌 Server Port Information

**Default Configuration:**
- **Port:** 5000
- **Bind Address:** 127.0.0.1 (localhost only)
- **Full Address:** http://127.0.0.1:5000

This means the server currently **only accepts connections from the same machine**.

## 🌐 Cloudflare Tunnel Configuration Options

You have **two main options** for Cloudflare Tunnel:

### ✅ Option 1: Tunnel to Localhost (Recommended & Current Setup)

**Configuration:**
```yaml
# /etc/cloudflared/config.yml
tunnel: <YOUR-TUNNEL-ID>
credentials-file: /root/.cloudflared/<YOUR-TUNNEL-ID>.json

ingress:
  - hostname: photos.yourdomain.com
    service: http://127.0.0.1:5000
  - service: http_status:404
```

**How it works:**
- Cloudflare Tunnel runs **on the same server** as your Flask app
- Tunnel connects to `127.0.0.1:5000` (local connection)
- No need to expose port 5000 to the network
- **Most secure** - application not accessible from LAN

**Advantages:**
- ✅ More secure (no network exposure)
- ✅ Works with current configuration (no changes needed)
- ✅ Cloudflare Tunnel and Flask on same machine
- ✅ No firewall rules needed

**When to use:**
- Cloudflare Tunnel daemon runs on the same server as the Flask app
- You want maximum security
- You only want access via Cloudflare domain

---

### ⚙️ Option 2: Tunnel to LAN IP (Alternative Setup)

**If you want:** `http://192.168.1.104:5000`

**Configuration needed:**

#### Step 1: Change Gunicorn bind address

Edit `gunicorn_config.py`:
```python
# Change from:
bind = "127.0.0.1:5000"

# To:
bind = "0.0.0.0:5000"  # Listen on all interfaces
# Or specifically:
bind = "192.168.1.104:5000"  # Listen only on LAN IP
```

#### Step 2: Configure Cloudflare Tunnel
```yaml
# /etc/cloudflared/config.yml
tunnel: <YOUR-TUNNEL-ID>
credentials-file: /root/.cloudflared/<YOUR-TUNNEL-ID>.json

ingress:
  - hostname: photos.yourdomain.com
    service: http://192.168.1.104:5000
  - service: http_status:404
```

**How it works:**
- Flask app listens on network interface
- Accessible from LAN as `http://192.168.1.104:5000`
- Cloudflare Tunnel (can be on different machine) connects to LAN IP
- Application exposed to local network

**Advantages:**
- ✅ Can access directly from LAN: `http://192.168.1.104:5000`
- ✅ Cloudflare Tunnel can run on different machine
- ✅ Easier for testing/debugging

**Disadvantages:**
- ⚠️ Application exposed to local network
- ⚠️ Need to configure firewall if enabled
- ⚠️ Less secure than localhost-only

**When to use:**
- Cloudflare Tunnel runs on a different machine
- You want LAN access for testing
- You trust your local network

---

## 🚀 Quick Setup Guide

### For Option 1 (Localhost - Recommended)

**No changes needed!** Your current setup already works.

1. Install Cloudflare Tunnel **on the same server**:
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

2. Login and create tunnel:
```bash
cloudflared tunnel login
cloudflared tunnel create photo-registration
```

3. Create config:
```bash
sudo nano /etc/cloudflared/config.yml
```

Add:
```yaml
tunnel: YOUR-TUNNEL-ID-HERE
credentials-file: /root/.cloudflared/YOUR-TUNNEL-ID.json

ingress:
  - hostname: photos.yourdomain.com
    service: http://127.0.0.1:5000
  - service: http_status:404
```

4. Route DNS and start:
```bash
cloudflared tunnel route dns photo-registration photos.yourdomain.com
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

### For Option 2 (LAN IP)

**Changes required:**

1. Update Gunicorn configuration:
```bash
sudo nano /opt/photo-registration-form/gunicorn_config.py
```

Change:
```python
bind = "0.0.0.0:5000"
```

2. Restart service:
```bash
sudo systemctl restart photo-registration
```

3. Test local access:
```bash
curl http://192.168.1.104:5000/health
```

4. Configure Cloudflare Tunnel (can be on any machine):
```yaml
# /etc/cloudflared/config.yml
tunnel: YOUR-TUNNEL-ID-HERE
credentials-file: /root/.cloudflared/YOUR-TUNNEL-ID.json

ingress:
  - hostname: photos.yourdomain.com
    service: http://192.168.1.104:5000
  - service: http_status:404
```

5. Start tunnel:
```bash
sudo cloudflared service install
sudo systemctl start cloudflared
```

---

## 🔒 Security Considerations

### Option 1 (127.0.0.1:5000) - Current Setup
- ✅ **Most Secure** - Only accessible via Cloudflare Tunnel
- ✅ Not exposed to LAN
- ✅ No firewall rules needed
- ✅ Cloudflare provides DDoS protection
- ✅ HTTPS automatically via Cloudflare

### Option 2 (0.0.0.0:5000 or 192.168.1.104:5000)
- ⚠️ Exposed to local network
- ⚠️ Anyone on LAN can access `http://192.168.1.104:5000`
- ⚠️ Consider adding firewall rules:
  ```bash
  # Allow only specific IPs
  sudo ufw allow from 192.168.1.0/24 to any port 5000
  ```
- ✅ Still protected by Cloudflare when accessed via domain
- ⚠️ Direct LAN access bypasses Cloudflare protection

---

## 📊 Comparison Table

| Aspect | Option 1 (127.0.0.1) | Option 2 (0.0.0.0 or LAN IP) |
|--------|---------------------|------------------------------|
| **Port** | 5000 | 5000 |
| **Bind Address** | 127.0.0.1 | 0.0.0.0 or 192.168.1.104 |
| **LAN Access** | ❌ No | ✅ Yes |
| **Cloudflare Access** | ✅ Yes | ✅ Yes |
| **Tunnel Location** | Same server | Any machine |
| **Security** | 🔒 High | ⚠️ Medium |
| **Firewall Needed** | ❌ No | ✅ Recommended |
| **Changes Required** | ✅ None | ⚙️ Config change |

---

## 🧪 Testing

### Test Flask Application

**If using 127.0.0.1:**
```bash
# On the server itself
curl http://127.0.0.1:5000/health

# From another machine (won't work)
curl http://192.168.1.104:5000/health  # Connection refused
```

**If using 0.0.0.0 or 192.168.1.104:**
```bash
# On the server
curl http://127.0.0.1:5000/health
curl http://192.168.1.104:5000/health

# From another machine in LAN
curl http://192.168.1.104:5000/health
```

### Test Cloudflare Tunnel

```bash
# Check tunnel status
sudo systemctl status cloudflared

# Check tunnel logs
sudo journalctl -u cloudflared -f

# Test via domain (both options)
curl https://photos.yourdomain.com/health
```

---

## 🔧 Configuration Files

### Current Setup (Option 1)

**`gunicorn_config.py`:**
```python
bind = "127.0.0.1:5000"  # ← Current (localhost only)
```

**Cloudflare Tunnel:**
```yaml
service: http://127.0.0.1:5000  # ← Connect to localhost
```

### Alternative Setup (Option 2)

**`gunicorn_config.py`:**
```python
bind = "0.0.0.0:5000"  # ← Listen on all interfaces
# OR
bind = "192.168.1.104:5000"  # ← Listen on specific IP
```

**Cloudflare Tunnel:**
```yaml
service: http://192.168.1.104:5000  # ← Connect to LAN IP
```

---

## 💡 Recommendation

**For your use case (fair event with public access):**

### Use Option 1 (Current Setup) ✅

**Why:**
1. More secure - no LAN exposure
2. Cloudflare handles all public traffic
3. DDoS protection included
4. Automatic HTTPS
5. No configuration changes needed
6. Works perfectly for your scenario

**Setup:**
- Keep `bind = "127.0.0.1:5000"` in gunicorn_config.py
- Install Cloudflare Tunnel on the same server (192.168.1.104)
- Configure tunnel to point to `http://127.0.0.1:5000`
- Access via your domain: `https://photos.yourdomain.com`

**When you'd need Option 2:**
- Only if Cloudflare Tunnel runs on a **different machine** than Flask
- If you need **direct LAN access** for testing
- If you have **multiple servers** and want centralized tunnel

---

## 📝 Summary

**Your Questions Answered:**

1. **"On which port does the server run?"**
   - **Port 5000** (configured in `gunicorn_config.py`)

2. **"Can I configure Cloudflare Tunnel to 192.168.1.104?"**
   - **Yes**, but you need to change `bind = "127.0.0.1:5000"` to `bind = "0.0.0.0:5000"` first
   - **Better option**: Keep current config and use `service: http://127.0.0.1:5000` in Cloudflare config
   - This requires Cloudflare Tunnel to run **on the same server** (192.168.1.104)

**Recommended Setup:**
```
Internet → Cloudflare → Tunnel (on 192.168.1.104) → localhost:5000 → Flask App
                                    ↑
                            Same server!
```

**Alternative Setup (if tunnel on different machine):**
```
Internet → Cloudflare → Tunnel (on 192.168.1.X) → 192.168.1.104:5000 → Flask App
                                    ↑                      ↑
                            Different machine!    Need to change bind!
```

---

**Last Updated:** October 21, 2025
