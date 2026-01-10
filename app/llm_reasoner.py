from app.ollama_client import generate

def explain_findings(model_id: str, prompt: str) -> tuple[bool, str]:
    return generate(model_id, prompt, temperature=0.2)