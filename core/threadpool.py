# -*- coding: UTF-8 -*-
"""Easy to use object-oriented thread core framework.

A thread core is an object that maintains a core of worker threads to perform
time consuming operations in parallel. It assigns jobs to the threads
by putting them in a work request queue, where they are picked up by the
next available thread. This then performs the requested operation in the
background and puts the results in another queue.

The thread core object can then collect the results from all threads from
this queue as soon as they become available or after all threads have
finished their work. It's also possible, to define callbacks to handle
each result as it comes in.

The basic concept and some code was taken from the book "Python in a Nutshell,
2nd edition" by Alex Martelli, O'Reilly 2006, ISBN 0-596-10046-9, from section
14.5 "Threaded Program Architecture". I wrapped the main program logic in the
ThreadPool class, added the WorkRequest class and the callback system and
tweaked the code here and there. Kudos also to Florent Aide for the exception
handling mechanism.

Basic usage::
    >>> poolsize=10
    >>> core = ThreadPool(poolsize)
    >>> requests = makeRequests(some_callable, list_of_args, callback)
    >>> [core.putRequest(req) for req in requests]
    >>> core.wait()

See the end of the module code for a brief, annotated usage example.

Website : http://chrisarndt.de/projects/threadpool/

"""
__docformat__ = "restructuredtext en"

__all__ = [
    'makeRequests',
    'NoResultsPending',
    'NoWorkersAvailable',
    'ThreadPool',
    'WorkRequest',
    'WorkerThread'
]

__author__ = "Christopher Arndt"
__version__ = '1.3.2'
__license__ = "MIT license"

# standard library modules
import sys
import threading
import traceback

try:
    import Queue  # Python 2
except ImportError:
    import queue as Queue  # Python 3


# exceptions
class NoResultsPending(Exception):
    """All work requests have been processed."""
    pass


class NoWorkersAvailable(Exception):
    """No worker threads available to process remaining requests."""
    pass


# internal module helper functions
def _handle_thread_exception(request, exc_info):
    """Default exception handler callback function.

    This just prints the exception info via ``traceback.print_exception``.

    """
    traceback.print_exception(*exc_info)


# utility functions
def makeRequests(callable_, args_list, callback=None,
                 exc_callback=_handle_thread_exception):
    """Create several work requests for same callable with different arguments.

    Convenience function for creating several work requests for the same
    callable where each invocation of the callable receives different values
    for its arguments.

    ``args_list`` contains the parameters for each invocation of callable.
    Each item in ``args_list`` should be either a 2-item tuple of the list of
    positional arguments and a dictionary of keyword arguments or a single,
    non-tuple argument.

    See docstring for ``WorkRequest`` for info on ``callback`` and
    ``exc_callback``.

    """
    requests = []
    for item in args_list:
        if isinstance(item, tuple):
            requests.append(
                WorkRequest(callable_, item[0], item[1], callback=callback, exc_callback=exc_callback)
            )
        else:
            requests.append(
                WorkRequest(callable_, [item], None, callback=callback, exc_callback=exc_callback)
            )
    return requests


# classes
class WorkerThread(threading.Thread):
    """Background thread connected to the requests/results queues.

    A worker thread sits in the background and picks up work requests from
    one queue and puts the results in another until it is dismissed.

    """

    def __init__(self, requests_queue, results_queue, poll_timeout=5, **kwds):
        """Set up thread in daemonic mode and start it immediatedly.

        ``requests_queue`` and ``results_queue`` are instances of
        ``Queue.Queue`` passed by the ``ThreadPool`` class when it creates a
        new worker thread.

        """
        threading.Thread.__init__(self, **kwds)
        self.setDaemon(True)
        self._requests_queue = requests_queue
        self._results_queue = results_queue
        self._poll_timeout = poll_timeout
        self._dismissed = threading.Event()
        self.start()

    def run(self):
        """Repeatedly process the job queue until told to exit."""
        while True:
            if self._dismissed.isSet():
                # we are dismissed, break out of loop
                break
            # get next work request. If we don't get a new request from the
            # queue after self._poll_timout seconds, we jump to the start of
            # the while loop again, to give the thread a chance to exit.
            try:
                request = self._requests_queue.get(True, self._poll_timeout)
            except Queue.Empty:
                continue
            else:
                if self._dismissed.isSet():
                    # we are dismissed, put back request in queue and exit loop
                    self._requests_queue.put(request)
                    break
                try:
                    result = request.callable(*request.args, **request.kwds)
                    self._results_queue.put((request, result))
                except:
                    request.exception = True
                    self._results_queue.put((request, sys.exc_info()))

    def dismiss(self):
        """Sets a flag to tell the thread to exit when done with current job.
        """
        self._dismissed.set()


