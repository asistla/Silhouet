#!/bin/bash
set -e

# --- Script for automated Docker and NVIDIA Container Toolkit setup ---
# Designed for a clean Ubuntu/Debian-based server.
#
# USAGE:
# 1. Upload this script to your remote server.
# 2. Run with sudo: sudo ./deploy_setup.sh
# 3. After the script finishes, copy your project files and run 'docker-compose up -d'.

# ---------------------------------------------------------------------

# A function to check for sudo privileges
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run this script with sudo."
        exit 1
    fi
}

# A function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ---------------------------------------------------------------------
# Step 1: Check for NVIDIA Drivers
# This script does NOT install GPU drivers. This is a system-specific task.
# We will check if they are present before proceeding.
# ---------------------------------------------------------------------
echo "--- Checking for NVIDIA drivers..."
if ! command_exists nvidia-smi; then
    echo "NVIDIA drivers not found. Please install them manually before running this script."
    echo "Refer to NVIDIA's official site for installation instructions for your specific OS and GPU model."
    exit 1
fi
echo "NVIDIA drivers found."

# ---------------------------------------------------------------------
# Step 2: Install Docker
# ---------------------------------------------------------------------
echo "--- Installing Docker..."
if command_exists docker; then
    echo "Docker is already installed. Skipping installation."
else
    # Install dependencies
    apt-get update
    apt-get install -y ca-certificates curl gnupg

    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add Docker repository to Apt sources
    echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker packages
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add current user to the 'docker' group to run commands without sudo
    # This change takes effect after logging out and back in
    if [ -n "$SUDO_USER" ]; then
        usermod -aG docker "$SUDO_USER"
        echo "User '$SUDO_USER' added to the 'docker' group. Please log out and back in to use docker without sudo."
    fi
fi
echo "Docker installation complete."

# ---------------------------------------------------------------------
# Step 3: Install NVIDIA Container Toolkit
# ---------------------------------------------------------------------
echo "--- Installing NVIDIA Container Toolkit..."
if command_exists nvidia-container-toolkit; then
    echo "NVIDIA Container Toolkit is already installed. Skipping installation."
else
    # Add NVIDIA's GPG key
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/ubuntu/$(. /etc/os-release;echo $VERSION_CODENAME)/libnvidia-container.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    # Install the toolkit
    apt-get update
    apt-get install -y nvidia-container-toolkit

    # Configure Docker to use the toolkit and restart the daemon
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
fi
echo "NVIDIA Container Toolkit installation complete."

# ---------------------------------------------------------------------
# Step 4: Install Docker Compose
# ---------------------------------------------------------------------
echo "--- Installing Docker Compose..."
if command_exists docker-compose; then
    echo "Docker Compose is already installed. Skipping installation."
else
    # The new 'docker-compose' is a Docker plugin, but we'll install a symlink for backward compatibility.
    # The 'docker-compose-plugin' was already installed with docker-ce above.
    echo "docker-compose-plugin is installed with docker. Creating symbolic link."
    ln -s /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
fi
echo "Docker Compose installation complete."

# ---------------------------------------------------------------------
# Step 5: Final Instructions
# ---------------------------------------------------------------------
echo "--- Setup Complete ---"
echo "Your server is now ready for deployment."
echo "Final steps:"
echo "1. Log out and back in for the 'docker' group changes to take effect (if applicable)."
echo "2. Upload your project directory to this server."
echo "3. Navigate to your project directory and run: docker-compose up -d"
