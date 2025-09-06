# 1. Use a modern, slim Python base image
FROM python:3.11-slim

# 2. Set up the working directory inside the container
WORKDIR /app

# 3. Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y build-essential

# 4. Copy the dependencies file first to leverage Docker's layer caching
COPY requirements.txt .

# 5. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code into the container
COPY . .

# 7. Expose the port Gunicorn will run on
EXPOSE 8000

# 8. Use Gunicorn to run the app with an increased timeout
#    -w 4: Use 4 worker processes
#    -k uvicorn.workers.UvicornWorker: The worker class for ASGI apps
#    --timeout 120: Allow workers 120 seconds to handle a request
#    --bind 0.0.0.0:8000: Listen on port 8000 for external traffic
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--timeout", "120"]

