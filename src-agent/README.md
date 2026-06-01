# Shinra Defense Agent (Rust)

eBPF-based detection and response agent for the Shinra Defense platform.

## Architecture

- **eBPF Programs**: Kernel-level syscall monitoring (openat, read, connect)
- **Memory Scraper**: Pattern-matching for cryptographic key detection (AES/RSA)
- **Kill-Switch**: Process termination via SIGKILL
- **Honeypot Monitor**: Tracks suspicious activity on honeypot targets

## Requirements

- Rust 1.70+
- Linux kernel 5.5+ (for eBPF support)
- clang/llvm for BPF compilation
- libbpf development headers

## Installation

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install dependencies (Ubuntu/Debian)
sudo apt-get install -y build-essential clang llvm libelf-dev libbpf-dev

# Build the project
cargo build --release
```

## Usage

```bash
# Run the agent with root privileges (required for eBPF)
sudo ./target/release/shinra-agent
```

## Components

### eBPF Programs

Located in `ebpf/` directory:
- `main.bpf.c`: eBPF program for syscall monitoring
- `vmlinux.h`: Kernel type definitions

### User-Space Agent

Located in `src/` directory:
- `main.rs`: Main agent implementation with event processing

## Features

1. **Syscall Monitoring**: Tracks openat, read, and connect syscalls
2. **Honeypot Detection**: Identifies activity on honeypot targets
3. **Memory Scraping**: Extracts cryptographic keys from process memory
4. **Automatic Termination**: Kills suspicious processes after threshold
5. **Artifact Extraction**: Sends extracted artifacts to Python engine

## Configuration

Edit `src/main.rs` to configure:
- Honeypot target paths
- Suspicious activity threshold
- Memory dump settings
