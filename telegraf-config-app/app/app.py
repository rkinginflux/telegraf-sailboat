#!/usr/bin/env python3
"""
Telegraf Configuration Manager Web Application
Provides a web interface for users to create and manage custom Telegraf configurations
Updated with diskio templates - v1.1
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import toml
from datetime import datetime
import tempfile
import shutil

app = Flask(__name__)

# Configuration storage directory
CONFIG_DIR = "/app/configs"
os.makedirs(CONFIG_DIR, exist_ok=True)

@app.route('/')
def index():
    """Main configuration page"""
    return render_template('index.html')

@app.route('/api/templates')
def get_templates():
    """Get available Telegraf configuration templates"""
    templates = {
        "basic_cpu": {
            "name": "Basic CPU Monitoring",
            "description": "Monitor CPU usage with 10-second intervals",
            "config": """[agent]
  interval = "10s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000

[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "telegraf"
  retention_policy = ""

[[inputs.cpu]]
  percpu = true
  totalcpu = false
  collect_cpu_time = false
  report_active = false
"""
        },
        "memory_disk": {
            "name": "Memory and Disk Monitoring",
            "description": "Monitor memory usage and disk statistics",
            "config": """[agent]
  interval = "30s"
  round_interval = true
  metric_batch_size = 1000

[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "telegraf"

[[inputs.mem]]

[[inputs.disk]]
  mountpoints = ["/"]
  ignore_fs = ["tmpfs", "devtmpfs"]
"""
        },
        "network_monitoring": {
            "name": "Network Interface Monitoring",
            "description": "Monitor network interface statistics",
            "config": """[agent]
  interval = "15s"
  round_interval = true

[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "telegraf"

[[inputs.net]]
  interfaces = ["*"]
  ignore_protocol_stats = false
"""
        },
        "docker_containers": {
            "name": "Docker Container Monitoring",
            "description": "Monitor Docker container statistics",
            "config": """[agent]
  interval = "20s"
  round_interval = true

[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "telegraf"

[[inputs.docker]]
  endpoint = "unix:///var/run/docker.sock"
  container_names = []
  timeout = "5s"
"""
        },
        "diskio_monitoring": {
            "name": "Disk I/O Monitoring",
            "description": "Monitor disk I/O performance metrics including reads, writes, and timing statistics",
            "config": """[agent]
  interval = "10s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000

[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "telegraf"
  retention_policy = ""


[[inputs.diskio]]
  ## Devices to collect stats for (wildcards supported)
  devices = ["*"]

  ## Skip gathering of the disk's serial numbers
  skip_serial_number = false

  ## Device metadata tags to add (Linux only)
  device_tags = ["ID_FS_TYPE", "ID_FS_USAGE"]

  ## Customize device names via templates (useful for LVM volumes)
  name_templates = ["$ID_FS_LABEL","$DM_VG_NAME/$DM_LV_NAME"]
"""
        },
        "comprehensive_disk": {
            "name": "Comprehensive Disk Monitoring",
            "description": "Monitor both disk usage and I/O performance metrics",
            "config": """[agent]
  interval = "15s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000

[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "telegraf"
  retention_policy = ""

[[inputs.disk]]
  ## By default stats will be gathered for all mount points
  mount_points = ["/"]

  ## Ignore mount points by filesystem type
  ignore_fs = ["tmpfs", "devtmpfs", "devfs", "iso9660", "overlay", "aufs", "squashfs"]

[[inputs.diskio]]
  ## Devices to collect stats for (wildcards supported)
  devices = ["*"]

  ## Skip gathering of the disk's serial numbers
  skip_serial_number = false

  ## Device metadata tags to add (Linux only)
  device_tags = ["ID_FS_TYPE", "ID_FS_USAGE"]
"""
        }
    }
    return jsonify(templates)

@app.route('/api/config', methods=['POST'])
def save_config():
    """Save a new Telegraf configuration"""
    try:
        data = request.json
        config_name = data.get('name', '').strip()
        config_content = data.get('config', '')

        if not config_name:
            return jsonify({"error": "Configuration name is required"}), 400

        # Validate TOML syntax
        try:
            if config_content.strip():
                toml.loads(config_content)
        except toml.TomlDecodeError as e:
            return jsonify({"error": f"Invalid TOML syntax: {str(e)}"}), 400

        # Save configuration
        config_file = os.path.join(CONFIG_DIR, f"{config_name}.json")

        # Add metadata
        full_config = {
            "name": config_name,
            "created_at": datetime.now().isoformat(),
            "description": data.get('description', ''),
            "telegraf_config": config_content,
            "format": "toml"
        }

        with open(config_file, 'w') as f:
            json.dump(full_config, f, indent=2)

        return jsonify({
            "message": "Configuration saved successfully",
            "config_file": config_file
        })

    except Exception as e:
        return jsonify({"error": f"Failed to save configuration: {str(e)}"}), 500

@app.route('/api/configs')
def list_configs():
    """List all saved configurations"""
    try:
        configs = []
        for filename in os.listdir(CONFIG_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(CONFIG_DIR, filename)
                with open(filepath, 'r') as f:
                    config = json.load(f)
                    configs.append({
                        "name": config.get('name', ''),
                        "description": config.get('description', ''),
                        "created_at": config.get('created_at', ''),
                        "filename": filename
                    })

        return jsonify(configs)

    except Exception as e:
        return jsonify({"error": f"Failed to list configurations: {str(e)}"}), 500

@app.route('/api/config/<config_name>')
def get_config(config_name):
    """Get a specific configuration"""
    try:
        config_file = os.path.join(CONFIG_DIR, f"{config_name}.json")

        if not os.path.exists(config_file):
            return jsonify({"error": "Configuration not found"}), 404

        with open(config_file, 'r') as f:
            config = json.load(f)

        return jsonify(config)

    except Exception as e:
        return jsonify({"error": f"Failed to load configuration: {str(e)}"}), 500

@app.route('/api/config/<config_name>/download')
def download_config(config_name):
    """Download configuration as TOML file"""
    try:
        config_file = os.path.join(CONFIG_DIR, f"{config_name}.json")

        if not os.path.exists(config_file):
            return jsonify({"error": "Configuration not found"}), 404

        with open(config_file, 'r') as f:
            config = json.load(f)

        # Get TOML content directly (stored as TOML string now)
        telegraf_config = config.get('telegraf_config', '')

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False)
        temp_file.write(telegraf_config)
        temp_file.close()

        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"{config_name}.conf",
            mimetype='text/plain'
        )

    except Exception as e:
        return jsonify({"error": f"Failed to download configuration: {str(e)}"}), 500

@app.route('/api/config/<config_name>', methods=['DELETE'])
def delete_config(config_name):
    """Delete a configuration"""
    try:
        config_file = os.path.join(CONFIG_DIR, f"{config_name}.json")

        if not os.path.exists(config_file):
            return jsonify({"error": "Configuration not found"}), 404

        os.remove(config_file)

        return jsonify({"message": "Configuration deleted successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to delete configuration: {str(e)}"}), 500

@app.route('/api/validate-toml', methods=['POST'])
def validate_toml():
    """Validate TOML syntax"""
    try:
        data = request.json
        toml_content = data.get('content', '')

        if not toml_content.strip():
            return jsonify({"error": "TOML content is empty"}), 400

        # Validate TOML syntax
        try:
            toml.loads(toml_content)
            return jsonify({"valid": True, "message": "Valid TOML syntax"})
        except toml.TomlDecodeError as e:
            return jsonify({"valid": False, "error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to validate TOML: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
