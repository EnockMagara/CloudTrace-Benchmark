# CloudTrace

![CloudTrace Logo](static/img/logo.svg)

CloudTrace is a cloud provider benchmark tool that measures and visualizes network performance to major cloud providers. It helps you make informed decisions about which cloud provider might offer the best network performance for your specific location and needs.

## Features

- **Multi-provider Benchmarking**: Test network performance to AWS, Azure, Google Cloud, Oracle Cloud, and more
- **Interactive Visualizations**: 
  - World map showing network paths
  - Charts comparing latency, packet loss, and hop count
  - Detailed traceroute data with geolocation information
- **Real-time Progress Tracking**: Monitor benchmark progress with live updates
- **Responsive Design**: Works on desktop and mobile devices
- **Background Processing**: Run benchmarks without blocking the UI
- **Detailed Reports**: Get comprehensive metrics including:
  - Average round-trip time (RTT)
  - Maximum/minimum latency
  - Packet loss percentage
  - Hop count
  - Geographic path information

## Requirements

- Python 3.7+
- Flask
- Geolocation API access
- Root/Administrator privileges (for traceroute functionality)

## Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cloudtrace.git
   cd cloudtrace
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   # On Linux/Mac (with sudo for raw socket access)
   sudo python app.py
   
   # On Windows (run as Administrator)
   python app.py
   ```

5. Access the application:
   Open your browser and navigate to `http://localhost:5000`

## Important Note on Permissions

CloudTrace uses traceroute functionality that requires raw socket access. You must run the application with Administrator (Windows) or root (Linux/macOS) privileges for full functionality.

## Project Structure

- `app.py` - Main Flask application
- `src/` - Core application code
  - `benchmark.py` - Benchmark logic
  - `tracer.py` - Traceroute implementation
  - `geo.py` - Geolocation services
- `static/` - CSS, JavaScript, and images
- `templates/` - HTML templates
- `data/` - Data storage for benchmark results

## Deployment

For production deployment, refer to these guides:

- [Server Setup Guide](SERVER_SETUP.md) - How to set up your server
- [Deployment Guide](DEPLOYMENT.md) - How to deploy the application
- [HTTPS Setup Guide](HTTPS_SETUP.md) - How to secure your site with HTTPS
- [CI/CD Pipeline](.github/workflows/deploy.yml) - GitHub Actions workflow

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- All the cloud providers whose endpoints we benchmark
- MaxMind for GeoLite2 database
- OpenStreetMap for map data