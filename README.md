# Ableton Agent Kit

**Скилл и локальные инструменты для агента, который работает со звуком в Ableton Live.**

Проект вырос из практической работы над вокалом: потерянные сэмплы, незаметно выключенные эффекты, неудачные хвосты эха, сломанные `.als`, лишние запросы параметров. Здесь эти уроки превращены в проверяемые команды и короткие инструкции.

Это не кнопка «идеальный хит». Набор помогает агенту собрать факты, сделать осмысленные изменения и проверить результат. Музыкальный вкус, слышимость слов и одобрение исполнителя остаются частью работы.

## Что входит

| Часть | Возможности |
|---|---|
| `skills/ableton-mix` | Скилл Codex с отдельными справочниками по вокалу, эффектам, проектам и проверке |
| `ableton-agent` | CLI: `.als`, аудио, графики, громкость, стерео, паузы, сетка, ноты, ASR, эхо, релиз |
| `ableton-agent-mcp` | Семь инструментов stdio MCP; запись параметров включается отдельно |
| LiveMCP extension | Компактный обзор, параметры и клипы с пагинацией, группы/возвраты, пакетные правки |
| Windows capture | Захват звука выбранного процесса и его дочерних процессов без смены драйвера |
| Tests + CI | Синтетические сигналы, искусственные XML, имитация TCP и Live API; никаких записей пользователя |

Сравнение вариантов **Ableton MCP / LiveMCP**, включая реализацию с `abletonmcp.com`: [исследование серверов](docs/backend-comparison.md). Существующие скиллы, лицензии, форумы и исследования восприятия: [что взяли и улучшили](docs/research.md). Скилл выбирает инструменты по реальным возможностям подключённого сервера.

Для работы с внешними эффектами добавлены [бесплатные VST3 и инструкции агенту](docs/free-plugins.md), а также отдельный проверочный хост: `pip install -e ".[plugins]"`, затем `ableton-agent plugin-probe "Plugin.vst3" --out local/plugin.json`. Он читает параметры и проверяет обработку синтетического сигнала, не запуская воспроизведение.

## Быстрый старт

Python 3.11 или новее. Для основной работы рекомендуются 3.11–3.13. Сам Ableton и установленный LiveMCP нужны только для управления Live, а не для анализа файлов.

```powershell
git clone https://github.com/rub1kub/ableton-agent-kit.git
cd ableton-agent-kit
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev,mp3,plot,mcp,windows]"
.venv/Scripts/python scripts/install_skill.py
.venv/Scripts/ableton-agent doctor
```

На macOS/Linux замените `.venv/Scripts/` на `.venv/bin/` и исключите `windows`. Захват процесса Windows недоступен на этих системах; используйте экспорт Ableton. Для анализа нот установите `.[pitch]`, для локального распознавания — `.[asr]`. Модель ASR загружается отдельно пользователем: команда принимает существующий каталог и не скачивает модель сама.

Скилл устанавливается в `$CODEX_HOME/skills/ableton-mix` или `~/.codex/skills/ableton-mix`. После обновления списка скиллов вызывайте **`$ableton-mix`**. Установщик не заменяет уже существующий скилл. Его локальный `runtime.json` указывает на выбранный Python; не перемещайте виртуальное окружение без повторной настройки.

## Несколько рабочих команд

В примерах ниже виртуальное окружение уже активировано. Без активации используйте `.venv/Scripts/ableton-agent` (Windows) или `.venv/bin/ableton-agent` (macOS/Linux).

