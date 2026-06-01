/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/* This is a minimal vmlinux.h for eBPF programs */
#ifndef __VMLINUX_H__
#define __VMLINUX_H__

#include <linux/types.h>

#define __user
#define __kernel

struct trace_event_raw_sys_enter {
    unsigned short type;
    unsigned char flags;
    unsigned char preempt_count;
    int pid;
    void *args[6];
};

#endif /* __VMLINUX_H__ */
