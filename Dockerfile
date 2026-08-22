FROM mysterysd/wzmlx:latest

WORKDIR /usr/src/app

# Avoid permission issues
RUN chmod -R 777 /usr/src/app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install uv for blazingly fast Python package installation
RUN pip3 install uv \
    && uv pip install --system --upgrade pip setuptools wheel \
    && uv pip install --system "setuptools_scm<8" \
    && uv pip install --system vcs_versioning \
    && uv pip install --system --no-cache -r requirements.txt

# Copy project files
COPY . .

# Start bot
CMD ["bash", "start.sh"]