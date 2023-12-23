import re
from dataclasses import dataclass, field

from .run import Run


@dataclass(unsafe_hash=True)
class Heading:
    runs: list[Run] = field(default_factory=list)
    level: int = 1
    _numbered = True

    @property
    def numbered(self):
        text = "".join(run.text for run in self.runs)

        # ГОСТ 7.32―2017 6.2.1-6.2.2
        if (text in ("СПИСОК ИСПОЛНИТЕЛЕЙ", "РЕФЕРАТ", "СОДЕРЖАНИЕ", "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ",
                     "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ", "ВВЕДЕНИЕ", "ЗАКЛЮЧЕНИЕ",
                     "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ") or text.startswith("ПРИЛОЖЕНИЕ")):
            return False
        return self._numbered

    @numbered.setter
    def numbered(self, value):
        self._numbered = value

    def add_run(self, *args, **kwargs):
        self.runs.append(Run(*args, **kwargs))

    @property
    def reference(self):
        return re.sub(r'([^\w-])+', '', self.text.lower().replace(" ", "-"))

    @property
    def text(self) -> str:
        return "".join(run.text for run in self.runs)
