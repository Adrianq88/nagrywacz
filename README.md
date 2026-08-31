# Nagrywacz

Automatycznie nagrywa niedzielna transmisję mszy z YouTube i zapisuje
**samą transkrypcję** kazania (tekst) na Dysku Google — żeby po powrocie
z pracy plik po prostu tam był.

Stream z kościoła leci **24/7** (stała kamera, nie tylko podczas mszy),
więc nie da się "poczekać aż się zacznie" — trzeba po prostu zacząć
nagrywać o właściwej godzinie i nagrywać przez ustalony czas.

Całość działa na **darmowej maszynie w chmurze (Oracle Cloud Free Tier)**,
a nie na niczyim domowym komputerze — dzięki temu nikt nie musi pamiętać
o włączonym laptopie. Jedyny haczyk: YouTube blokuje pobieranie streamów
live z adresów IP dużych centrów danych ("Sign in to confirm you're not
a bot"), więc autoryzujemy się plikiem cookies z prawdziwego konta
Google (patrz krok 6 poniżej) — to w zupełności wystarcza, żeby ominąć
blokadę.

Jak to działa:

1. W niedzielę o 9:55 cron na serwerze uruchamia skrypt.
2. `yt-dlp` (z plikiem cookies) rozwiązuje aktualny adres strumienia, a
   `ffmpeg` nagrywa z niego audio (mp3) przez `record_duration_minutes`
   (domyślnie 95 min: 5 min zapasu przed mszą + 60 min mszy + 30 min
   zapasu, gdyby się przeciągnęła), po czym czysto kończy plik.
3. `faster-whisper` (offline, model rozpoznawania mowy) transkrybuje
   audio na polski tekst.
4. Plik `kazanie_RRRR-MM-DD.txt` trafia przez `rclone` na Dysk Google,
   do udostępnionego folderu widocznego dla Was obu z dowolnego miejsca
   (telefon, przeglądarka).
5. Plik audio jest domyślnie kasowany po transkrypcji.

## 1. Załóż darmową maszynę (Oracle Cloud Free Tier)

1. Wejdź na [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) i
   załóż konto (wymaga karty do weryfikacji tożsamości, ale w ramach
   "Always Free" nic nie zostanie pobrane, jeśli zostaniesz w limitach).
2. Utwórz instancję (Compute → Create instance):
   - Image: **Ubuntu 22.04** (lub nowszy LTS).
   - Shape: dowolny z oznaczeniem **"Always Free eligible"** (np.
     `VM.Standard.E2.1.Micro` albo `VM.Standard.A1.Flex` z 1 OCPU/6GB —
     jeśli dostępny w Twoim regionie, jest wyraźnie mocniejszy i lepszy
     do Whispera).
   - Zapisz wygenerowaną parę kluczy SSH (plik `.pem`) — będzie potrzebny
     do logowania.
3. W zakładce sieci instancji dodaj regułę **Ingress** pozwalającą na SSH
   (port 22) z Twojego IP (albo zostaw domyślną, jeśli już jest).
4. Połącz się:
   ```
   ssh -i sciezka/do/klucza.pem ubuntu@<PUBLIC_IP_INSTANCJI>
   ```

## 2. Zainstaluj zależności na serwerze

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg git
curl https://rclone.org/install.sh | sudo bash
```

## 3. Wgraj projekt

```bash
git clone <adres tego repozytorium> ~/nagrywacz
cd ~/nagrywacz
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## 4. Zainstaluj yt-dlp (najnowsza wersja bezpośrednio z GitHuba)

YouTube zmienia się często, więc lepiej mieć zawsze świeżą wersję niż tę
z `requirements.txt`:

```bash
venv/bin/pip install --upgrade --pre "yt-dlp[default]"
```

## 5. Skonfiguruj rclone (jednorazowo, wysyłka na Dysk Google)

Na serwerze bez przeglądarki (headless) `rclone config` i tak Cię
przeprowadzi przez logowanie — pokaże link, który otwierasz na **swoim**
komputerze/telefonie, logujesz się na dowolne konto Google i wklejasz
z powrotem kod:

```bash
rclone config
```

Wybierz kolejno: `n` (new remote) → nazwa `gdrive` → typ `drive` (Google
Drive) → zostaw client_id/client_secret puste → scope `1` (full access)
→ resztę Enterem → `n` (nie edytować zaawansowanych ustawień) → `y`
(autoryzacja przez przeglądarkę — pokaże link i poprosi o kod) → `n`
(to nie dysk współdzielony organizacji).

Na koniec utwórz w Drive folder na wyniki i sprawdź, że rclone go widzi:

```bash
rclone mkdir gdrive:Kazania
rclone lsd gdrive:
```

Potem na [drive.google.com](https://drive.google.com) znajdź folder
`Kazania`, kliknij prawym → **Udostępnij** → dodaj adresy e-mail Twój i
taty, żeby oboje mieli podgląd z telefonu/przeglądarki niezależnie od
tego, na czyje konto poszło rclone.

## 6. Wyeksportuj plik cookies z YouTube (jednorazowo, omija blokadę bota)

1. W przeglądarce (na swoim komputerze) zainstaluj rozszerzenie **"Get
   cookies.txt LOCALLY"** (Chrome/Firefox) i zaloguj się na dowolne
   konto Google na youtube.com.
2. Wejdź na sam link do streamu (ten z `config.json`), kliknij ikonę
   rozszerzenia i wyeksportuj `cookies.txt` (format Netscape).
3. Wyślij plik na serwer:
   ```bash
   scp -i sciezka/do/klucza.pem cookies.txt ubuntu@<PUBLIC_IP>:~/nagrywacz/cookies.txt
   ```

Cookies z czasem wygasają (zwykle po tygodniach/miesiącach) — jeśli
niedzielne uruchomienie zacznie kończyć się błędem o blokadzie bota,
wystarczy powtórzyć ten krok ze świeżym eksportem.

## 7. Konfiguracja

```bash
cp config.example.json config.json
nano config.json
```

```json
{
  "youtube_url": "https://www.youtube.com/live/NluaCVnEV7I",
  "output_dir": "/home/ubuntu/nagrywacz/output",
  "cookies_file": "/home/ubuntu/nagrywacz/cookies.txt",
  "rclone_remote": "gdrive:Kazania",
  "whisper_model": "small",
  "language": "pl",
  "keep_audio": false,
  "record_duration_minutes": 95
}
```

- `output_dir`: lokalny folder roboczy na serwerze (audio tymczasowo, plus
  kopia tekstu przed wysyłką) — nie musi być nigdzie synchronizowany,
  rclone i tak wyśle sam tekst na Dysk Google.
- `whisper_model`: `small` jest szybki i wystarczająco dokładny; jeśli
  jakość tekstu będzie za słaba, zmień na `medium` (wolniejsze — na
  słabszym Free Tier shape'ie może być zauważalnie dłużej).
- `record_duration_minutes`: jak długo nagrywać licząc od momentu
  uruchomienia (9:55). Zwiększ, jeśli msza regularnie się przeciąga.

## 8. Test ręczny

Stream leci 24/7, więc test zadziała o dowolnej porze (nie trzeba czekać
na niedzielę) — treść transkrypcji będzie bez sensu poza mszą, ale
sprawdzisz cały pipeline technicznie:

```bash
venv/bin/python src/record_transcribe.py --config config.json
```

Sprawdź `logs/` oraz czy plik pojawił się w `rclone lsf gdrive:Kazania`.

## 9. Harmonogram (cron)

```bash
bash scripts/install_cron.sh
```

Zarejestruje wpis crona na **niedzielę 9:55**. Sprawdź strefę czasową
serwera (`timedatectl`) — jeśli chodzi na UTC, a nie na czas polski,
popraw godzinę w crontabie (`crontab -e`) o odpowiednie przesunięcie
(np. latem Polska to UTC+2, czyli 9:55 czasu polskiego = wpis `55 7`).

Żeby usunąć zadanie: `bash scripts/uninstall_cron.sh`.

## Uwagi

- Zero zależności od czyjegokolwiek domowego komputera — serwer działa
  cały czas, niezależnie od tego, czy laptop taty jest włączony.
- Wszystkie logi lądują w `logs/log_RRRR-MM-DD_HHMM.txt` oraz zbiorczo w
  `logs/cron.log` — przydatne do diagnozowania, gdyby coś nie zadziałało.
- Jeśli po jakimś czasie pojawi się błąd "Sign in to confirm you're not a
  bot" mimo pliku cookies, to znak że cookies wygasły — powtórz krok 6.
- yt-dlp zmienia się często wraz z YouTube — jeśli nagrywanie przestanie
  działać bez oczywistego powodu, spróbuj najpierw zaktualizować:
  `venv/bin/pip install --upgrade --pre "yt-dlp[default]"`.
