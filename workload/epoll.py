"""Event wait path: perf bench epoll wait, N-1 waiter threads woken through epoll."""
from common import run_bench, parse, main

def bench_epoll():
    r = run_bench(["perf", "bench", "epoll", "wait"])
    return {"ops_s": (parse(r"Averaged\s+([\d.]+) operations/sec", r, "perf epoll"), "higher")}

BENCHMARKS = {"epoll": {"needs": "perf", "fn": bench_epoll}}

if __name__ == "__main__":
    main(BENCHMARKS)
