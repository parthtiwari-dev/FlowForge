# retry_utils.py

def retry(func, retries=3, delay=1):
    """Retry a function or method with a specified number of retries and delay."""
    import time
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

def backoff(func, retries=3, initial_delay=1, backoff_factor=2):
    """Retry a function with exponential backoff."""
    import time
    delay = initial_delay
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= backoff_factor
            else:
                raise e