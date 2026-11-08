"""Block layer with nothing behind it: fio 4k random reads on /dev/nullb0
(CONFIG_BLK_DEV_NULL_BLK=y gives one device at boot). qd1 = per-request submit/complete
latency, qd32 = batched single queue, qd32 x N jobs = blk-mq across every CPU. Needs root."""
import json
from pathlib import Path
from common import NPROC, run_bench, main

DEV = Path("/dev/nullb0")

def bench_bio():
    if not DEV.exists():
        raise RuntimeError("no /dev/nullb0 (kernel needs CONFIG_BLK_DEV_NULL_BLK=y)")
    out = {}
    for name, extra in [("qd1",  ["--iodepth=1"]),
                        ("qd32", ["--iodepth=32"]),
                        (f"qd32-{NPROC}j", ["--iodepth=32", f"--numjobs={NPROC}"])]:
        r = run_bench(["fio", "--name", name, f"--filename={DEV}", "--rw=randread", "--bs=4k",
                       "--direct=1", "--ioengine=io_uring", "--runtime=10", "--time_based",
                       "--group_reporting", "--output-format=json"] + extra)
        side = json.loads(r.stdout)["jobs"][0]["read"]
        out[f"{name}.iops"] = (side["iops"], "higher")
        if name == "qd1":
            out["qd1.p99_lat_us"] = (side["clat_ns"]["percentile"]["99.000000"] / 1000, "lower")
    return out

BENCHMARKS = {"bio": {"needs": "fio", "fn": bench_bio}}

if __name__ == "__main__":
    main(BENCHMARKS)
