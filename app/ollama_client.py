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
