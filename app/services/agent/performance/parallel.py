"""Parallel processing utilities for agent operations."""
import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps

from app.services.agent.config import agent_config

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """Parallel execution manager for agent operations."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize parallel executor."""
        self.max_workers = max_workers
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers)
    
    async def execute_parallel_async(
        self,
        tasks: List[Callable],
        task_args: List[Tuple] = None,
        task_kwargs: List[Dict] = None,
        return_exceptions: bool = True
    ) -> List[Any]:
        """Execute async tasks in parallel."""
        
        if task_args is None:
            task_args = [() for _ in tasks]
        if task_kwargs is None:
            task_kwargs = [{} for _ in tasks]
        
        # Create coroutines
        coroutines = []
        for i, task in enumerate(tasks):
            args = task_args[i] if i < len(task_args) else ()
            kwargs = task_kwargs[i] if i < len(task_kwargs) else {}
            
            if asyncio.iscoroutinefunction(task):
                coroutines.append(task(*args, **kwargs))
            else:
                # Wrap sync function in async
                coroutines.append(self._run_sync_in_thread(task, *args, **kwargs))
        
        # Execute in parallel
        start_time = time.time()
        results = await asyncio.gather(*coroutines, return_exceptions=return_exceptions)
        execution_time = time.time() - start_time
        
        logger.debug(f"Executed {len(tasks)} tasks in parallel in {execution_time:.2f}s")
        
        return results
    
    async def _run_sync_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run synchronous function in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_executor, func, *args, **kwargs)
    
    async def execute_with_semaphore(
        self,
        tasks: List[Callable],
        max_concurrent: int = None,
        task_args: List[Tuple] = None,
        task_kwargs: List[Dict] = None
    ) -> List[Any]:
        """Execute tasks with concurrency limit using semaphore."""
        
        max_concurrent = max_concurrent or self.max_workers
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_task(task, args, kwargs):
            async with semaphore:
                if asyncio.iscoroutinefunction(task):
                    return await task(*args, **kwargs)
                else:
                    return await self._run_sync_in_thread(task, *args, **kwargs)
        
        if task_args is None:
            task_args = [() for _ in tasks]
        if task_kwargs is None:
            task_kwargs = [{} for _ in tasks]
        
        # Create limited tasks
        limited_tasks = [
            limited_task(task, task_args[i] if i < len(task_args) else (), 
                        task_kwargs[i] if i < len(task_kwargs) else {})
            for i, task in enumerate(tasks)
        ]
        
        # Execute with semaphore
        start_time = time.time()
        results = await asyncio.gather(*limited_tasks, return_exceptions=True)
        execution_time = time.time() - start_time
        
        logger.debug(f"Executed {len(tasks)} tasks with semaphore ({max_concurrent}) in {execution_time:.2f}s")
        
        return results
    
    def shutdown(self):
        """Shutdown executors."""
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)


class BatchProcessor:
    """Batch processor for handling multiple similar operations."""
    
    def __init__(self, batch_size: int = 10, max_wait_time: float = 1.0):
        """Initialize batch processor."""
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_items: List[Tuple[Any, asyncio.Future]] = []
        self.batch_lock = asyncio.Lock()
        self.processing = False
    
    async def add_item(self, item: Any, processor: Callable) -> Any:
        """Add item to batch for processing."""
        future = asyncio.Future()
        
        async with self.batch_lock:
            self.pending_items.append((item, future))
            
            # Start batch processing if not already running
            if not self.processing:
                asyncio.create_task(self._process_batch(processor))
        
        return await future
    
    async def _process_batch(self, processor: Callable):
        """Process current batch."""
        self.processing = True
        
        try:
            # Wait for batch to fill or timeout
            start_time = time.time()
            while (len(self.pending_items) < self.batch_size and 
                   time.time() - start_time < self.max_wait_time):
                await asyncio.sleep(0.1)
            
            # Get current batch
            async with self.batch_lock:
                batch_items = self.pending_items.copy()
                self.pending_items.clear()
            
            if not batch_items:
                return
            
            # Process batch
            items = [item for item, _ in batch_items]
            futures = [future for _, future in batch_items]
            
            try:
                if asyncio.iscoroutinefunction(processor):
                    results = await processor(items)
                else:
                    results = processor(items)
                
                # Set results
                for i, future in enumerate(futures):
                    if i < len(results):
                        future.set_result(results[i])
                    else:
                        future.set_exception(IndexError("Not enough results"))
                        
            except Exception as e:
                # Set exception for all futures
                for future in futures:
                    future.set_exception(e)
        
        finally:
            self.processing = False


