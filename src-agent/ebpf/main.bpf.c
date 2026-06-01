// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
/* Copyright (c) 2026 Shinra Defense */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define MAX_FILENAME_LEN 256
#define MAX_COMM_LEN 16

struct event_t {
    __u32 pid;
    __u32 uid;
    char comm[MAX_COMM_LEN];
    char filename[MAX_FILENAME_LEN];
    __u64 timestamp;
    __u32 syscall_type; // 0: openat, 1: read, 2: connect
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

// Monitor openat syscalls
SEC("syscalls/sys_enter_openat")
int sys_enter_openat(struct trace_event_raw_sys_enter *ctx)
{
    struct event_t e = {};
    __u64 id = bpf_get_current_pid_tgid();
    e.pid = id >> 32;
    e.uid = bpf_get_current_uid_gid();
    e.timestamp = bpf_ktime_get_ns();
    e.syscall_type = 0;

    bpf_get_current_comm(&e.comm, sizeof(e.comm));

    // Read filename from syscall arguments
    void *filename_ptr = (void *)BPF_CORE_READ(ctx, args[2]);
    bpf_probe_read_user_str(&e.filename, sizeof(e.filename), filename_ptr);

    bpf_ringbuf_output(&events, &e, sizeof(e), 0);
    return 0;
}

// Monitor read syscalls
SEC("syscalls/sys_enter_read")
int sys_enter_read(struct trace_event_raw_sys_enter *ctx)
{
    struct event_t e = {};
    __u64 id = bpf_get_current_pid_tgid();
    e.pid = id >> 32;
    e.uid = bpf_get_current_uid_gid();
    e.timestamp = bpf_ktime_get_ns();
    e.syscall_type = 1;

    bpf_get_current_comm(&e.comm, sizeof(e.comm));

    bpf_ringbuf_output(&events, &e, sizeof(e), 0);
    return 0;
}

// Monitor connect syscalls (network activity)
SEC("syscalls/sys_enter_connect")
int sys_enter_connect(struct trace_event_raw_sys_enter *ctx)
{
    struct event_t e = {};
    __u64 id = bpf_get_current_pid_tgid();
    e.pid = id >> 32;
    e.uid = bpf_get_current_uid_gid();
    e.timestamp = bpf_ktime_get_ns();
    e.syscall_type = 2;

    bpf_get_current_comm(&e.comm, sizeof(e.comm));

    bpf_ringbuf_output(&events, &e, sizeof(e), 0);
    return 0;
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";
