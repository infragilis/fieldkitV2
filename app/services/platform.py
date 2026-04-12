from pathlib import Path


class PlatformService:
    """Detect Raspberry Pi family capabilities so UI and backend can adapt by model."""

    def detect(self) -> dict:
        model_text = self._read_model()
        generation = self._infer_generation(model_text)
        wifi_supported = generation is not None and generation >= 3
        return {
            "model": model_text,
            "generation": generation,
            "wifi_supported": wifi_supported,
            "serial_profiles_supported": 2,
            "notes": self._notes(generation, wifi_supported),
        }

    def _read_model(self) -> str:
        model_file = Path("/sys/firmware/devicetree/base/model")
        if model_file.exists():
            return model_file.read_text(errors="ignore").replace("\x00", "").strip()
        cpuinfo = Path("/proc/cpuinfo")
        if cpuinfo.exists():
            for line in cpuinfo.read_text(errors="ignore").splitlines():
                if line.startswith("Model"):
                    return line.split(":", 1)[1].strip()
        return "Unknown platform"

    def _infer_generation(self, model_text: str) -> int | None:
        for generation in (5, 4, 3, 2, 1):
            if f"Pi {generation}" in model_text or f"Model {generation}" in model_text:
                return generation
        return None

    def _notes(self, generation: int | None, wifi_supported: bool) -> list[str]:
        notes = []
        if generation is None:
            notes.append("Pi generation could not be detected; defaulting to conservative capability assumptions.")
        if wifi_supported:
            notes.append("Wi-Fi client/AP features can be enabled on Pi 3 and newer models.")
        else:
            notes.append("Wi-Fi features should remain disabled on Pi models older than Pi 3 unless a USB adapter is added.")
        return notes