class WorkRequest(object):
    """A request to execute a callable for putting in the request queue later.

    See the module function ``makeRequests`` for the common case
    where you want to build several ``WorkRequest`` objects for the same
    callable but with different arguments for each call.

    """

    def __init__(self, callable_, args=None, kwds=None, requestID=None,
                 callback=None, exc_callback=_handle_thread_exception):
        """Create a work request for a callable and attach callbacks.

        A work request consists of the a callable to be executed by a
        worker thread, a list of positional arguments, a dictionary
        of keyword arguments.

        A ``callback`` function can be specified, that is called when the
        results of the request are picked up from the result queue. It must
        accept two anonymous arguments, the ``WorkRequest`` object and the
        results of the callable, in that order. If you want to pass additional
        information to the callback, just stick it on the request object.

        You can also give custom callback for when an exception occurs with
        the ``exc_callback`` keyword parameter. It should also accept two
        anonymous arguments, the ``WorkRequest`` and a tuple with the exception
        details as returned by ``sys.exc_info()``. The default implementation
        of this callback just prints the exception info via
        ``traceback.print_exception``. If you want no exception handler
        callback, just pass in ``None``.

        ``requestID``, if given, must be hashable since it is used by
        ``ThreadPool`` object to store the results of that work request in a
        dictionary. It defaults to the return value of ``id(self)``.

        """
        if requestID is None:
            self.requestID = id(self)
        else:
            try:
                self.requestID = hash(requestID)
            except TypeError:
                raise TypeError("requestID must be hashable.")
        self.exception = False
        self.callback = callback
        self.exc_callback = exc_callback
        self.callable = callable_
        self.args = args or []
        self.kwds = kwds or {}

    def __str__(self):
        return "<WorkRequest id=%s args=%r kwargs=%r exception=%s>" % \
               (self.requestID, self.args, self.kwds, self.exception)


class ThreadPool(object):
    """A thread core, distributing work requests and collecting results.

    See the module docstring for more information.

    """

    def __init__(self, num_workers, q_size=0, resq_size=0, poll_timeout=5):
        """Set up the thread core and start num_workers worker threads.

        ``num_workers`` is the number of worker threads to start initially.

        If ``q_size > 0`` the size of the work *request queue* is limited and
        the thread core blocks when the queue is full and it tries to put
        more work requests in it (see ``putRequest`` method), unless you also
        use a positive ``timeout`` value for ``putRequest``.

        If ``resq_size > 0`` the size of the *results queue* is limited and the
        worker threads will block when the queue is full and they try to put
        new results in it.

        .. warning:
            If you set both ``q_size`` and ``resq_size`` to ``!= 0`` there is
            the possibilty of a deadlock, when the results queue is not pulled
            regularly and too many jobs are put in the work requests queue.
            To prevent this, always set ``timeout > 0`` when calling
            ``ThreadPool.putRequest()`` and catch ``Queue.Full`` exceptions.

        """
        self._requests_queue = Queue.Queue(q_size)
        self._results_queue = Queue.Queue(resq_size)
        self.workers = []
        self.dismissedWorkers = []
        self.workRequests = {}
        self.createWorkers(num_workers, poll_timeout)

    def createWorkers(self, num_workers, poll_timeout=5):
        """Add num_workers worker threads to the core.

        ``poll_timout`` sets the interval in seconds (int or float) for how
        ofte threads should check whether they are dismissed, while waiting for
        requests.

        """
        for i in range(num_workers):
            self.workers.append(WorkerThread(self._requests_queue,
                                             self._results_queue, poll_timeout=poll_timeout))

    def dismissWorkers(self, num_workers, do_join=False):
        """Tell num_workers worker threads to quit after their current task."""
        dismiss_list = []
        for i in range(min(num_workers, len(self.workers))):
            worker = self.workers.pop()
            worker.dismiss()
            dismiss_list.append(worker)

        if do_join:
            for worker in dismiss_list:
                worker.join()
        else:
            self.dismissedWorkers.extend(dismiss_list)

    def joinAllDismissedWorkers(self):
        """Perform Thread.join() on all worker threads that have been dismissed.
        """
        for worker in self.dismissedWorkers:
            worker.join()
        self.dismissedWorkers = []

    def putRequest(self, request, block=True, timeout=None):
        """Put work request into work queue and save its id for later."""
        assert isinstance(request, WorkRequest)
        # don't reuse old work requests
        assert not getattr(request, 'exception', None)
        self._requests_queue.put(request, block, timeout)
        self.workRequests[request.requestID] = request

    def poll(self, block=False):
        """Process any new results in the queue."""
        while True:
            # still results pending?
            if not self.workRequests:
                raise NoResultsPending
            # are there still workers to process remaining requests?
            elif block and not self.workers:
                raise NoWorkersAvailable
            try:
                # get back next results
                request, result = self._results_queue.get(block=block)
                # has an exception occured?
                if request.exception and request.exc_callback:
                    request.exc_callback(request, result)
                # hand results to callback, if any
                if request.callback and not (request.exception and request.exc_callback):
                    request.callback(request, result)
                del self.workRequests[request.requestID]
            except Queue.Empty:
                break

    def wait(self):
        """Wait for results, blocking until all have arrived."""
        while 1:
            try:
                self.poll(True)
            except NoResultsPending:
                break


