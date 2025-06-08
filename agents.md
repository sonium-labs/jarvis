# Jarvis Voice Assistant: Core Agent Principles

This document outlines the fundamental principles guiding the development of the Jarvis Voice Assistant. These principles aim to ensure a high-quality user experience, maintainability, and adherence to the project's vision.

## 1. Prioritize Local Functioning

*   **Objective**: Maximize offline capability and user privacy by processing data and commands locally wherever feasible.
*   **Rationale**:
    *   **Responsiveness**: Local processing significantly reduces latency compared to relying on cloud services.
    *   **Privacy**: Keeps user data (voice commands, personal information) on the user's device.
    *   **Reliability**: Ensures core functionality remains available even without an internet connection.
    *   **Cost**: Avoids potential costs associated with API calls to external services.
*   **Implementation**:
    *   Utilize local libraries for wake word detection (e.g., Porcupine), speech-to-text (e.g., Vosk), and text-to-speech (e.g., pyttsx3).
    *   Minimize reliance on external APIs for core command processing. External calls should be opt-in or for non-critical enhancements (like the current music bot integration, which is understood to be external).

## 2. Maintain a Small and Lightweight Footprint

*   **Objective**: Keep the application lean in terms of codebase size, dependencies, and resource consumption.
*   **Rationale**:
    *   **Performance**: Lighter applications generally start faster and run more smoothly, especially on less powerful hardware.
    *   **Maintainability**: A smaller, focused codebase is easier to understand, debug, and extend.
    *   **Portability**: Easier to package, distribute, and run across different environments.
    *   **Clarity**: Encourages clear, concise code and avoids unnecessary complexity.
*   **Implementation**:
    *   Carefully vet any new dependencies for their size and necessity.
    *   Prefer Python's standard library or small, efficient third-party libraries.
    *   Write modular and efficient code.
    *   Regularly review and refactor to remove dead code or overly complex solutions.

## 3. Ensure Low Latency and High Responsiveness

*   **Objective**: Provide an immediate and fluid user experience, which is paramount for a voice assistant.
*   **Rationale**:
    *   **User Experience**: Delays in response make a voice assistant feel clunky and frustrating.
    *   **Natural Interaction**: Mimicking human conversation requires quick feedback and processing.
*   **Implementation**:
    *   Optimize critical code paths, especially in audio processing, wake word detection, and transcription.
    *   Employ asynchronous operations (like the current TTS) where appropriate to prevent blocking the main loop.
    *   Continuously profile and monitor performance to identify and address bottlenecks.
    *   Design UI feedback (console or otherwise) to be immediate, even if the full processing takes a moment (e.g., partial transcription updates).
    *   Silence detection parameters should be tunable to balance responsiveness with capturing the user's full intent.
    *   Reuse HTTP connections when possible to minimize request latency, but allow disabling pooling if compatibility issues arise.

## 4. Modularity and Clarity

*   **Objective**: Structure the codebase in a clear, modular way.
*   **Rationale**:
    *   **Readability**: Makes it easier for anyone (including future you) to understand the code.
    *   **Testability**: Well-defined modules are easier to test in isolation.
    *   **Reusability**: Components can be reused or replaced more easily.
*   **Implementation**:
    *   Separate concerns into distinct modules (e.g., `wake_word.py`, `transcribe.py`, `console_ui.py`).
    *   Use clear naming conventions for variables, functions, and classes.
    *   Document code effectively, explaining the "why" as much as the "what."

---

These principles should serve as a guide for all development decisions. While trade-offs are sometimes necessary, deviations should be consciously evaluated against these core tenets.

## 5. Preserve Helpful Comments

*   **Objective**: Keep existing explanatory comments intact unless they become incorrect or misleading.
*   **Rationale**: Comments provide valuable context for future maintainers and help explain design choices.
*   **Implementation**:
    *   When modifying code, update related comments instead of deleting them.
    *   Only remove a comment if it is clearly obsolete or redundant.
