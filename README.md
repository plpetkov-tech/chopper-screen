# Chopper Screen Dashboard

A containerized web content display system designed for framebuffer devices (like Raspberry Pi screens, and as in our case, a OnePlus 6 with PostmarketOS screen). Captures screenshots of web pages and displays them on a physical screen with configurable refresh rates and night mode.

## Features

- **Web Content Display**: Captures and displays any web URL on a framebuffer device
- **Configurable Refresh**: Set custom refresh intervals for content updates
- **Night Mode**: Automatically turns off the screen during specified hours
- **Fully Configurable**: All settings controllable via environment variables
- **Kubernetes Ready**: Includes DaemonSet manifest with ConfigMap support
- **Multi-Architecture**: Supports AMD64, ARM64 (aarch64), and ARMv7 - automatically pulls the right image for your device
- **Auto-Backlight Control**: Automatically detects and controls screen backlight
- **Health Checks**: Built-in health monitoring for Kubernetes

## Quick Start

### Docker

```bash
docker run -d \
  --privileged \
  --device=/dev/fb0 \
  -v /dev/input:/dev/input:ro \
  -v /sys/class/backlight:/sys/class/backlight \
  -e DISPLAY_URL="https://your-dashboard.com" \
  -e REFRESH_INTERVAL="300" \
  ghcr.io/plpetkov-tech/chopper-screen:latest
```

### Kubernetes

```bash
# Edit manifest.yaml ConfigMap with your settings
kubectl apply -f manifest.yaml
```

## Configuration

All configuration is done via environment variables. You can change these without rebuilding the image!

### Display Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY_URL` | `https://google.com` | URL to display |
| `WINDOW_WIDTH` | `800` | Screenshot width in pixels |
| `WINDOW_HEIGHT` | `600` | Screenshot height in pixels |
| `FULLSCREEN` | `true` | Enable fullscreen mode |
| `REFRESH_INTERVAL` | `300` | Refresh interval in seconds |

### Night Mode

| Variable | Default | Description |
|----------|---------|-------------|
| `NIGHT_MODE_ENABLED` | `true` | Enable night mode |
| `NIGHT_START` | `22:00` | Night mode start time (HH:MM) |
| `NIGHT_END` | `07:00` | Night mode end time (HH:MM) |

### Chromium Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMIUM_PATH` | `chromium-browser` | Path to Chromium executable |
| `CHROMIUM_TIMEOUT` | `30` | Screenshot timeout in seconds |
| `SCREENSHOT_PATH` | `/tmp/screenshot.png` | Temporary screenshot location |

### Backlight Control

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKLIGHT_PATH` | (auto-detect) | Path to backlight brightness file |
| `BACKLIGHT_MAX` | `255` | Maximum backlight brightness value |

### System Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CHECK_INTERVAL` | `60` | Schedule check interval in seconds |
| `SDL_VIDEODRIVER` | (auto-detect) | SDL video driver - auto-detects kmsdrm, fbcon, or directfb. Override if needed. |

## Deployment Examples

### Raspberry Pi with Local Dashboard

```yaml
# In manifest.yaml ConfigMap
DISPLAY_URL: "http://localhost:3000/dashboard"
REFRESH_INTERVAL: "60"
WINDOW_WIDTH: "1920"
WINDOW_HEIGHT: "1080"
NIGHT_MODE_ENABLED: "false"
```

### Public Website with Night Mode

```yaml
DISPLAY_URL: "https://status.example.com"
REFRESH_INTERVAL: "300"
NIGHT_START: "20:00"
NIGHT_END: "08:00"
```

### OnePlus 6 with PostmarketOS (Our Setup!)

```yaml
DISPLAY_URL: "https://your-awesome-dashboard.com"
REFRESH_INTERVAL: "120"
WINDOW_WIDTH: "1080"   # OnePlus 6 native resolution
WINDOW_HEIGHT: "2280"  # Portrait mode
NIGHT_MODE_ENABLED: "true"
NIGHT_START: "23:00"
NIGHT_END: "07:00"
BACKLIGHT_PATH: ""  # Auto-detect on PostmarketOS
```

### Multiple Displays (Node Selector)

For targeting specific nodes with displays:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        hardware: display-screen
```

## Building from Source

```bash
# Build the image
docker build -t chopper-screen:local .

