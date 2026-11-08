"""Futex paths (perf bench futex): hash = uncontended wait/wake through the futex hash,
lock-pi = contended PI lock, the rtmutex path (the whole kernel on PREEMPT_RT)."""
from common import run_bench, parse, main

def _futex(sub):
    r = run_bench(["perf", "bench", "futex", sub])
    return parse(r"Averaged\s+([\d.]+) operations/sec", r, f"perf futex {sub}")

def bench_futex():
    return {"hash.ops_s": (_futex("hash"), "higher"),
            "lock-pi.ops_s": (_futex("lock-pi"), "higher")}

BENCHMARKS = {"futex": {"needs": "perf", "fn": bench_futex}}

if __name__ == "__main__":
    main(BENCHMARKS)
