"""Корневой conftest для pytest.

Добавляет каталог проекта в sys.path, чтобы тесты могли импортировать
модули inventory и storage независимо от текущего каталога запуска
(из папки проекта, из родительской папки, из IDE/VS Code и т. п.).
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
