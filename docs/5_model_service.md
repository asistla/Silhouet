# 5. Model Service

The Model Service is a dedicated FastAPI microservice responsible for the core task of analyzing text and assigning personality scores. It is designed to be stateless and scalable.

## Core Technology

*   **Framework**: FastAPI (Python)
*   **Model**: `sentence-transformers/all-mpnet-base-v2`
*   **Library**: `PyTorch` for tensor operations.

## API Endpoint

### `POST /score`

*   **Description**: Accepts a block of text and returns a dictionary of personality scores.
*   **Request Body**:
    ```json
    {
      "text": "string"
    }
    ```
*   **Response (200 OK)**: A JSON object containing the scores.
    ```json
    {
      "scores": {
        "intellectual_honesty": -0.23,
        "courage": 0.51,
        ...
      }
    }
    ```

## Scoring Logic

The scoring mechanism is based on semantic similarity using vector embeddings.

1.  **Initialization**: When the service starts, it pre-processes the `PERSONALITY_LABEL_MAP` from `silhouet_config.py`. For each of the ~53 personality traits, it does the following:
    *   It takes the positive example sentence (e.g., "I could be wrong...") and the negative example sentence (e.g., "I already know I'm right...").
    *   It uses the Sentence Transformer model to encode each sentence into a high-dimensional vector (embedding).
    *   These "pole" vectors (one positive, one negative) for every trait are stored in memory for quick access.

2.  **Scoring a Post**: When a request comes to `/score`:
    *   The input text from the post is encoded into its own vector embedding using the same model.
    *   For each personality trait, the service calculates the **cosine similarity** between the post's embedding and the pre-computed positive and negative pole vectors.
    *   The final score for the trait is calculated as: `(similarity_to_positive_vector) - (similarity_to_negative_vector)`.
    *   This results in a score ranging from **-1.0** (perfectly aligned with the negative pole) to **+1.0** (perfectly aligned with the positive pole), with 0.0 representing neutrality or equal similarity to both.

## Modeling Philosophy and Future Work

The current model represents a clever and efficient baseline for psychographic profiling. The choice to use single sentences for the positive and negative poles of each trait has several implications:

*   **Efficiency**: It's fast and computationally inexpensive.
*   **Clarity**: The basis for each score is transparent and directly tied to the example sentences.

However, this is understood to be a starting point. As you noted, this is the "meat" of the operation and will be refined over time. Future work on the model could include:

*   **Expanding Example Sets**: Instead of a single sentence, each pole could be represented by the mean vector of multiple example sentences. This would create a more robust and nuanced understanding of the trait, making the scoring less sensitive to the specific phrasing of a single example.
*   **Fine-tuning**: With a sufficiently large and labeled dataset, the underlying Sentence Transformer model could be fine-tuned to better understand the specific nuances of the personality traits defined in this project.
*   **Exploring Other Architectures**: Investigating different model architectures or techniques might yield further improvements in scoring accuracy and depth.

The current focus is on completing the application's core functionality, which will then enable a more dedicated and iterative focus on improving this classification model.
