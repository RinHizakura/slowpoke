"""stress-ng rates, N workers x 15s: page faults, fork/exec, mmap/munmap, timerfd, dentry (tmpfs)."""
from common import NPROC, run_bench, parse, main

def _stressng(stressor, *extra):
    """bogo ops/s (real time) for one stress-ng stressor, N workers x 15s."""
    r = run_bench(["stress-ng", f"--{stressor}", NPROC, "-t", "15", "--metrics-brief", *extra])
    v = parse(rf"{stressor}\s+\d+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)",  # 5th col = bogo ops/s (real)
              r, f"stress-ng {stressor}")
    return {"bogo_ops_s": (v, "higher")}

BENCHMARKS = {
    "pagefault": {"needs": "stress-ng", "fn": lambda: _stressng("fault")},
    "fork":      {"needs": "stress-ng", "fn": lambda: _stressng("fork")},
    # map + touch + unmap 8M per op: VMA setup/teardown with a little faulting, not a second pagefault
    "mmap":      {"needs": "stress-ng", "fn": lambda: _stressng("mmap", "--mmap-bytes", "8M")},
    "timerfd":   {"needs": "stress-ng", "fn": lambda: _stressng("timerfd")},  # hrtimer arm/expire/read
    "dentry":    {"needs": "stress-ng", "fn": lambda: _stressng("dentry", "--temp-path", "/dev/shm")},  # vfs + dcache, no disk
}

if __name__ == "__main__":
    main(BENCHMARKS)
