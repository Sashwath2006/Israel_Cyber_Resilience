def get_model_registry() -> list[dict]:
    return [
        {
            "name": "LLaMA 3 8B",
            "ollama_id": "llama3:8b",
            "parameter_size": "8B",
            "approx_ram_gb": 8.0,
            "gpu_recommended": False,
            "description": "Balanced general-purpose model suitable for CPU inference.",
        },
        {
            "name": "LLaMA 3 13B",
            "ollama_id": "llama3:13b",
            "parameter_size": "13B",
            "approx_ram_gb": 16.0,
            "gpu_recommended": True,
            "description": "Higher-quality reasoning; benefits from GPU acceleration.",
        },
        {
            "name": "Mistral 7B",
            "ollama_id": "mistral:7b",
            "parameter_size": "7B",
            "approx_ram_gb": 8.0,
            "gpu_recommended": False,
            "description": "Fast and efficient; good for analysis tasks.",
        },
    ]


def assess_model_compatibility(model: dict, hardware: dict) -> list[str]:
    notes: list[str] = []

    total_ram = hardware["ram"]["total_gb"]
    gpu_available = hardware["gpu"]["available"]

    if total_ram < model["approx_ram_gb"]:
        notes.append(
            "System RAM may be insufficient; performance issues or crashes are possible."
        )

    if model["gpu_recommended"] and not gpu_available:
        notes.append(
            "This model typically benefits from a GPU; CPU-only execution may be slow."
        )

    return notes
