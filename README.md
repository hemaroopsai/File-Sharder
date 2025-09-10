# 🔐 Secure File Sharder & Joiner

A web-based application to securely **encrypt, split files into multiple pieces, and join them back together**. The application is containerized with **Docker** for easy deployment.

---

## 📌 Prerequisites
- Docker must be installed and running on your system.

---

## 🚀 How to Run the Application
Follow these steps in your terminal from the project's root directory.

### 1. Build the Docker Image
This command reads the `Dockerfile` and builds a container image named `file-sharder-app`. The `.` at the end tells Docker to look for the Dockerfile in the current directory.
```bash
docker build -t file-sharder-app .
```

### 2. Run the Docker Container
This command starts a container from the image you just built:
```bash
docker run -d -p 8000:8000 --name file-sharder-container file-sharder-app
```

#### Command Breakdown
- `-d` : Runs the container in detached mode (in the background).
- `-p 8000:8000` : Maps port 8000 on your host machine to port 8000 inside the container.
- `--name file-sharder-container` : Gives your running container a memorable name.
- `file-sharder-app` : The name of the image to run.

---

## 🌐 Access the Application
Once the container is running, open your web browser and navigate to:

```
http://localhost:8000
```

You should see your File Sharder application served from the Docker container.

---

## ⏹️ How to Stop the Container
To stop the running application, use the following command:
```bash
docker stop file-sharder-container
```

---

## 📜 License
This project is licensed under the MIT License.

---

## 📝 3-Line Description
**Secure File Sharder & Joiner** is a web-based app that securely encrypts and splits files into multiple parts, with the ability to rejoin them easily.
It is containerized using **Docker** for simple setup and deployment.
The tool ensures safe file handling and quick access through a lightweight web interface.

