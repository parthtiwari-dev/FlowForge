# example.py

from core.task import Task
from core.dag import DAG

# Define dummy functions
def extract():
    print("Extracting data...")

def transform():
    print("Transforming data...")

def load():
    print("Loading data...")

# Create tasks
t1 = Task("extract", func=extract)
t2 = Task("transform", func=transform)
t3 = Task("load", func=load)

# Define dependencies
t2.add_dependency(t1)  # transform depends on extract
t3.add_dependency(t2)  # load depends on transform

# Build DAG
dag = DAG()
dag.add_task(t1)
dag.add_task(t2)
dag.add_task(t3)

# Check structure
dag.print_structure()

# Run in topological order
for task in dag.topological_sort():
    if task.is_ready():
        task.run()
