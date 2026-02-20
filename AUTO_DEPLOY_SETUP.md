# 🚀 Инструкция: Как настроить автоматическую заливку

Чтобы все работало по одной кнопке, нужно сделать эту настройку **один раз**.

## Шаг 1: Подключить GitHub (Локально)

1.  Создайте новый **Пустой репозиторий** на [github.com](https://github.com/new).
    - Назовите его `hh-scraper-cloud`.
    - Не ставьте галочки "Add README", "Add .gitignore".
2.  Откройте консоль в папке проекта (`hh-scraper-cloud`):
    ```bash
    git init
    git add .
    git commit -m "First commit"
    git branch -M main
    git remote add origin https://github.com/ВАШ_ЛОГИН/hh-scraper-cloud.git
    git push -u origin main
    ```

Теперь файл `deploy_to_git.bat` будет работать! Просто запускайте его, чтобы отправить изменения на GitHub.

## Шаг 2: Подключить GitHub (На сервере)

1.  Зайдите на сервер через Консоль в браузере.
2.  Скопируйте репозиторий (если еще не сделали):
    ```bash
    git clone https://github.com/ВАШ_ЛОГИН/hh-scraper-cloud.git
    ```
    *(Вам придется ввести логин и Personal Access Token вместо пароля, так как GitHub отключил вход по паролю).*

3.  Перейдите в папку:
    ```bash
    cd hh-scraper-cloud
    ```

## Шаг 3: Настроить `deploy_to_server.bat` (На компьютере)

1.  Откройте файл `deploy_to_server.bat` в Блокноте.
2.  Замените `HOST=85.239.34.67` на ваш IP (если он другой).
3.  Замените `REPO_DIR=/root/hh-scraper-cloud` на путь к папке на сервере (обычно `/root/hh-scraper-cloud`).
4.  Сохраните.

Теперь при запуске `deploy_to_server.bat` у вас спросят пароль от сервера, и он сам обновит код и перезапустит бота!

---

## ⚡️ Как теперь работать?

1.  Что-то поменяли в коде на компьютере.
2.  Нажали **`deploy_to_git.bat`** -> Код улетел на GitHub.
3.  Нажали **`deploy_to_server.bat`** -> Сервер скачал код и перезапустил бота.

Всё!