```powershell
ableton-agent als-audit "Song.als" --out reports/set.json
ableton-agent audio-analyze "beat.wav" --bpm 154 --out reports/beat.json
ableton-agent audio-plot "mix.wav" reports/overview.png
ableton-agent audio-compare "approved.wav" "candidate.wav"
ableton-agent ab-pack "approved.wav" "candidate.wav" local/ab --start 12 --duration 8
ableton-agent masking-proxy "vocal.wav" "beat.wav" --aligned --out reports/competition.json
ableton-agent live-snapshot --limit 16 --out reports/live.json
ableton-agent echo-plan --word-end 24.1 --word-duration 0.32 --next-phrase 24.9 --bpm 154
ableton-agent pitch "vocal.wav" --start 12 --end 20 --out reports/pitch.json
ableton-agent key "beat.wav" --start 12 --end 24 --out reports/key.json
```

Команды не делают автоматический мастеринг, не нормализуют аудио и не переписывают исходники. `--out` сохраняет подробный JSON локально и возвращает короткий итог. Результаты анализа тональности — гипотезы, а не доказанный гармонический разбор.

`live-snapshot`, остальные прямые `live-*` команды и `doctor --live` предназначены для старого LiveMCP. Для wstierhout Ableton MCP используйте его собственные инструменты и `ableton-live-mcp doctor`; протоколы не взаимозаменяемы.

## Подключение MCP и расширения LiveMCP

Пример настройки stdio-сервера и процедура установки расширения находятся в [docs/setup.md](docs/setup.md). Расширение добавляется к **вашей установленной копии LiveMCP**: код стороннего сервера не входит в репозиторий и не заменяется форком с неизвестной лицензией.

```powershell
.venv/Scripts/python scripts/stage_extension.py "PATH_TO_LiveMCP" "local/LiveMCP-staged"
```

Команда создаёт отдельную копию. Перед заменой активного Remote Script закройте Live, сохраните оригинальную папку и следуйте инструкции. Обновлённые запросы выполняются в основном потоке Live. Сохранение, открытие сета и Collect All and Save **не объявляются доступными**: в используемом интерфейсе они не реализованы.

## Почему агенту нужно меньше контекста

- Короткий `SKILL.md` направляет в нужный справочник, вместо загрузки всей книги о сведении.
- Снимки ограничены страницами; вместо всех параметров запрашивается конкретное устройство.
- Подробные измерения хранятся в JSON, в диалог попадают вывод и нужные фрагменты.
- Планы правок привязаны к SHA-256 файла или ожидаемым именам и значениям параметров.
- `audio-analyze --cache local/cache` повторно использует анализ только при совпадении аудио, параметров, кода анализа и версий библиотек.
- `diff` сравнивает сохранённые отчёты. Ошибки транспортного уровня не запускают повторную запись вслепую.

В [синтетическом бенчмарке](docs/context-benchmark.json) обзор 24 дорожек и запрос одного устройства занимает 3 723 токена вместо 281 403 при выгрузке всех параметров. Это пример стоимости **конкретного запроса**, а не обещание такого же выигрыша на всём сведении. Входной скилл — около 1 081 токена; остальные справочники читаются по задаче.

## Границы и проверка

См. [docs/verification.md](docs/verification.md) — что проверено автоматически и что требует реального Live. Статическая проверка XML не гарантирует загрузку проекта. Сборщик копирует аудио `SampleRef`, но не заменяет штатный Collect All для плагинов, библиотек и пресетов. Пик с четырёхкратной передискретизацией помечен как оценка, не сертифицированный dBTP.

Локально прошли 55 тестов на Windows / Python 3.12.10. Первая проверка GitHub Actions не стартовала из-за блокировки аккаунта по биллингу; межплатформенный CI пока не подтверждён.

Пакет не отправляет аудио в облако. Исходники, захваты, модели и отчёты должны оставаться вне Git. Подробности — [SECURITY.md](SECURITY.md), лицензии — [THIRD_PARTY.md](THIRD_PARTY.md).

```powershell
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
```

English: this is a local, evidence-driven Ableton agent toolkit with a Codex skill, optional MCP bridge, additive LiveMCP handlers, audio analysis and conservative project tools. Install the Python package and skill, then follow the English skill references. See [setup](docs/setup.md) and [verification](docs/verification.md) for exact boundaries. Not affiliated with Ableton.
