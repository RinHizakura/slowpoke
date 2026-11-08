"""rtla tracers (need root for tracefs):
timerlat — a 1ms periodic timer on every CPU, latency until a user thread runs (irq +
kernel thread + return to user); p99.9 and p99.99 over all samples (CONFIG_TIMERLAT_TRACER).
osnoise — a busy loop on every CPU, counting the time stolen by irqs, softirqs, NMIs
and other threads (CONFIG_OSNOISE_TRACER + CONFIG_HIST_TRIGGERS for the histogram)."""
import os
from common import run_bench, main

DURATION = 30  # s per rep; timerlat's 1ms period -> 30k samples per CPU
ENTRIES = 4096  # timerlat hist buckets of 1us; samples past this land in "over:"

def _root():
    if os.geteuid():
        raise RuntimeError("needs root (tracefs)")

def _pct(hist, p):
    """p-quantile (0-1) of a {latency_us: count} histogram."""
    total, acc = sum(hist.values()), 0
    for us in sorted(hist):
        acc += hist[us]
        if acc >= p * total:
            return us

def _hist(cmd):
    """Run an `rtla ... hist` command and return (cols, hist, summ): cols the column names
    after "Index", hist[col] a {bucket_us: count} dict, summ[row][col] for over/count/avg/max.
    rtla prints one row per 1us bucket (zero rows omitted), then over:/count:/min:/avg:/max:."""
    r = run_bench(cmd)
    lines = r.stdout.splitlines()
    cols = next((l.split()[1:] for l in lines if l.startswith("Index")), None)
    if not cols:
        raise RuntimeError(f"could not parse {cmd[1]} hist output")
    hist, summ = {c: {} for c in cols}, {}
    for line in lines:
        f = line.split()
        if len(f) != len(cols) + 1:
            continue
        if f[0].isdigit():
            for c, n in zip(cols, f[1:]):
                hist[c][int(f[0])] = int(n)
        elif f[0] in ("over:", "count:", "avg:", "max:"):
            summ[f[0][:-1]] = dict(zip(cols, (float(x) for x in f[1:])))
    return cols, hist, summ

def _merge(cols, hist, summ):
    """One histogram over the given columns; samples past the last bucket clamp to ENTRIES."""
    h = {}
    for c in cols:
        for us, n in hist[c].items():
            h[us] = h.get(us, 0) + n
    if over := int(sum(summ.get("over", {}).get(c, 0) for c in cols)):
        h[ENTRIES] = h.get(ENTRIES, 0) + over
    return h

def bench_timerlat():
    _root()
    cols, hist, summ = _hist(["rtla", "timerlat", "hist", "-u", "-d", f"{DURATION}s", "-E", ENTRIES])
    # Only the user-thread latency is kept: it is what an application sees and already
    # contains the irq and kernel-thread legs. irq.* was identical across kernels (board
    # floor), avg barely moves, p99 is bimodal on non-RT; run rtla by hand to see the layers.
    h = _merge([c for c in cols if c.startswith("Usr")], hist, summ)
    # No max: the single worst event in 30 s never reproduces (n1 vs n3: 138 vs 110 with
    # p99.9 at 67 vs 66). p99.99 is the top ~12 of 120k samples, a tail that can still settle.
    return {"p99.9_us": (_pct(h, .999), "lower"),
            "p99.99_us": (_pct(h, .9999), "lower")}

def bench_osnoise():
    """noise_us: time stolen from the busy loops, summed over CPUs for the whole run
    (count x avg per CPU, exact). p99.9_single_us: p99.9 of single-interruption length.
    The old max_single/max_noise were one worst event per run and never reproduced; the
    hist needs CONFIG_HIST_TRIGGERS on top of CONFIG_OSNOISE_TRACER."""
    _root()
    cols, hist, summ = _hist(["rtla", "osnoise", "hist", "-d", f"{DURATION}s", "-E", ENTRIES])
    return {"noise_us": (sum(summ["count"][c] * summ["avg"][c] for c in cols), "lower"),
            "p99.9_single_us": (_pct(_merge(cols, hist, summ), .999), "lower")}

BENCHMARKS = {"timerlat": {"needs": "rtla", "fn": bench_timerlat},
              "osnoise": {"needs": "rtla", "fn": bench_osnoise}}

if __name__ == "__main__":
    main(BENCHMARKS)
