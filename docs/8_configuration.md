# 8. Configuration Management

Consistent and clear configuration is vital for the stability and maintainability of a multi-service application like Silhouet. This document outlines how configuration variables are managed across the project.

## The `.env` File

The primary source of configuration for the entire Dockerized environment is the `.env` file located in the project root.

*   **Purpose**: It provides a single place to define environment variables that can be used by multiple services in the `docker-compose.yml` file.
*   **How it Works**: Docker Compose automatically reads the `.env` file in the root directory and substitutes the variables into the `docker-compose.yml` file.
*   **Source Control**: The `.env` file itself should **never** be committed to source control, as it may contain sensitive credentials. Instead, the `.env.example` file serves as a template that **is** committed to the repository.

## `shared_config/` Directory

Some configuration is not a secret, but rather data that must be identical across multiple services to ensure they operate correctly.

*   **Purpose**: The `shared_config/` directory contains Python files with configuration data that is critical for the consistent operation of the `backend`, `model`, and `worker` services.
*   **Key File**: `silhouet_config.py`
    *   `PERSONALITY_KEYS`: This list of ~53 strings is the ground truth for the personality traits being scored. The order and content must be identical across all services that interact with scores to prevent data corruption or misinterpretation.
    *   `PERSONALITY_LABEL_MAP`: This dictionary maps the keys to the positive and negative example sentences used by the model service.
*   **How it's Used**: In the `docker-compose.yml` file, the `shared_config` directory is mounted as a volume into the relevant Python services (`backend`, `model`, `worker`). This ensures that when any of these services import from `silhouet_config`, they are all reading from the exact same file on the host machine.

This dual approach provides a clean separation between:
1.  **Environment-specific variables** (like passwords and URLs) managed by `.env`.
2.  **Application-wide constants** (like the personality keys) managed by `shared_config`.
