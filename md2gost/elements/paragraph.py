from dataclasses import dataclass, field

from .run import Run


@dataclass
class Paragraph:
    runs: list[Run] = field(default_factory=list)

    def add_run(self, *args, **kwargs):
        self.runs.append(Run(*args, **kwargs))

    @property
    def text(self) -> str:
        return "".join([run.text for run in self.runs])