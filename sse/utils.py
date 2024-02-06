import re
from typing import Union

from workspaces.models import Task, Column, Board


def get_board_id(path: str) -> Union[int, None]:
    pattern = r"/api/(\w+)/(\d+)/(\w+)/(\d+)?"
    match = re.match(pattern, path)

    if not match:
        return

    parent, parent_id = match.group(1), match.group(2)
    child = match.group(3)

    if child == 'comments':
        return
    elif parent == 'task':
        board_id = Task.objects.get(pk=parent_id).column.board_id
    elif parent == 'column':
        board_id = Column.objects.get(pk=parent_id).board_id
    elif parent == 'boards':
        board_id = parent_id
    elif parent == 'workspace':
        board_id = int(match.group(4))
    else:
        return

    return board_id


def get_task_id(path: str) -> Union[int, None]:
    pattern = r"/api/(\w+)/(\d+)/(\w+)/(\d+)"
    match = re.match(pattern, path)

    if not match:
        return

    if 'task' == match.group(3):
        return int(match.group(4))
