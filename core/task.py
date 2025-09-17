class Task:
    def __init__(self, name, dependencies=None):
        self.name = name
        self.dependencies = dependencies if dependencies is not None else []
        self.state = 'pending'  # Possible states: pending, running, completed, failed

    def execute(self):
        # Logic to execute the task
        pass

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def add_dependency(self, task):
        self.dependencies.append(task)

    def remove_dependency(self, task):
        self.dependencies.remove(task)

    def has_dependencies(self):
        return len(self.dependencies) > 0