class ParallelContextAssembler:
    """Parallel context assembly for multiple document types."""
    
    def __init__(self, executor: ParallelExecutor):
        """Initialize parallel context assembler."""
        self.executor = executor
    
    async def assemble_context_parallel(
        self,
        project_id: str,
        targets: Dict[str, List[str]],
        intent: str,
        tools: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assemble context using parallel retrieval."""
        
        # Prepare parallel tasks
        tasks = []
        task_args = []
        task_kwargs = []
        
        # SO sections task
        if targets.get("so_ids") and "so_tool" in tools:
            tasks.append(tools["so_tool"]._execute)
            task_kwargs.append({
                "project_id": project_id,
                "section_ids": targets["so_ids"],
                "include_neighbors": intent in ["improve_paragraph", "integration_check"]
            })
        
        # Requirements task
        if targets.get("requirement_ids") and "requirement_tool" in tools:
            tasks.append(tools["requirement_tool"]._execute)
            task_kwargs.append({
                "project_id": project_id,
                "requirement_ids": targets["requirement_ids"]
            })
        
        # Diagrams task
        if targets.get("diagram_ids") and "diagram_tool" in tools:
            tasks.append(tools["diagram_tool"]._execute)
            task_kwargs.append({
                "project_id": project_id,
                "diagram_ids": targets["diagram_ids"]
            })
        
        # Chat summary task
        if "chat_tool" in tools:
            tasks.append(tools["chat_tool"]._execute)
            task_kwargs.append({
                "project_id": project_id
            })
        
        # Execute tasks in parallel
        if not tasks:
            return {
                "so_sections": [],
                "requirements": [],
                "diagrams": [],
                "chat_summary": "",
                "metadata": {"parallel_execution": False}
            }
        
        start_time = time.time()
        results = await self.executor.execute_parallel_async(
            tasks=tasks,
            task_kwargs=task_kwargs,
            return_exceptions=True
        )
        execution_time = time.time() - start_time
        
        # Process results
        assembled_context = {
            "so_sections": [],
            "requirements": [],
            "diagrams": [],
            "chat_summary": "",
            "metadata": {
                "parallel_execution": True,
                "execution_time_ms": int(execution_time * 1000),
                "tasks_executed": len(tasks)
            }
        }
        
        # Merge results based on task order
        task_index = 0
        
        if targets.get("so_ids"):
            if task_index < len(results) and not isinstance(results[task_index], Exception):
                result = results[task_index]
                assembled_context["so_sections"] = result.get("sections", [])
            task_index += 1
        
        if targets.get("requirement_ids"):
            if task_index < len(results) and not isinstance(results[task_index], Exception):
                result = results[task_index]
                assembled_context["requirements"] = result.get("requirements", [])
            task_index += 1
        
        if targets.get("diagram_ids"):
            if task_index < len(results) and not isinstance(results[task_index], Exception):
                result = results[task_index]
                assembled_context["diagrams"] = result.get("diagrams", [])
            task_index += 1
        
        # Chat summary (always last if present)
        if "chat_tool" in tools:
            if task_index < len(results) and not isinstance(results[task_index], Exception):
                assembled_context["chat_summary"] = results[task_index]
        
        return assembled_context


def parallel_enabled(func: Callable) -> Callable:
    """Decorator to enable parallel processing for a function."""
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if agent_config.parallel_processing:
            return await func(*args, **kwargs)
        else:
            # Fall back to sequential execution
            logger.debug(f"Parallel processing disabled for {func.__name__}")
            return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if agent_config.parallel_processing:
            return func(*args, **kwargs)
        else:
            logger.debug(f"Parallel processing disabled for {func.__name__}")
            return func(*args, **kwargs)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class AsyncQueue:
    """Async queue for managing work items."""
    
    def __init__(self, maxsize: int = 0):
        """Initialize async queue."""
        self.queue = asyncio.Queue(maxsize=maxsize)
        self.workers: List[asyncio.Task] = []
        self.running = False
    
    async def put(self, item: Any) -> None:
        """Put item in queue."""
        await self.queue.put(item)
    
    async def get(self) -> Any:
        """Get item from queue."""
        return await self.queue.get()
    
    def task_done(self) -> None:
        """Mark task as done."""
        self.queue.task_done()
    
    async def join(self) -> None:
        """Wait for all tasks to complete."""
        await self.queue.join()
    
    def start_workers(self, worker_func: Callable, num_workers: int = 4) -> None:
        """Start worker tasks."""
        self.running = True
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(worker_func, f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop_workers(self) -> None:
        """Stop all workers."""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
    
    async def _worker(self, worker_func: Callable, worker_name: str) -> None:
        """Worker coroutine."""
        logger.debug(f"Starting worker: {worker_name}")
        
        try:
            while self.running:
                try:
                    # Get work item with timeout
                    item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                    
                    # Process item
                    if asyncio.iscoroutinefunction(worker_func):
                        await worker_func(item)
                    else:
                        worker_func(item)
                    
                    # Mark task as done
                    self.queue.task_done()
                    
                except asyncio.TimeoutError:
                    # No work available, continue
                    continue
                except Exception as e:
                    logger.error(f"Error in worker {worker_name}: {str(e)}")
                    self.queue.task_done()
        
        except asyncio.CancelledError:
            logger.debug(f"Worker {worker_name} cancelled")
        
        logger.debug(f"Worker {worker_name} stopped")


# Global instances
parallel_executor = ParallelExecutor(max_workers=agent_config.max_so_chunks)
batch_processor = BatchProcessor()
parallel_context_assembler = ParallelContextAssembler(parallel_executor)