

class TaskCommonDataMixin:
    def fill_common_data(self):
        board = self.obj.column.board
        self.data['workspace'] = board.work_space_id
        self.data['board'] = board.id
        self.data['task'] = self.obj.name
        self.data['link'] = self.generate_task_link(
            board.work_space_id,
            board.id,
            self.obj.id
        )
