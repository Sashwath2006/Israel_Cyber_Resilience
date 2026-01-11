import requests

OLLAMA_BASE_URL = "http://localhost:11434"


def is_ollama_available(timeout: float = 1.0) -> bool:
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=timeout,
        )
        return response.status_code == 200
    except Exception:
        return False


def pull_model(model_id: str) -> tuple[bool, str]:
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"name": model_id},
            stream=True,
            timeout=5,
        )

        if response.status_code != 200:
            return False, f"Ollama error: {response.text}"

        # Consume streaming response fully
        for _ in response.iter_lines():
            pass

        return True, "Model download completed successfully."

    except Exception as exc:
        return False, f"Failed to connect to Ollama: {exc}"


def generate(
    model_id: str,
    prompt: str,
    temperature: float = 0.2,
    timeout: float = 60.0,
) -> tuple[bool, str]:
    """
    Generate LLM response with controlled temperature for deterministic reasoning.
    
    Args:
        model_id: Ollama model identifier
        prompt: Input prompt for the model
        temperature: Sampling temperature (default 0.2 for low randomness)
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (success: bool, response: str)
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model_id,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": max(0.0, min(1.0, temperature)),  # Clamp to [0.0, 1.0]
                },
            },
            timeout=timeout,
        )

        if response.status_code != 200:
            return False, f"Ollama error: {response.text}"

        data = response.json()
        output = data.get("response", "").strip()

        if not output:
            return False, "Model returned an empty response."

        return True, output

    except requests.Timeout:
        return False, "Inference request timed out."

    except Exception as exc:
        return False, f"Failed to generate response: {exc}"