# Albatross

Небольшая аркада про альбатроса: он стартует с горы, планирует над долиной и старается улететь
как можно дальше, расходуя ограниченный запас сил на взмахи крыльями.

## Установка готовых сборок

Готовые установочные файлы публикуются в
[GitHub Releases](https://github.com/PavlenkoEvgeniy/python-game-albatros/releases)
приватного репозитория:

| Платформа | Файл | Установка |
|---|---|---|
| Linux (Debian/Ubuntu) | `Albatross-<версия>-linux-amd64.deb` | `sudo apt install ./Albatross-*.deb` |
| Linux (Fedora/RHEL) | `Albatross-<версия>-linux-x86_64.rpm` | `sudo dnf install ./Albatross-*.rpm` |
| Windows | `Albatross-<версия>-windows-setup.exe` | запустить установщик |
| macOS | `Albatross-<версия>-macos.dmg` | открыть образ и перетащить `Albatross.app` в `Applications` |

Сборки не подписаны сертификатами Apple и Microsoft:

- Windows SmartScreen может показать предупреждение — «Подробнее» → «Выполнить в любом случае».
- macOS Gatekeeper: первый запуск через правый клик → «Открыть», либо
  `xattr -dr com.apple.quarantine /Applications/Albatross.app`.

## Запуск из исходников

Нужен Python 3.12+ и [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run albatross
```

Проверить версию без открытия окна:

```bash
uv run albatross --version
```

## Управление

| Клавиша | Действие |
|---|---|
| Пробел или левая кнопка мыши | Взмах крыльями; старт из меню; рестарт после проигрыша |
| Esc | Пауза и продолжение полёта |
| R | Рестарт на экране проигрыша |
| L | Переключение языка RU/EN |
| M | Включение и выключение звука |

## Механика

- Птица всегда движется вперёд и без взмахов постепенно снижается.
- Каждый взмах даёт импульс вверх и тратит часть полоски сил. Между взмахами есть короткая
  пауза, поэтому «зажать» кнопку и взлететь бесконечно нельзя.
- Силы не восстанавливаются: когда полоска пуста, остаётся только планировать вниз.
- Касание земли завершает забег. Счёт — горизонтальная дистанция в метрах от точки старта.
- Более сильные результаты подсвечиваются на экране проигрыша как новый рекорд.

## Рекорд

Лучший результат сохраняется в платформенном каталоге данных:

- Linux: `~/.local/share/albatross/record.json`;
- macOS: `~/Library/Application Support/albatross/record.json`;
- Windows: `%LOCALAPPDATA%\albatross\record.json`.

Файл пишется атомарно. Если он отсутствует или повреждён, игра запускается без рекорда, а
следующий завершённый забег записывает корректный файл.

## Язык и звук

- Интерфейс есть на русском и английском; `L` переключает язык во время игры, текущий забег
  не сбрасывается.
- Взмах и фоновый ветер генерируются процедурно, внешних аудиофайлов нет. `M` выключает звук.
  Если аудиоустройство недоступно, игра продолжает работать молча.

## Графика

Вся сцена — векторный минимализм, нарисованный кодом: градиентное небо, солнце, облака, три
слоя гор с параллаксом, земля, силуэт альбатроса с анимацией крыльев и следом взмаха. Внешних
изображений и шрифтов нет — используется встроенный шрифт pygame с кириллицей.

## Структура проекта

```
src/albatross/
  domain/          # чистая физика, состояния сессии, рекорд — без pygame
  application/     # игровой цикл, fixed timestep, ввод, связывание слоёв
  presentation/    # сцена, птица, HUD, локализация, процедурный звук
  infrastructure/  # чтение и атомарная запись record.json
tests/             # pytest + hypothesis; покрытие домена и хранилища 100%
packaging/
  icons/           # PNG/ICO/ICNS, сгенерированы из графики игры
  linux/           # deb/rpm, .desktop, иконка, spec
  windows/         # Inno Setup установщик
  macos/           # сборка .dmg
main.py            # точка входа для PyInstaller
openspec/          # спецификации и задачи OpenSpec
```

Домен не импортирует pygame: физика проверяется без окна и не зависит от FPS. Симуляция идёт
фиксированным шагом 1/120 с и работает в метрах и секундах; рендер переводит метры в пиксели.

## Разработка и проверки

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

`pytest` включает branch coverage для `albatross.domain` и `albatross.infrastructure` с порогом
100%. `ci.yml` прогоняет те же команды на Python 3.12, 3.13 и 3.14 с dummy-драйверами SDL.

## Сборка установщиков

`build.yml` собирает артефакты на Ubuntu, Windows и macOS. Локально на Linux можно проверить
основную часть:

```bash
uv run pyinstaller --onefile --windowed --noconfirm --clean \
  --name Albatross-linux \
  --collect-all pygame --copy-metadata albatross main.py
./dist/Albatross-linux --version
SKIP_RPM=1 bash packaging/linux/build_packages.sh 0.1.0 dist/Albatross-linux dist/installers
```

Без `SKIP_RPM=1` нужен `rpmbuild`; в CI он устанавливается вместе с `rpm`. Windows-установщик
собирается Inno Setup, macOS-образ — `packaging/macos/build_dmg.sh` на macOS.

Иконки генерируются из графики игры (нужен Pillow только на этапе генерации):

```bash
uv run --with pillow python packaging/make_icons.py
```

Релиз создаётся отправкой тега, совпадающего с версией в `pyproject.toml`:

```bash
git tag v0.1.0
git push origin v0.1.0
```

CI проверит тесты, соберёт deb/rpm, exe и dmg и прикрепит их к GitHub Release.

Проект следует спецификации OpenSpec; активный change — `add-albatross-game`.
