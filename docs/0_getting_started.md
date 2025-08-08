# 0. Getting Started: A Developer's Onboarding Guide

Welcome to the Silhouet project. This guide provides all the necessary steps to set up and run the entire application stack on your local machine for development purposes.

## Prerequisites

Before you begin, ensure you have the following software installed on your system:

*   **Docker**: The platform for running the application's containerized services.
*   **Docker Compose**: The tool for defining and running the multi-container Docker application.

## Setup and Installation

### 1. Clone the Repository

If you haven't already, clone the project repository to your local machine.

```bash
git clone <your-repository-url>
cd Silhouet
```

### 2. Create Your Environment Configuration

The project uses an `.env` file in the root directory to manage all necessary environment variables, such as database credentials and service URLs. A template is provided for you.

**Copy the example file to create your own local configuration:**

```bash
cp .env.example .env
```

For local development, the default values in the `.env.example` file are sufficient to get the application running. You do not need to change them unless you have a specific port conflict or other custom requirement.

### 3. Build and Launch the Services

With Docker running, use Docker Compose to build the images for all services and launch them in detached mode (`-d`).

```bash
docker-compose up -d --build
```

*   `--build`: This flag forces Docker Compose to rebuild the images from the Dockerfiles. You should use this the first time you launch the application or whenever you make changes to a `Dockerfile`, `requirements.txt`, or `package.json`.
*   `-d`: This flag runs the containers in the background.

This command will:
1.  Pull the base images (Postgres, Redis).
2.  Build the custom images for the `frontend`, `backend`, `worker`, and `model` services.
3.  Create and start containers for all services.
4.  Establish a Docker network for the services to communicate with each other.

### 4. Accessing the Application

Once all the containers are up and running, you can access the different parts of the application:

*   **Frontend Application**: Open your web browser and navigate to:
    *   `http://localhost:3000`

*   **Backend API Docs**: The FastAPI backend automatically generates interactive API documentation. You can access it at:
    *   `http://localhost:8000/docs`

### 5. Stopping the Application

To stop all running services, use the following command:

```bash
docker-compose down
```

This will stop and remove the containers and the network created by `docker-compose up`. To also remove the database volume (and all its data), you can add the `-v` flag: `docker-compose down -v`.
