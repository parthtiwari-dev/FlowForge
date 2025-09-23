# FlowForge Examples

This directory contains example workflows demonstrating different use cases of FlowForge. Each example showcases specific features and patterns for building robust workflow automation.

## Overview

FlowForge examples demonstrate practical implementations for:
- **Data Pipeline Automation**: ETL processes and data transformation workflows
- **Machine Learning Pipelines**: ML model training, validation, and deployment workflows
- **Complex Multi-step Workflows**: Advanced dependency management and error handling

---

## 📊 sample_workflow.py

**Purpose**: Comprehensive demonstration of all FlowForge features

### Workflow Structure
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   setup     │───▶│  process    │───▶│  cleanup    │
└─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
    Initialize          Transform            Finalize
   Environment           Data               Results
```

### Key Features Demonstrated
- **Task Dependencies**: Linear and parallel task execution
- **Retry Logic**: Configurable retry mechanisms with exponential backoff
- **Event Management**: Comprehensive logging and monitoring
- **State Persistence**: Checkpoint and recovery capabilities
- **Multiple Executors**: Local, threaded, and process-based execution
- **Context Management**: Resource cleanup and file handling

### Tasks Breakdown
1. **Setup Task**: Environment initialization and resource allocation
2. **Process Task**: Core data processing with retry capabilities
3. **Cleanup Task**: Resource cleanup and result finalization

### Usage
```bash
# Basic execution
python cli.py run examples/sample_workflow.py

# With threading and workers
python cli.py run examples/sample_workflow.py --executor thread --workers 4

# With checkpointing
python cli.py run examples/sample_workflow.py --checkpoint sample_state.json

# Verbose mode for debugging
python cli.py run examples/sample_workflow.py --verbose
```

---

## 🔄 etl_workflow.py

**Purpose**: Classic Extract-Transform-Load data pipeline

### Workflow Structure
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Extract   │───▶│ Transform   │───▶│    Load     │
└─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
  Data Sources         Data Cleaning        Data Storage
  • Databases         • Validation         • Warehouses
  • APIs              • Normalization      • Files
  • Files             • Enrichment         • APIs
```

### Key Features Demonstrated
- **Sequential Processing**: Strict ordering for data integrity
- **Data Validation**: Input/output validation at each stage
- **Error Handling**: Graceful failure recovery and data rollback
- **Monitoring**: Progress tracking and performance metrics

### Tasks Breakdown
1. **Extract Task**: 
   - Connects to data sources
   - Validates data availability
   - Handles connection timeouts and retries
   
2. **Transform Task**:
   - Data cleaning and validation
   - Format standardization
   - Business rule application
   
3. **Load Task**:
   - Data persistence to target systems
   - Integrity checks
   - Transaction management

### Usage
```bash
# Standard ETL execution
python cli.py run examples/etl_workflow.py

# With data validation
python cli.py run examples/etl_workflow.py --verbose

# Process-based for large datasets
python cli.py run examples/etl_workflow.py --executor process --workers 2
```

---

## 🤖 ml_workflow.py

**Purpose**: End-to-end Machine Learning pipeline automation

### Workflow Structure
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Data Prepare │───▶│   Train     │───▶│  Validate   │───▶│   Deploy    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
  • Data Loading      • Model Training    • Performance      • Model Serving
  • Preprocessing     • Hyperparameter     Evaluation       • API Deployment
  • Feature Eng.        Tuning           • Cross-validation • Monitoring
  • Train/Test Split  • Model Selection   • Metrics Report   • A/B Testing
```

### Key Features Demonstrated
- **Parallel Training**: Multiple model training with different parameters
- **Model Validation**: Automated performance evaluation
- **Experiment Tracking**: Metrics and artifact management
- **Conditional Deployment**: Deploy only if validation passes
- **Resource Management**: GPU/CPU allocation for training tasks

### Tasks Breakdown
1. **Data Preparation Task**:
   - Data loading and validation
   - Feature engineering and selection
   - Train/validation/test split
   - Data preprocessing and scaling

2. **Model Training Task**:
   - Multiple algorithm training
   - Hyperparameter optimization
   - Cross-validation setup
   - Model artifact saving

3. **Model Validation Task**:
   - Performance metric calculation
   - Model comparison and selection
   - Validation report generation
   - Quality gate evaluation

4. **Model Deployment Task**:
   - Model packaging and versioning
   - API endpoint creation
   - Performance monitoring setup
   - Rollback capability

### Usage
```bash
# Full ML pipeline
python cli.py run examples/ml_workflow.py

# Parallel training with multiple workers
python cli.py run examples/ml_workflow.py --executor process --workers 4

# With experiment tracking
python cli.py run examples/ml_workflow.py --checkpoint ml_experiment.json

# Development mode with detailed logging
python cli.py run examples/ml_workflow.py --verbose --dry-run
```

---

## 🚀 Getting Started

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python cli.py --help
```

### Running Examples

1. **Start with the sample workflow** to understand basic concepts:
   ```bash
   python cli.py run examples/sample_workflow.py --verbose
   ```

2. **Try the ETL workflow** for data processing use cases:
   ```bash
   python cli.py run examples/etl_workflow.py
   ```

3. **Explore the ML workflow** for machine learning automation:
   ```bash
   python cli.py run examples/ml_workflow.py
   ```

### Common Patterns

#### Adding Dependencies
```python
# Task B depends on Task A
task_b.add_dependency(task_a)

# Multiple dependencies
task_c.add_dependency(task_a)
task_c.add_dependency(task_b)
```

#### Error Handling
```python
# Configure retries
task = Task("my_task", func=my_function, max_retries=3)

# Custom retry strategy
@retry_task(max_retries=5, backoff_factor=2.0)
def unreliable_function():
    # Function implementation
    pass
```

#### Resource Management
```python
# Context managers for cleanup
@with_context(lambda: file_context("output.txt", "w"))
def write_results(file_handle):
    file_handle.write("Results")
    return "success"
```

---

## 🔧 Customization

Each example can be customized for your specific needs:

### Modifying Task Functions
- Replace example functions with your actual business logic
- Maintain the same function signature for compatibility
- Add proper error handling and logging

### Adjusting Dependencies
- Modify task dependencies based on your workflow requirements
- Add parallel execution paths where appropriate
- Consider data dependencies and resource constraints

### Configuration Options
- Adjust retry counts and timeouts
- Configure different executors based on workload
- Set up custom event handlers and metrics

---

## 📋 Best Practices

1. **Task Design**:
   - Keep tasks focused on single responsibilities
   - Make tasks idempotent when possible
   - Include proper input validation

2. **Error Handling**:
   - Use appropriate retry strategies
   - Implement graceful degradation
   - Log errors with sufficient context

3. **Performance**:
   - Choose the right executor for your workload
   - Monitor resource usage
   - Use checkpointing for long-running workflows

4. **Testing**:
   - Use `--dry-run` for workflow validation
   - Test individual tasks before integration
   - Implement comprehensive logging

---

## 📚 Additional Resources

- **Main Documentation**: See the root README.md for complete FlowForge documentation
- **API Reference**: Check the `core/` directory for detailed API documentation
- **Testing**: Review the `tests/` directory for testing patterns
- **CLI Help**: Run `python cli.py --help` for all available commands

For more advanced use cases and custom implementations, refer to the main FlowForge documentation and API reference.
