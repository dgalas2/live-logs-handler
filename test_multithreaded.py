"""
Test script for multi-threaded logging with stdout, stderr, and logging module.

This script spawns multiple threads that simultaneously write logs using:
- #print() statements (stdout)
- sys.stderr.write() (stderr)
- logging module (logging.info, logging.error, etc.)

Run this to verify thread-safe behavior of the logger.
"""

import sys
import time
import logging
import threading
from live_logs_handler import start_logging


def worker_task(worker_id, iterations=5):
    """
    Worker function that generates various types of log output.
    
    Args:
        worker_id: Unique identifier for this worker thread
        iterations: Number of log messages to generate
    """
    for i in range(iterations):
        # Print to stdout
        #print(f"[Worker {worker_id}] Print message #{i+1}")
        
        # Write to stderr
        # sys.stderr.write(f"[Worker {worker_id}] Stderr message #{i+1}\n")
        # sys.stderr.flush()
        
        # Use logging module
        logging.info(f"Worker {worker_id} - Info log #{i+1}")
        logging.warning(f"Worker {worker_id} - Warning log #{i+1}")
        
        if i % 3 == 0:
            logging.error(f"Worker {worker_id} - Error log #{i+1}")
        
        # Small delay to create interleaving
        time.sleep(0.01)
    
    logging.info(f"Worker {worker_id} completed all iterations")


def test_basic_logging():
    """Test basic logging functionality."""
    #print("\n=== Test 1: Basic Logging ===")
    
    logger = start_logging("test_basic.log", capture_print=True)
    
    #print("Testing basic print statement")
    logging.info("Testing basic logging.info")
    logging.error("Testing basic logging.error")
    # sys.stderr.write("Testing stderr write\n")
    
    logger.stop()
    #print("✓ Basic logging test completed\n")


def test_multithreaded_logging():
    """Test multi-threaded logging with concurrent workers."""
    #print("\n=== Test 2: Multi-threaded Logging ===")
    
    # Start logger
    logger = start_logging("test_multithreaded.log", capture_print=True)
    
    # Create multiple worker threads
    num_threads = 5
    iterations_per_thread = 10
    threads = []
    
    #print(f"Spawning {num_threads} worker threads...")
    
    for i in range(num_threads):
        thread = threading.Thread(
            target=worker_task,
            args=(i, iterations_per_thread),
            name=f"Worker-{i}"
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Stop logger
    logger.stop()
    #print(f"✓ Multi-threaded test completed: {num_threads} threads × {iterations_per_thread} iterations\n")

    
    try:
        # Another exception
        items = [1, 2, 3]
        value = items[10]
    except IndexError:
        logging.exception("Caught index error")
    
    logger.stop()
    #print("✓ Exception logging test completed\n")


def test_high_volume_logging():
    """Test high-volume logging from multiple threads."""
    #print("\n=== Test 5: High Volume Logging ===")
    
    logger = start_logging("test_high_volume.log", buffer_size=5000, capture_print=True)
    
    num_threads = 10
    iterations = 50
    threads = []
    
    #print(f"Spawning {num_threads} threads with {iterations} iterations each...")
    
    for i in range(num_threads):
        thread = threading.Thread(
            target=worker_task,
            args=(i, iterations),
            name=f"HighVolume-{i}"
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    logger.stop()
    #print(f"✓ High volume test completed: {num_threads * iterations * 4} log entries\n")


def main():
    """Run all tests."""
    #print("=" * 60)
    #print("Multi-threaded Logging Test Suite")
    #print("=" * 60)
    
    # Run all tests
    test_basic_logging()
    test_multithreaded_logging()
    # test_logfmt_format()
    # test_exception_logging()
    test_high_volume_logging()
    
    #print("=" * 60)
    #print("All tests completed successfully! ✓")
    #print("=" * 60)


if __name__ == "__main__":
    main()
