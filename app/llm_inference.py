import requests

OLLAMA_BASE_URL = "http://localhost:11434"


def run_inference(
    model_id: str,
    prompt: str,
    timeout: float = 60.0,
) -> tuple[bool, str]:
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model_id,
                "prompt": prompt,
                "stream": False,
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
        return False, f"Failed to run inference: {exc}"
