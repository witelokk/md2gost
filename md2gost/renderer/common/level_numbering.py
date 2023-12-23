class LevelNumbering:
    def __init__(self):
        self._numbering = [1 for _ in range(10)]
        self._previous_level = 0

    def new(self, level: int):
        if self._previous_level >= level:
            self._numbering[level - 1] += 1
            for i in range(level, len(self._numbering)):
                self._numbering[i] = 1

        self._previous_level = level

        return ".".join([str(x) for x in self._numbering[:level]])
