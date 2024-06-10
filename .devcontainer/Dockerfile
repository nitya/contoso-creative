# Use a specific tag for the bullseye image to ensure reproducibility
ARG IMAGE=python
ARG TAG=3.11
FROM --platform=amd64 mcr.microsoft.com/devcontainers/${IMAGE}:${TAG} as base

# Setting frontend to noninteractive to avoid user prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Combine RUN instructions to reduce layers, install necessary packages, and clean up in one layer to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends xdg-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install Azure DevOps (azd) in a single RUN command to reduce layers.
# Installed from daily version of azd (for latest updates)
# Ensure the use of `-s` and `-S` flags with curl for better error handling and security.
# The flags '--version' and '--skip-verify' should be used with caution; not specifying a version could lead to stability issues.
RUN curl -fsSL https://aka.ms/install-azd.sh | \
    bash -s -- \
      --version '' --skip-verify