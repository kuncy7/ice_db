---

# Instrukcja Wdrożenia jako Usługa Systemd

Ten przewodnik opisuje, jak uruchomić aplikację jako stałą usługę systemową (`systemd`) w środowisku Ubuntu.

## Krok 1: Przygotuj plik usługi

1.  Otwórz plik `deploy/lodowisko-api.service` w edytorze tekstu.
2.  Znajdź sekcję `[Service]` i zastąp placeholdery `<USER>` oraz `<PROJECT_PATH>` swoimi faktycznymi wartościami.

    *   **`<USER>`**: Nazwa użytkownika, na którego koncie działa aplikacja (np. `ice`).
    *   **`<PROJECT_PATH>`**: Pełna, absolutna ścieżka do głównego katalogu aplikacji (np. `/home/ice/git/lodowisko-api`).

## Krok 2: Skopiuj i aktywuj usługę

1.  **Skopiuj** przygotowany plik do systemowego katalogu `systemd`:
    ```bash
    sudo cp deploy/lodowisko-api.service /etc/systemd/system/
    ```

2.  **Przeładuj** demona `systemd`, aby wczytał nową konfigurację:
    ```bash
    sudo systemctl daemon-reload
    ```

3.  **Włącz** usługę, aby startowała automatycznie przy każdym restarcie serwera:
    ```bash
    sudo systemctl enable lodowisko-api.service
    ```

4.  **Uruchom** usługę:
    ```bash
    sudo systemctl start lodowisko-api.service
    ```

## Krok 3: Weryfikacja

Aby sprawdzić, czy usługa działa poprawnie, użyj polecenia:
```bash
sudo systemctl status lodowisko-api.service
```
Powinieneś zobaczyć zielony status `active (running)`.

## Przydatne Komendy

*   **Restart usługi** (np. po aktualizacji kodu z Gita):
    ```bash
    sudo systemctl restart lodowisko-api
    ```

*   **Zatrzymanie usługi:**
    ```bash
    sudo systemctl stop lodowisko-api
    ```

*   **Podgląd logów na żywo:**
    ```bash
    sudo journalctl -u lodowisko-api -f
    ```
