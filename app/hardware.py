import platform
import psutil
import subprocess


def detect_hardware() -> dict:
    cpu_info = {
        "model": platform.processor() or "Unknown",
        "cores": psutil.cpu_count(logical=False) or 0,
        "threads": psutil.cpu_count(logical=True) or 0,
    }

    ram_info = {
        "total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2)
    }

    gpu_info = {
        "available": False,
        "vendor": None,
        "model": None,
        "vram_gb": None,
    }

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            name, memory = result.stdout.strip().split(",")
            gpu_info.update(
                {
                    "available": True,
                    "vendor": "NVIDIA",
                    "model": name.strip(),
                    "vram_gb": round(float(memory.replace("MiB", "").strip()) / 1024, 2),
                }
            )
    except Exception:
        pass  # GPU is optional and non-fatal

    return {
        "cpu": cpu_info,
        "ram": ram_info,
        "gpu": gpu_info,
    }
