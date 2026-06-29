FROM mysterysd/wzmlx:latest

WORKDIR /usr/src/app

# Avoid permission issues
RUN chmod -R 777 /usr/src/app

# Install system dependencies (important for media bots)
RUN apt-get update && apt-get install -y \
    mediainfo \
    ffmpeg \
    && apt-get clean

# Copy requirements first (better caching)
COPY requirements.txt .

# Install uv for blazingly fast Python package installation
RUN pip3 install uv \
    && uv pip install --system --upgrade pip setuptools wheel \
    && uv pip install --system "setuptools_scm<8" \
    && uv pip install --system vcs_versioning \
    && uv pip install --system --no-cache -r requirements.txt

# Install Playwright (your original step)
# RUN playwright install --with-deps chromium

# Copy project files
COPY . .

# Start bot
CMD ["bash", "start.sh"]