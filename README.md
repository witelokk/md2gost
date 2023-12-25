# md2gost

Скрипт для генерации docx отчета в соответствии с ГОСТ из markdown файла.

## Основные возможности
- Генерация отчета;
- Добавление титульной страницы в формате docx;
- Генерация интерактивного содержания;
- Поддержка сквозной нумерации и кросс-референсинга;
- Автоматическая расстановка рисунков, продолжений таблиц и листингов и т.д.

## Пример
Markdown-файл: [example.md](https://github.com/witelokk/md2gost/blob/main/examples/example.md).

Сгенерированный файл в zip архиве (команда `python -m md2gost --syntax-highlighting example.md`): [example.zip](https://nightly.link/witelokk/md2gost/workflows/example-generator/main/example.zip?h=f65c99d31a9379f44fcc6e923de4a735a271d5aa).

## Установка
Для установки и обновления используйте:
```bash
pip install --upgrade git+https://github.com/witelokk/md2gost.git@main
```

<details>
<summary>PEP 668</summary>

Если ваша система приняла стандарт [PEP 668](https://peps.python.org/pep-0668/), используйте [pipx](https://pypa.github.io/pipx/):
```bash
pipx install git+https://github.com/witelokk/md2gost.git@main
```

Обновление:

```bash
pipx upgrade md2gost
```
</details>


> [!IMPORTANT]
> Также  в системе должны быть установлены шрифты **Times New Roman** и **Courier New** (можно поменять в шаблоне).

## Использование
```
(python -m ) md2gost [-h] [-o OUTPUT] [-T TITLE] [--title-pages TITLE_PAGES] [--syntax-highlighting | --no-syntax-highlighting] [--debug] [filenames ...]
```

При отсутствии флага -o, сгенерированный отчет будет иметь имя с названием исходного файла и расширением .docx.

## Фичи
Скрипт использует [Github Flavored Markdown](https://github.github.com/gfm/) + синтаксис, описанный ниже.

### Шаблон
Чтобы поменять какие-то параметры в документе (отступы, размер шрифта и т.д.), скачайте [шаблон](https://github.com/witelokk/md2gost/raw/main/md2gost/Template.docx), настройте его
и укажите как параметр `--template`(или `-t`): `md2gost report.md --template my_template.docx`

### Добавление титульной страницы
Чтобы добавить титульную страницу, используйте флаг `--title`(`-T`) с путем до файла с титульной страницей (в формате docx).

Пример: `md2gost report.md --title title.docx`.

### Номер первой страницы
Чтобы изменить номер первой страницы, используйте параметр `--first-page` (например `--first-page 3`).

### Подписи рисунков, листингов, таблиц
<details>
<summary>Рисунки</summary>

```markdown
![](path/to/image "Caption text")
```

</details>

<details>
<summary>Таблицы</summary>

```markdown
% Caption text

| a | b | c |
|---|---|---|
| a | b | c |
```

</details>

<details>
<summary>Листинги</summary>

~~~markdown
% Caption text

```python
print("hello world")
```
~~~

</details>

<details>
<summary>Формулы</summary>

```markdown
%uniquename

$$
2 + 2 = 4
$$
```

</details>

### Ссылки (кросс-референсинг)
Чтобы вставить кликабельный номер картинки/листинга/etc, используйте
~~~markdown
![](path/to/image "%pic")

%code

```python
print("hello world")
```

Рис. @pic, листинг @code.
~~~

### Заголовки для основных разделов
Для заголовков основных разделов (таких, как `СОДЕРЖАНИЕ`, `ВВЕДЕНИЕ` и т.д.) автоматически отключена нумерация и 
включено выравнивание по центру.

<details>
<summary>Полный список таких заголовков</summary>

- СПИСОК ИСПОЛНИТЕЛЕЙ
- РЕФЕРАТ
- СОДЕРЖАНИЕ
- ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ
- ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ
- ВВЕДЕНИЕ
- ЗАКЛЮЧЕНИЕ
- СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ
- ПРИЛОЖЕНИЕ ...

</details>

### Генерация содержания
```markdown
[TOC]
```

### Подсветка синтаксиса в листингах
Используйте флаг ```--syntax-highlighting```.

### Импорт кода в листингах
~~~markdown
```python code.py
```
~~~
`code.py` - путь до файла с кодом.
