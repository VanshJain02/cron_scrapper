# Use official Python image
FROM python:3.10-slim

# Install system deps for Playwright + Chromium
RUN apt-get update && apt-get install -y wget gnupg curl \
    libglib2.0-0 libnss3 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxi6 libxtst6 libxrandr2 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
    libdrm2 libxss1 libgbm1 libxshmfence1 libxext6 libegl1 libnss3 libatk1.0-0 \
    fonts-liberation libappindicator1 libappindicator3-1 libdbusmenu-glib4 \
    libdbusmenu-gtk3-4 libx11-xcb-dev && apt-get clean

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright and Chromium
RUN pip install playwright && playwright install chromium

# Add app files
COPY . /app
WORKDIR /app

# Set entrypoint
CMD ["python", "cron_scrapper.py"]
