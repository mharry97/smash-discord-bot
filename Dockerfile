# Use the official Microsoft Playwright image, which includes Python and all needed dependencies
FROM mcr.microsoft.com/playwright/python:v1.53.0-jammy

# Set the working directory
WORKDIR /app

# Copy your requirements file and install your bot's Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Set the command to run your bot
CMD ["python", "bot.py"]