################
# USAGE EXAMPLE
################

if __name__ == '__main__':
    import random
    import time

    # 线程必须要做的工作（在我们的例子中是微不足道的）
    def do_something(data):
        time.sleep(2)
        result = round(random.random() * data, 5)
        # 只是为了展示，我们偶尔抛出一个异常
        # if result > 5:
        #     raise RuntimeError("展示异常情况!")
        return result


    # 每次结果都可以调用
    def print_result(request, result):
        pass
        # print("**** 返回一个请求 #%s: %r" % (request.requestID, result))


    # 当线程中出现异常时，将调用这个示例异常处理程序只比默认处理程序多一点
    def handle_exception(request, exc_info):
        if not isinstance(exc_info, tuple):
            # 有些严重的错误 ...
            print(request)
            print(exc_info)
            raise SystemExit
        print("**** 请求发生异常 #%s: %s" % (request.requestID, exc_info))


    # 将每个作业的参数组合到列表中 ...
    data = [random.randint(1, 10) for i in range(20)]
    # ... 并为数据中的每个项构建工作请求对象
    requests = makeRequests(do_something, data, print_result, handle_exception)
    # 若要使用默认异常处理程序，请取消注释下一行并注释掉
    # requests = makeRequests(do_something, data, print_result)

    # 或其他形式的Args列表接受 makeRequests: ((,), {})
    data = [((random.randint(1, 10),), {}) for i in range(20)]
    requests.extend(
        makeRequests(do_something, data, print_result, handle_exception)
        # 使用默认的异常处理程序，取消注释下一行和注释
        # makeRequests(do_something, data, print_result)
    )

    # 我们创建了一个3个工作线程池
    print("Creating thread core with 3 worker threads.")
    main = ThreadPool(3)

    # 然后在队列中放置工作请求...
    for req in requests:
        main.putRequest(req)
        print("工作请求 #%s added." % req.requestID)
    # 或更短
    # [main.putRequest(req) for req in requests]

    # 等待结果到达结果队列 使用THealPoCult.WaIT（）。这将阻塞直到所有的工作都已经完成
    # main.wait()

    # 相反，我们可以在做其他事情的时候投票结果。:
    i = 0
    while True:
        try:
            time.sleep(0.5)
            main.poll()
            print("主线程工作...")
            print("(活跃的工作线程: %i)" % (threading.activeCount() - 1,))
            if i == 10:
                print("**** 添加3个工作线程...")
                main.createWorkers(3)
            if i == 20:
                print("**** 退出2个工作线程...")
                main.dismissWorkers(2)
            i += 1
        except KeyboardInterrupt:
            print("**** 中断!")
            break
        except NoResultsPending:
            print("**** 没有结果返回.")
            break
    if main.dismissedWorkers:
        print("退出所有工作线程...")
        main.joinAllDismissedWorkers()
