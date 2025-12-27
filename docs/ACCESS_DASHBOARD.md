# Accessing Photo Factory Dashboard

## Option 1: Windows Hosts File (Recommended)

Edit your Windows hosts file to map a friendly hostname to localhost.

### Steps:

1. **Open Notepad as Administrator:**
   - Press `Win + X` and select "Windows PowerShell (Admin)" or "Terminal (Admin)"
   - Or right-click Notepad → "Run as administrator"

2. **Open the hosts file:**
   - In Notepad, go to: `C:\Windows\System32\drivers\etc\hosts`
   - Or run: `notepad C:\Windows\System32\drivers\etc\hosts` (as admin)

3. **Add this line at the end:**
   ```
   127.0.0.1    photo.server
   ```

4. **Save the file** (you may need admin permissions)

5. **Access the dashboard:**
   - Open your browser and go to: `http://photo.server:8501`
   - Or: `http://photo.factory:8501`
   - Or: `http://dashboard.local:8501`

### Alternative Hostnames:

You can use any hostname you prefer:
```
127.0.0.1    photo.server
127.0.0.1    photo.factory
127.0.0.1    dashboard.local
127.0.0.1    factory.local
```

## Option 2: Use Homepage (Already Running)

Your Homepage service is already running on port 3000. You can add the dashboard as a shortcut there.

1. **Access Homepage:** `http://localhost:3000`
2. **Add Dashboard Service:**
   - Edit the Homepage config (usually in `Stack/App_Data/homepage/config.yaml`)
   - Add the dashboard service with URL: `http://localhost:8501`

## Option 3: Browser Bookmarks

Simply bookmark `http://localhost:8501` in your browser for quick access.

## Troubleshooting

- **Can't save hosts file:** Make sure you're running Notepad as Administrator
- **Hostname not working:** Clear your browser cache or try a different browser
- **Port 8501 not accessible:** Check that the dashboard container is running: `docker-compose ps dashboard`

