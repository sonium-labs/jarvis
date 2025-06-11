# Jarvis: Core Technical Directives

System architecture and modifications adhere to the following directives to ensure performance, maintainability, and user privacy.

## 1. Local Processing Prioritization

*   **Directive**: Maximize local data processing for core functions; minimize external API reliance.
*   **Key Mechanisms**:
    *   Wake Word: Local (Porcupine).
    *   Speech-to-Text (STT): Local (Vosk).
    *   Text-to-Speech (TTS): Local (pyttsx3).
    *   External APIs: Restricted to non-critical, opt-in features (e.g., music bot integration).
    *   Benefit: Reduced latency, enhanced privacy, offline capability.

## 2. Resource Efficiency

*   **Directive**: Maintain minimal codebase size, dependency count, and resource (CPU/memory) footprint.
*   **Key Mechanisms**:
    *   Dependencies: Scrutinize for necessity and size. Favor standard library or small, performant alternatives.
    *   Code: Implement modular, efficient algorithms. Conduct regular reviews and refactoring to eliminate redundancy and dead code.
    *   Benefit: Improved startup, runtime performance, and maintainability.

## 3. High Responsiveness & Low Latency

*   **Directive**: Ensure immediate system feedback and rapid command execution.
*   **Key Mechanisms**:
    *   Critical Paths: Optimize audio processing, wake word, and transcription pipelines.
    *   Asynchronous Operations: Utilize for non-blocking tasks (e.g., TTS via `AsyncTTS` class).
    *   Performance Monitoring: Profile and address bottlenecks proactively.
    *   UI Feedback: Provide immediate console updates (e.g., partial transcription).
    *   Tunable Parameters: Expose settings like silence detection (RMS threshold, duration) for user optimization.
    *   HTTP Connections: Employ `requests.Session` for connection pooling to reduce API call latency for external services; allow disabling via `USE_HTTP_SESSION` env var for debugging.
    *   Benefit: Fluid user interaction.

## 4. Codebase Modularity & Clarity

*   **Directive**: Structure code into distinct, well-defined, and documented modules.
*   **Key Mechanisms**:
    *   Module Separation: Isolate concerns (e.g., `wake_word.py`, `transcribe.py`, `console_ui.py`, `jarvis.py` for orchestration).
    *   Naming Conventions: Adhere to clear, consistent naming for all code elements.
    *   Documentation: Maintain concise, functional comments explaining purpose and design, especially for public APIs and complex logic.
    *   Benefit: Enhanced readability, testability, and reusability.

## 5. Comment Preservation & Accuracy

*   **Directive**: Maintain relevant code comments; update or remove only if obsolete or incorrect.
*   **Key Mechanisms**:
    *   Review: During code modification, assess and update associated comments.
    *   Accuracy: Ensure comments reflect current code functionality.
    *   Benefit: Preserves design rationale and context for future development.

## 6. Git Commit Message Standards

*   **Directive**: Write clear, concise, and factual commit messages that describe the change and its outcome.
*   **Format**:
    *   **Subject Line**:
        *   Use imperative mood (e.g., "Add feature X," not "Added feature X" or "Adds feature X").
        *   Start with a capital letter.
        *   Do not end with a period.
        *   Keep concise (aim for 50 characters or less if possible, max 72).
        *   Summarize the change directly: state *what* was done.
    *   **Body (Optional)**:
        *   Use if the subject line is insufficient to explain the change.
        *   Separate from subject with a blank line.
        *   Explain *what* was changed and *why* (the problem solved or goal achieved).
        *   Describe the *result* or impact of the change.
        *   Wrap lines at 72 characters.
*   **Content Guidelines**:
    *   **Be Specific**: Clearly state the modification (e.g., "Refactor `user_auth` module to use class-based views" instead of "Improved auth").
    *   **State Outcome**: Describe the functional result (e.g., "Fix bug in `calculate_total` preventing negative inputs" leading to "`calculate_total` now handles negative inputs by returning zero").
    *   **No Fluff**: Avoid subjective terms, buzzwords (e.g., "optimized," "enhanced," "refactored nicely"), or personal opinions.
    *   **Factual & Objective**: Stick to what the code change does.
*   **Example (Good)**:
    ```
    Add rate limiting to `/api/login` endpoint

    Implemented token bucket algorithm for rate limiting on the
    `/api/login` route. This prevents brute-force attacks by
    restricting login attempts to 5 per minute per IP address.

    Result: Increased security for user authentication.
    ```
*   **Example (Needs Improvement)**:
    ```
    Fixed stuff

    lots of changes to make it better
    ```

---

These directives guide development. Deviations require explicit justification against these standards.
