"""Nagrywa niedzielna transmisje mszy z YouTube (stream 24/7) i zapisuje
samą transkrypcję.

Uzycie:
    python record_transcribe.py --config config.json

Zrodlowy stream leci non-stop, wiec skrypt nie czeka az sie "zacznie" -
po prostu rozwiazuje aktualny adres strumienia i nagrywa go przez ustalony
czas (record_duration_minutes w konfiguracji), zaczynajac dokladnie w
momencie uruchomienia (patrz Harmonogram zadan / scripts/install_task.ps1).

Wymaga yt-dlp oraz ffmpeg w PATH.
"""

import argparse
import datetime
import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("nagrywacz")


def load_config(config_path: Path) -> dict:
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    for key in ("youtube_url", "output_dir"):
        if not config.get(key):
            raise ValueError(f"Brak wymaganego pola '{key}' w pliku konfiguracyjnym")
    return config


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    log_file = log_dir / f"log_{timestamp}.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )


def resolve_stream_url(url: str) -> str:
    """Rozwiazuje biezacy adres strumienia audio dla transmisji na zywo."""
    cmd = ["yt-dlp", "-f", "bestaudio/best", "--get-url", url]
    logger.info("Rozwiazuje adres strumienia: %s", " ".join(cmd))
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    stream_url = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    if not stream_url:
        raise RuntimeError("yt-dlp nie zwrocil adresu strumienia (transmisja offline?)")
    return stream_url


def record_audio(url: str, dest_path: Path, duration_seconds: int) -> Path:
    """Nagrywa fragment strumienia na zywo o zadanej dlugosci, zwraca sciezke do pliku mp3."""
    stream_url = resolve_stream_url(url)
    cmd = [
        "ffmpeg", "-y",
        "-i", stream_url,
        "-t", str(duration_seconds),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "5",
        str(dest_path),
    ]
    logger.info("Nagrywam %d s audio ze strumienia...", duration_seconds)
    subprocess.run(cmd, check=True)

    if not dest_path.exists():
        raise FileNotFoundError(f"ffmpeg nie utworzyl oczekiwanego pliku {dest_path}")
    return dest_path


def transcribe(audio_path: Path, language: str, model_size: str) -> str:
    from faster_whisper import WhisperModel

    logger.info("Ladowanie modelu Whisper '%s' (CPU, int8)...", model_size)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    logger.info("Transkrybuje %s...", audio_path.name)
    segments, info = model.transcribe(str(audio_path), language=language, beam_size=5, vad_filter=True)
    logger.info("Wykryty jezyk: %s (pewnosc %.2f)", info.language, info.language_probability)

    lines = [segment.text.strip() for segment in segments if segment.text.strip()]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.json", help="Sciezka do pliku konfiguracyjnego JSON")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path

    setup_logging(project_root / "logs")

    try:
        config = load_config(config_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Nie udalo sie wczytac konfiguracji %s: %s", config_path, exc)
        return 1

    output_dir = Path(config["output_dir"])
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error("Folder docelowy %s jest niedostepny (Dysk Google niezalogowany/niezamontowany?): %s", output_dir, exc)
        return 1

    today = datetime.date.today().isoformat()
    tmp_audio_path = output_dir / f"_tmp_msza_{today}.mp3"
    text_path = output_dir / f"kazanie_{today}.txt"
    duration_seconds = int(config.get("record_duration_minutes", 95)) * 60

    try:
        audio_path = record_audio(config["youtube_url"], tmp_audio_path, duration_seconds)
    except subprocess.CalledProcessError as exc:
        logger.error("Nagrywanie transmisji nie powiodlo sie: %s", exc)
        return 1
    except (FileNotFoundError, RuntimeError) as exc:
        logger.error(str(exc))
        return 1

    try:
        text = transcribe(audio_path, config.get("language", "pl"), config.get("whisper_model", "small"))
    except Exception:
        logger.exception("Transkrypcja nie powiodla sie")
        return 1

    header = f"Kazanie z {today}\nZrodlo: {config['youtube_url']}\n\n"
    text_path.write_text(header + text, encoding="utf-8")
    logger.info("Zapisano transkrypcje: %s", text_path)

    if not config.get("keep_audio", False):
        audio_path.unlink(missing_ok=True)
        logger.info("Usunieto plik audio %s", audio_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
