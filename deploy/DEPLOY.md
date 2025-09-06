# Wdrożenie jako usługa `systemd`

Instrukcja uruchomienia aplikacji jako usługi.

## 1) Plik usługi

```bash
sudo cp deploy/ice-db-api.service /etc/systemd/system/ice-db-api.service
sudo systemctl daemon-reload
```

## 2) Zmienne środowiskowe

Aplikacja czyta `.env` w katalogu projektu. Przykład w `.env.example`.

## 3) Uruchomienie / logi

```bash
sudo systemctl enable ice-db-api
sudo systemctl start ice-db-api
sudo systemctl status ice-db-api
journalctl -u ice-db-api -f
```
