from dsl.workflow_dsl import workflow, task

with workflow("ETL_Workflow") as wf:

    @task
    def extract():
        print("Extracting data...")
        return "raw_data"

    @task(max_retries=1)
    def transform():
        print("Transforming data...")
        return "clean_data"

    @task
    def load():
        print("Loading data...")
        return "loaded"

    # Set dependencies (if your DSL requires explicit dependency setup)
    wf.dag.get_task("transform").add_dependency(wf.dag.get_task("extract"))
    wf.dag.get_task("load").add_dependency(wf.dag.get_task("transform"))

    # Run the workflow
    wf.run()

