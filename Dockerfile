FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install browsers one more time to be sure (though image has them)
RUN playwright install chromium

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
