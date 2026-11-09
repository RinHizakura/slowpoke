# slowpoke

Run a set of kernel benchmarks and compare results across kernel versions and platforms.

Latest report: <https://rinhizakura.github.io/slowpoke/>

## Usage

```sh
./slowpoke.py run                  # all benchmarks -> data/runs/results.json
./slowpoke.py run --output rpi4    # per-platform data dir -> data/rpi4/ (results.json, hw.json, configs/)
./slowpoke.py list --output rpi4   # list saved runs
./slowpoke.py rm <run> --output rpi4
python3 -m http.server            # view report locally at http://localhost:8000
```

Each benchmark lives in `workload/<name>.py`. Run one directly to execute it once and
print its metrics without saving anything (e.g. `sudo python3 workload/perf-pipe.py`,
`python3 workload/schbench.py schbench-light`).

Each run also records `sysinfo` (kernel, cmdline, `/proc/version`, governor, THP mode,
preempt mode when debugfs is readable, 1/5/15-min loadavg at suite start, config hash, `rt` for PREEMPT_RT kernels, kernel boot time from `systemd-analyze`) and rewrites
`hw.json` (board, cpus, memory, caches, the filesystem/device under the repo that fio writes to).
The report's RT/non-RT series split uses `sysinfo.rt`.

## Benchmarks

| name       | needs       | measures                                                                 |
|------------|-------------|--------------------------------------------------------------------------|
| fio        | fio         | block I/O: 4k rand r/w IOPS + p99 lat, 1M seq throughput, 4k fsync write |
| schbench   | schbench    | heavy (2x oversubscribed): rps + req p99 latency; light (N/2 workers): wake p99 latency |
| memory-256k | sysbench   | cache-regime memory bandwidth, read/write MiB/s (256K blocks)            |
| memory-64m | sysbench    | DRAM-regime memory bandwidth, read/write MiB/s (64M blocks)              |
| net        | iperf3      | loopback TCP Gbps (plain + zero-copy), 64B UDP pps (1 + N streams); 10 s steady state after a 2 s warm-up, 10 reps |
| syscall    | perf        | syscall entry/exit overhead                                              |
| ipc        | perf        | scheduler+IPC throughput (hackbench-style)                               |
| perf-pipe  | perf       | pinned pipe ping-pong wakeup cost from the root cgroup and 16 cpu-cgroup levels deep (creates cgroups, so run as root) |
| timerlat   | rtla        | 1ms timer wakeup latency as seen by a user thread: p99.9 and p99.99 over all samples (tracefs, so run as root; kernel needs CONFIG_TIMERLAT_TRACER) |
| osnoise    | rtla        | OS noise stolen from a busy loop on every CPU: total us, p99.9 of single-interruption length (root; CONFIG_OSNOISE_TRACER + CONFIG_HIST_TRIGGERS) |
| pagefault  | stress-ng   | page-fault rate                                                          |
| fork       | stress-ng   | fork/exec rate                                                           |
| mmap       | stress-ng   | mmap + touch + munmap of 8M per op: VMA setup/teardown rate; 10 reps (in-run CV ~8%) |
| timerfd    | stress-ng   | timerfd arm/expire/read rate (hrtimer path)                              |
| dentry     | stress-ng   | create/unlink dentries on tmpfs: vfs + dcache rate, no disk              |
| futex      | perf        | futex hash (uncontended wait/wake) and lock-pi (contended PI lock, the rtmutex path) ops/s |
| epoll      | perf        | epoll wait: waiter threads woken through epoll, ops/s                    |
| timerlat-load | rtla + stress-ng | timerlat at FIFO 90 while stress-ng hogs every CPU and churns memory: latency under load (root) |
| bio        | fio         | 4k random reads on /dev/nullb0, the block layer with no media: qd1 IOPS + p99 lat, qd32, qd32 x N jobs (root; CONFIG_BLK_DEV_NULL_BLK=y) |

