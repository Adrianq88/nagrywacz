# Nagrywacz

Automatycznie nagrywa niedzielna transmisje mszy z YouTube i zapisuje **samą
transkrypcję** kazania (tekst) do folderu zsynchronizowanego z Dyskiem
Google — żeby po powrocie z pracy plik po prostu tam był.

Stream z kościoła leci **24/7** (kamera w kościele, nie tylko podczas mszy),
więc nie da się "poczekać aż się zacznie" — trzeba po prostu zacząć
nagrywać o właściwej godzinie i nagrywać przez ustalony czas.

Jak to działa:

1. W niedzielę o 9:55 Harmonogram zadań Windows uruchamia skrypt.
2. `yt-dlp` rozwiązuje aktualny adres strumienia, a `ffmpeg` nagrywa z niego
   audio (mp3) przez `record_duration_minutes` (domyślnie 95 min: 5 min
   zapasu przed mszą + 60 min mszy + 30 min zapasu, gdyby się przeciągnęła),
   po czym czysto kończy plik.
3. `faster-whisper` (offline, model rozpoznawania mowy) transkrybuje audio
   na polski tekst.
4. Wynik trafia jako `kazanie_RRRR-MM-DD.txt` do folderu na Dysku Google.
   Plik audio jest domyślnie kasowany po transkrypcji.

## Instalacja na laptopie taty (Windows)

1. **Python** — zainstaluj Python 3.11+ z [python.org](https://www.python.org/downloads/),
   zaznacz "Add python.exe to PATH".

2. **ffmpeg** — potrzebny do wyciągania audio. Najprościej przez
   [winget](https://learn.microsoft.com/pl-pl/windows/package-manager/winget/):
   ```
   winget install Gyan.FFmpeg
   ```
   (po instalacji zrestartuj terminal/laptop, żeby PATH się odświeżył).

3. **Dysk Google (Google Drive for desktop)** — konto logowania nie ma
   znaczenia (może być Twoje, taty albo dowolne inne), bo i tak folder
   udostępnimy dalej. Zależy nam, żeby tata miał **zwykły folder na
   Pulpicie**, więc korzystamy z funkcji "kopia zapasowa folderu z
   komputera" (Backup and sync), a nie z mountowania `G:\`:
   1. Zainstaluj z [google.com/drive/download](https://www.google.com/drive/download/)
      i zaloguj na wybrane konto Google.
   2. Utwórz zwykły folder na Pulpicie taty: `C:\Users\<nazwa_uzytkownika>\Desktop\Kazania`.
   3. W ustawieniach apki Dysk Google → **Foldery z tego komputera** → dodaj
      ten folder (`Kazania`) do kopii zapasowej, tryb synchronizacji: **Mirror
      files** (nie "Stream") — dzięki temu pliki fizycznie leżą na dysku
      laptopa (widoczne od razu, nawet offline) i jednocześnie wysyłają się
      do chmury w tle.
   4. Na [drive.google.com](https://drive.google.com) odszukaj ten folder
      (pojawi się pod "Computers" → nazwa laptopa → Kazania), kliknij prawym
      → **Udostępnij** → dodaj adres e-mail Twój i/lub taty (jeśli to inne
      konto niż zalogowane). Dzięki temu oboje macie podgląd z telefonu/
      przeglądarki, niezależnie na czyje konto poszła kopia zapasowa.

   Tata i tak nigdy nie musi wchodzić na drive.google.com — dla niego to po
   prostu folder `Kazania` na Pulpicie.

4. **Ten projekt** — skopiuj folder `nagrywacz` na laptopa, np. do
   `C:\Nagrywacz`.

5. **Środowisko Python** — w PowerShell, w folderze projektu:
   ```
   python -m venv venv
   venv\Scripts\pip install -r requirements.txt
   ```

6. **Konfiguracja** — skopiuj `config.example.json` do `config.json` i
   uzupełnij:
   ```json
   {
     "youtube_url": "https://www.youtube.com/live/NluaCVnEV7I",
     "output_dir": "C:\\Users\\<nazwa_uzytkownika>\\Desktop\\Kazania",
     "whisper_model": "small",
     "language": "pl",
     "keep_audio": false,
     "record_duration_minutes": 95
   }
   ```
   Link do stałego streamu kościoła jest już wpisany domyślnie — trzeba
   tylko poprawić `<nazwa_uzytkownika>` w `output_dir` na faktyczną nazwę
   konta Windows taty (ten sam folder co w kroku 3, żeby pliki od razu
   wpadały pod kopię zapasową).
   - `whisper_model`: `small` jest szybki i wystarczająco dokładny na
     zwykłym CPU; jeśli jakość tekstu będzie za słaba, zmień na `medium`
     (wolniejsze, dokładniejsze).
   - `record_duration_minutes`: jak długo nagrywać licząc od momentu
     uruchomienia zadania (9:55). Zwiększ, jeśli msza regularnie się
     przeciąga.

7. **Test ręczny** (najlepiej na już zakończonej/aktualnie trwającej
   transmisji, żeby sprawdzić, czy wszystko działa):
   ```
   venv\Scripts\python.exe src\record_transcribe.py --config config.json
   ```
   Sprawdź plik w `logs\` oraz wynikowy `.txt` w folderze `Kazania` na
   Pulpicie (a po chwili też na drive.google.com — apka synchronizuje w
   tle).

8. **Harmonogram** — w PowerShell **jako Administrator**:
   ```
   powershell -ExecutionPolicy Bypass -File scripts\install_task.ps1
   ```
   Utworzy to zadanie "NagrywaczMszy" uruchamiane co niedzielę o 9:55.

9. **Ustawienia zasilania** — żeby laptop faktycznie odpalił zadanie:
   - Panel sterowania → Opcje zasilania → Zmień ustawienia planu →
     Zaawansowane ustawienia zasilania → Sen → **Zezwalaj na czasomierze
     pobudki: Włącz**.
   - Laptop powinien być podłączony do zasilania i **nie** całkowicie
     wyłączony (może być uśpiony) w niedzielę przed 9:55.

Żeby usunąć zadanie: `powershell -ExecutionPolicy Bypass -File scripts\uninstall_task.ps1`
(jako Administrator).

## Uwagi

- Stream jest stały 24/7, więc `record_duration_minutes` decyduje o tym,
  ile realnie nagrywamy — jeśli msza regularnie się przeciąga, zwiększ tę
  wartość w `config.json`.
- Wszystkie logi z każdego uruchomienia lądują w `logs\log_RRRR-MM-DD_HHMM.txt`
  — przydatne do diagnozowania, gdyby coś nie zadziałało.
- Do testu ręcznego (krok 7) nie trzeba czekać na niedzielę — skrypt zawsze
  nagrywa to, co aktualnie leci na streamie, więc zadziała o każdej porze
  (nawet gdy w kościele ciemno i cicho — dobre do sprawdzenia, że cały
  pipeline działa techniczne, choć transkrypcja wyjdzie wtedy pusta/losowa).
