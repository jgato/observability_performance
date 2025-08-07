#!/usr/bin/env python3
# Copyright 2024 Jose Gato Luis <jgato@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Setup script for the OpenShift Prometheus Query Tool.
"""

import os
import sys
import subprocess


def run_command(command, description):
    """Run a shell command and print the result."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stderr:
            print(f"  Error: {e.stderr.strip()}")
        return False


def main():
    """Main setup function."""
    print("OpenShift Prometheus Query Tool Setup")
    print("=" * 40)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    if sys.version_info < (3, 7):
        print("⚠️  Warning: Python 3.7+ is recommended")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("❌ Failed to install dependencies. Please check your pip installation.")
        return False
    
    # Make scripts executable
    scripts = ["main.py", "example_usage.py"]
    for script in scripts:
        if os.path.exists(script):
            run_command(f"chmod +x {script}", f"Making {script} executable")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Get your OpenShift bearer token: oc whoami -t")
    print("2. Get your Prometheus URL: oc get route prometheus-k8s -n openshift-monitoring")
    print("3. Run the tool: python main.py --token YOUR_TOKEN --url YOUR_URL --list-presets")
    print("\nFor more information, see README.md")


if __name__ == "__main__":
    main() 