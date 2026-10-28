FROM mysterysd/wzmlx:latest

WORKDIR /usr/src/app

# Install official standalone uv binaries so subprocess and shell can always use uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Ensure uv is in PATH
ENV PATH="/bin:/usr/local/bin:$PATH"

# Avoid permission issues
RUN chmod -R 777 /usr/src/app

# Install system dependencies (important for media bots)
RUN apt-get update && apt-get install -y \
    mediainfo \
    ffmpeg \
    curl \
    && apt-get clean

# Install cloudflared for free HTTPS Quick Tunnels
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared \
    && chmod +x /usr/local/bin/cloudflared

# Install HatchZip for in-place, space-saving archive extraction
RUN (curl -fsSL https://raw.githubusercontent.com/xevrion/hatchzip/main/install.sh | HATCHZIP_INSTALL_DIR=/usr/local/bin sh) \
    || ( \
        ARCH=$(uname -m) && \
        case "$ARCH" in \
            x86_64|amd64) HZ_ARCH="x86_64" ;; \
            aarch64|arm64) HZ_ARCH="aarch64" ;; \
            *) HZ_ARCH="x86_64" ;; \
        esac && \
        curl -fsSL "https://github.com/xevrion/hatchzip/releases/latest/download/hatchzip-${HZ_ARCH}-linux.tar.gz" -o /tmp/hatchzip.tar.gz && \
        tar -xzf /tmp/hatchzip.tar.gz -C /tmp && \
        cp "/tmp/hatchzip-${HZ_ARCH}-linux/hatchzip" /usr/local/bin/hatchzip && \
        chmod +x /usr/local/bin/hatchzip && \
        ln -sf /usr/local/bin/hatchzip /usr/local/bin/hz && \
        rm -rf /tmp/hatchzip* \
    ) && (hatchzip --version || true)

# Copy requirements first (better caching)
COPY requirements.txt .

# Install uv for blazingly fast Python package installation
RUN pip3 install --no-cache-dir uv \
    && uv pip install --system --break-system-packages --upgrade pip setuptools wheel \
    && uv pip install --system --break-system-packages "setuptools_scm<8" \
    && uv pip install --system --break-system-packages vcs_versioning \
    && uv pip install --system --break-system-packages --no-cache -r requirements.txt \
    && python3 -c "import hashlib; open('.requirements_installed', 'w').write(hashlib.sha256(open('requirements.txt', 'rb').read()).hexdigest())"

# Install Playwright
# RUN playwright install --with-deps chromium

# Copy project files
COPY . .

# Start bot
CMD ["bash", "start.sh"]