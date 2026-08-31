"""Nagrywa niedzielna transmisje mszy z YouTube i zapisuje samą transkrypcję.

Uzycie:
    python record_transcribe.py --config config.json

Wymaga zainstalowanego ffmpeg w PATH (yt-dlp uzywa go do wyciagniecia audio).
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


def download_audio(url: str, dest_stem: Path, wait_seconds: int) -> Path:
    """Pobiera (lub czeka na start i nagrywa) transmisje na zywo, zwraca sciezke do pliku mp3."""
    output_template = str(dest_stem) + ".%(ext)s"
    cmd = [
        "yt-dlp",
        url,
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "--live-from-start",
        "--wait-for-video", str(wait_seconds),
        "--no-part",
        "--newline",
        "-o", output_template,
    ]
    logger.info("Startuje yt-dlp: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)

    audio_path = dest_stem.with_suffix(".mp3")
    if not audio_path.exists():
        raise FileNotFoundError(f"yt-dlp nie utworzyl oczekiwanego pliku {audio_path}")
    return audio_path


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
    tmp_audio_stem = output_dir / f"_tmp_msza_{today}"
    text_path = output_dir / f"kazanie_{today}.txt"

    try:
        audio_path = download_audio(
            config["youtube_url"],
            tmp_audio_stem,
            int(config.get("wait_for_video_seconds", 1800)),
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Pobieranie transmisji nie powiodlo sie: %s", exc)
        return 1
    except FileNotFoundError as exc:
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
