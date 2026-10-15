# Base image contains: Python 3.10, libmagic, Mega SDK, UPX-compressed masked binaries, and embedded aria.sh
FROM aquib4040/azmlv1:latest

WORKDIR /usr/src/app


# Copy requirements first (better caching)
COPY requirements.txt .

# Install dependencies using standalone uv
RUN uv pip install --system --break-system-packages --upgrade pip setuptools wheel \
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