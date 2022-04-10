from typing import Any


def has_duplicates(iterable):
    seen = []
    for x in iterable:
        if x in seen:
            return True
        seen.append(x)
    return False


class Matrix:
    def __init__(self):
        self.matrix = {}
        self.n_x: int = 0
        self.n_y: int = 0

    def set_value(self, x: int, y: int, value):
        if x > self.n_x:
            self.n_x = x

        if y > self.n_y:
            self.n_y = y

        self.matrix[x, y] = value
        self.matrix[x, "n_values"] = self.matrix[x, "n_values"] + 1 or 1
        self.matrix[y, "n_values"] = self.matrix[y, "n_values"] + 1 or 1

    def get_value(self, x: int, y: int) -> Any:
        return self.matrix[x, y] or None

    def remove_value(self, x: int, y: int):
        del self.matrix[x, y]

        self.matrix[x, "n_values"] -= 1
        self.matrix[y, "n_values"] -= 1

        self.check_empty()

    def check_empty(self):
        changed: bool = False

        if self.matrix[self.n_x, "n_values"] == 0:
            self.n_x -= 1
            del self.matrix[self.n_x, "n_values"]
            changed = True

        if self.matrix[self.n_y, "n_values"] == 0:
            self.n_y -= 1
            del self.matrix[self.n_y, "n_values"]
            changed = True

        if changed:
            self.check_empty()
