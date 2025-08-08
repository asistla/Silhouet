# 9. Testing Guide

This guide provides instructions on how to run the automated tests for the Silhouet project to verify its functionality and prevent regressions.

## Backend Testing (Pytest)

The backend tests are written using the `pytest` framework and are located in the `test_silhouet.py` file. These tests should be run from within the `backend` service container to ensure they have access to the same environment as the application.

### Running the Tests

1.  **Ensure services are running**: Make sure your Docker containers are up and running.
    ```bash
    docker-compose up -d
    ```

2.  **Execute `pytest` inside the container**: Use `docker-compose exec` to run the `pytest` command inside the `backend` container.

    ```bash
    docker-compose exec backend pytest
    ```

    This command will automatically discover and run the tests in `test_silhouet.py`. You will see the output in your terminal.

## Frontend Testing (React Testing Library)

The frontend tests are set up with Create React App's default testing framework, which uses Jest and React Testing Library. The test files are located in the `frontend/src/` directory (e.g., `App.test.tsx`).

### Running the Tests

1.  **Execute `npm test` inside the container**: Use `docker-compose exec` to run the test script defined in `package.json` inside the `frontend` container.

    ```bash
    docker-compose exec frontend npm test
    ```

    This will start the Jest test runner in interactive watch mode. It will run all test files and then wait for changes.

    *   Press `a` to run all tests.
    *   Press `q` to quit the watch mode.

This setup allows you to run tests for each service independently, in an environment that mirrors production.
