# CloudTrace Deployment Guide

This guide explains how the CI/CD pipeline works and how to deploy CloudTrace to your DigitalOcean droplet.

## CI/CD Pipeline Overview

The CloudTrace application uses GitHub Actions for continuous integration and deployment. The pipeline consists of three main steps:

1. **Test**: Runs unit tests to ensure code quality
2. **Build**: Creates a distributable package
3. **Deploy**: Deploys the application to your DigitalOcean droplet

## Automatic Deployment

When you push changes to the `main` branch, the CI/CD pipeline automatically:

1. Runs all tests
2. Builds the application package
3. Deploys to your DigitalOcean droplet

The deployment process:
- Transfers application files to your server
- Sets up required configurations
- Restarts the service

## Manual Deployment

If needed, you can also deploy manually:

1. SSH into your DigitalOcean droplet
   ```bash
   ssh deploy@your-droplet-ip
   ```

2. Navigate to the application directory
   ```bash
   cd /home/deploy/cloudtrace
   ```

3. Pull the latest changes
   ```bash
   git pull origin main
   ```

4. Run the deployment script
   ```bash
   bash deploy.sh
   ```

## Requirements for Raw Socket Access

CloudTrace uses traceroute functionality which requires raw socket access. The systemd service file (`cloudtrace.service`) is configured with the `CAP_NET_RAW` capability to allow this without running the entire application as root.

If you experience permission issues, you can verify the service capabilities:

```bash
sudo systemctl status cloudtrace.service
sudo grep CapabilityBoundingSet /proc/$(pgrep -f app.py)/status
```

## Monitoring the Application

To monitor the application:

1. Check service status
   ```bash
   sudo systemctl status cloudtrace.service
   ```

2. View application logs
   ```bash
   sudo tail -f /var/log/cloudtrace/stdout.log
   sudo tail -f /var/log/cloudtrace/stderr.log
   ```

3. Check Nginx logs
   ```bash
   sudo tail -f /var/log/nginx/access.log
   sudo tail -f /var/log/nginx/error.log
   ```

## Updating the Application

1. Make changes to your local repository
2. Commit and push to GitHub
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```
3. The CI/CD pipeline will automatically deploy your changes

## Troubleshooting

### Permission Issues

If the application doesn't have the necessary permissions:

1. Check the service file
   ```bash
   sudo cat /etc/systemd/system/cloudtrace.service
   ```

2. Make sure the `CAP_NET_RAW` capability is set
   ```bash
   # If not, edit the service file
   sudo nano /etc/systemd/system/cloudtrace.service
   
   # Add these lines in the [Service] section
   CapabilityBoundingSet=CAP_NET_RAW
   AmbientCapabilities=CAP_NET_RAW

   # Reload and restart
   sudo systemctl daemon-reload
   sudo systemctl restart cloudtrace.service
   ```

### Deployment Failures

If the GitHub Actions deployment fails:

1. Check the GitHub Actions logs for errors
2. Verify that your GitHub Secrets are correct:
   - `SSH_PRIVATE_KEY`
   - `DROPLET_IP`
   - `DROPLET_USER`
   - `DEPLOY_PATH`

3. Try a manual deployment to see more detailed error messages

### Service Won't Start

If the service fails to start:

```bash
# Check detailed status
sudo systemctl status cloudtrace.service

# Check journal logs
sudo journalctl -u cloudtrace.service

# Verify file permissions
sudo ls -la /home/deploy/cloudtrace
sudo ls -la /home/deploy/cloudtrace/app.py
```

## Reverting to Previous Version

If needed, you can revert to a previous version:

```bash
# SSH to your server
ssh deploy@your-droplet-ip

# Go to application directory
cd /home/deploy/cloudtrace

# Check git log for commit to revert to
git log --oneline

# Revert to specific commit
git reset --hard <commit-hash>

# Run deployment script
bash deploy.sh
```

## Additional Resources

- See `SERVER_SETUP.md` for initial server configuration
- See `cloudtrace.service` for the systemd service configuration 