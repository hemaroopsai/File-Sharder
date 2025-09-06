# This gives us a clean Linux environment with Python 3.11 pre-installed.
FROM python:3.11-slim

# 2. Set the working directory inside the container
# All subsequent commands will run from this path.
WORKDIR /app

# 3. Install system dependencies required for building some Python packages
# This is the crucial fix: it installs compilers (like gcc) needed by libraries like cryptography.
RUN apt-get update && apt-get install -y build-essential

# 4. Copy the dependency requirements file
COPY requirements.txt .

# 5. Install the Python dependencies
# This command reads requirements.txt and installs the libraries.
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code into the container
COPY . .

# 7. Expose the port the app runs on
# This tells Docker that the container will listen on port 8000.
EXPOSE 8000

# 8. Define the command to run the application
# This is what starts the FastAPI server when the container launches.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