# Run locally
docker run -d \
  --privileged \
  --device=/dev/fb0 \
  -e DISPLAY_URL="https://example.com" \
  chopper-screen:local
```

## CI/CD

The project includes a GitHub Actions workflow that automatically:
- Builds multi-architecture images (AMD64, ARM64, ARMv7)
- Pushes to GitHub Container Registry
- Creates tags for branches and releases
- Maintains a `latest` tag for the main branch

### Triggering Builds

- **Push to `main`**: Builds and tags as `latest`
- **Push to other branches**: Builds and tags with branch name
- **Create tag `v*`**: Builds and tags as release version
- **Manual**: Use "Run workflow" in GitHub Actions

## Dependency Management

This project uses [Renovate](https://renovatebot.com) to automatically keep all dependencies up-to-date.

### What Gets Updated

- **Docker Base Image**: Alpine Linux version (pinned to `3.20`)
- **Python Packages**: pygame and schedule (from `requirements.txt`)
- **GitHub Actions**: All action versions with SHA pinning for security

### How It Works

Renovate runs weekly (Monday mornings) and creates Pull Requests for:
- Minor/patch updates grouped together
- Major updates separated for review
- Security vulnerabilities immediately

### Configuration

All Renovate settings are in `renovate.json`:
- **Schedule**: Before 6am on Mondays
- **Auto-merge**: Disabled (requires manual review)
- **Dependency Dashboard**: Enabled (shows all pending updates)
- **Vulnerability Alerts**: Enabled with security label

### Enabling Renovate

1. Install the [Renovate GitHub App](https://github.com/apps/renovate) on your repository
2. Renovate will automatically detect `renovate.json` and start creating PRs
3. Review and merge PRs as they appear
4. Check the Dependency Dashboard issue for an overview of all updates

## Hardware Requirements

- Framebuffer device (`/dev/fb0`)
- Sufficient memory for Chromium (minimum 256MB recommended)
- Optional: Backlight control support

### Tested Hardware

- **Raspberry Pi** (all models with display)
- **OnePlus 6** running PostmarketOS (aarch64)

## Troubleshooting

### Screen not displaying

1. Check framebuffer is available: `ls -l /dev/fb0`
2. Verify container has privileged access
3. Check logs: `kubectl logs -f daemonset/screen-dashboard`

### Permission denied on backlight

- Ensure container runs with `privileged: true`
- Check backlight path exists: `ls /sys/class/backlight/`

### Chromium timeout

- Increase `CHROMIUM_TIMEOUT` for slow-loading pages
- Check network connectivity from container
- Verify URL is accessible

### Night mode not working

- Verify time format is `HH:MM` (24-hour)
- Check container timezone matches your timezone
- Look for "Night time" in logs

### SDL video driver errors (fbcon not available)

The app automatically tries multiple video drivers (kmsdrm → fbcon → directfb → dummy).

- **Check logs** to see which driver was selected: `kubectl logs -f <pod-name>`
- **Modern devices** (PostmarketOS, newer kernels) use `kmsdrm`
- **Legacy devices** (older Raspberry Pi) use `fbcon`
- **Override driver** if auto-detection fails:
  ```yaml
  env:
  - name: SDL_VIDEODRIVER
    value: "kmsdrm"  # or fbcon, directfb
  ```
- Ensure container has `/dev/dri` access for kmsdrm:
  ```yaml
  volumeMounts:
  - name: dri
    mountPath: /dev/dri
  volumes:
  - name: dri
    hostPath:
      path: /dev/dri
  ```

## Development

### Project Structure

```
.
├── dashboard.py           # Main application
├── requirements.txt       # Python dependencies (pinned versions)
├── Dockerfile            # Container image definition
├── manifest.yaml         # Kubernetes deployment
├── renovate.json         # Dependency update configuration
└── .github/
    └── workflows/
        └── docker-build-push.yml  # CI/CD pipeline
```

### Running Tests

```bash
# Test the dashboard locally (requires display)
python3 dashboard.py

# Test with environment variables
DISPLAY_URL=https://example.com FULLSCREEN=false python3 dashboard.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - feel free to use and modify as needed.

## Support

For issues and questions, please open an issue on GitHub.
