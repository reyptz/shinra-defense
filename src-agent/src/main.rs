use aya::{include_bytes_aligned, Bpf, programs::KProbe};
use aya_log::BpfLogger;
use anyhow::Context;
use bytes::Bytes;
use log::{info, warn, error};
use nix::sys::signal::{self, Signal};
use nix::unistd::Pid;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::mpsc;
use tokio::sync::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct EbpfEvent {
    pid: u32,
    uid: u32,
    comm: String,
    filename: String,
    timestamp: u64,
    syscall_type: u32, // 0: openat, 1: read, 2: connect
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct MemoryArtifact {
    pid: u32,
    artifact_type: String,
    value: String,
    confidence: f32,
}

#[derive(Debug, Clone)]
struct ProcessInfo {
    pid: u32,
    suspicious_count: u32,
    last_activity: u64,
}

// Memory scraper for cryptographic key detection
struct MemoryScraper {
    aes_pattern: Regex,
    rsa_pattern: Regex,
}

impl MemoryScraper {
    fn new() -> Self {
        // AES key patterns (256-bit = 64 hex chars)
        let aes_pattern = Regex::new(r"[0-9a-fA-F]{64}").unwrap();
        // RSA key patterns (larger hex strings)
        let rsa_pattern = Regex::new(r"[0-9a-fA-F]{256,}").unwrap();
        
        MemoryScraper {
            aes_pattern,
            rsa_pattern,
        }
    }

    fn scan_memory(&self, data: &[u8]) -> Vec<MemoryArtifact> {
        let mut artifacts = Vec::new();
        let hex_str = hex::encode(data);
        
        // Scan for AES keys
        for mat in self.aes_pattern.find_iter(&hex_str) {
            artifacts.push(MemoryArtifact {
                pid: 0, // Will be set by caller
                artifact_type: "AES-256".to_string(),
                value: mat.as_str().to_string(),
                confidence: 0.95,
            });
        }
        
        // Scan for RSA keys
        for mat in self.rsa_pattern.find_iter(&hex_str) {
            artifacts.push(MemoryArtifact {
                pid: 0,
                artifact_type: "RSA".to_string(),
                value: mat.as_str().to_string(),
                confidence: 0.90,
            });
        }
        
        artifacts
    }
}

// Kill-switch for process termination
struct KillSwitch;

impl KillSwitch {
    fn terminate_process(pid: u32) -> anyhow::Result<()> {
        let nix_pid = Pid::from_raw(pid as i32);
        signal::kill(nix_pid, Signal::SIGKILL)
            .context(format!("Failed to kill process {}", pid))?;
        info!("Process {} terminated via SIGKILL", pid);
        Ok(())
    }
}

// Honeypot target monitoring
struct HoneypotMonitor {
    targets: Vec<String>,
    suspicious_processes: Arc<RwLock<HashMap<u32, ProcessInfo>>>,
}

impl HoneypotMonitor {
    fn new(targets: Vec<String>) -> Self {
        HoneypotMonitor {
            targets,
            suspicious_processes: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    fn is_honeypot_target(&self, path: &str) -> bool {
        self.targets.iter().any(|target| path.contains(target))
    }

    async fn track_suspicious_activity(&self, pid: u32) -> bool {
        let mut processes = self.suspicious_processes.write().await;
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let process_info = processes.entry(pid).or_insert(ProcessInfo {
            pid,
            suspicious_count: 0,
            last_activity: now,
        });
        
        process_info.suspicious_count += 1;
        process_info.last_activity = now;
        
        // Threshold for automatic termination
        process_info.suspicious_count >= 5
    }
}

// Memory dump functionality
fn dump_process_memory(pid: u32) -> anyhow::Result<Vec<u8>> {
    let mem_path = format!("/proc/{}/mem", pid);
    let maps_path = format!("/proc/{}/maps", pid);
    
    if !Path::new(&mem_path).exists() {
        return Err(anyhow::anyhow!("Process {} does not exist", pid));
    }
    
    // Read memory maps to identify readable regions
    let maps_content = fs::read_to_string(&maps_path)
        .context("Failed to read memory maps")?;
    
    let mut memory_data = Vec::new();
    
    for line in maps_content.lines() {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() < 2 {
            continue;
        }
        
        let range: Vec<&str> = parts[0].split('-').collect();
        if range.len() != 2 {
            continue;
        }
        
        let start_addr = u64::from_str_radix(range[0], 16)
            .unwrap_or(0);
        let end_addr = u64::from_str_radix(range[1], 16)
            .unwrap_or(0);
        
        let size = end_addr - start_addr;
        if size > 10 * 1024 * 1024 { // Skip regions larger than 10MB
            continue;
        }
        
        // In a real implementation, we would read from /proc/pid/mem
        // For now, we'll simulate this
        // memory_data.extend_from_slice(&vec![0u8; size as usize]);
    }
    
    Ok(memory_data)
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    env_logger::init();
    
    info!("Starting Shinra Defense Agent...");
    
    // Initialize honeypot monitor with target paths
    let honeypot_targets = vec![
        "/honeypot/smb".to_string(),
        "/honeypot/ssh".to_string(),
        "/honeypot/http".to_string(),
    ];
    let monitor = HoneypotMonitor::new(honeypot_targets);
    let monitor = Arc::new(monitor);
    
    // Initialize memory scraper
    let scraper = MemoryScraper::new();
    
    // Load eBPF program
    let mut bpf = Bpf::load(include_bytes_aligned!("../../target/bpfel-unknown-none/release/shinra-agent.bpf.o"))?;
    if let Err(e) = BpfLogger::init(&mut bpf) {
        warn!("Failed to initialize eBPF logger: {}", e);
    }
    
    // Attach eBPF programs
    let program: &mut KProbe = bpf.program_mut("sys_enter_openat")?.try_into()?;
    program.load()?;
    program.attach("sys_openat", 0)?;
    info!("Attached sys_enter_openat probe");
    
    let program: &mut KProbe = bpf.program_mut("sys_enter_read")?.try_into()?;
    program.load()?;
    program.attach("sys_read", 0)?;
    info!("Attached sys_enter_read probe");
    
    let program: &mut KProbe = bpf.program_mut("sys_enter_connect")?.try_into()?;
    program.load()?;
    program.attach("sys_connect", 0)?;
    info!("Attached sys_enter_connect probe");
    
    // Create channel for event processing
    let (tx, mut rx) = mpsc::channel::<EbpfEvent>(1000);
    
    // Spawn event processor
    let monitor_clone = Arc::clone(&monitor);
    tokio::spawn(async move {
        while let Some(event) = rx.recv().await {
            info!("Received eBPF event: PID={}, syscall={}, file={}", 
                event.pid, event.syscall_type, event.filename);
            
            // Check if event targets honeypot
            if monitor_clone.is_honeypot_target(&event.filename) {
                warn!("Suspicious activity detected on honeypot: PID={}, file={}", 
                    event.pid, event.filename);
                
                // Track suspicious activity
                let should_terminate = monitor_clone.track_suspicious_activity(event.pid).await;
                
                if should_terminate {
                    warn!("Terminating suspicious process: PID={}", event.pid);
                    if let Err(e) = KillSwitch::terminate_process(event.pid) {
                        error!("Failed to terminate process: {}", e);
                    }
                    
                    // Perform memory dump before termination
                    if let Ok(memory) = dump_process_memory(event.pid) {
                        let artifacts = scraper.scan_memory(&memory);
                        for artifact in artifacts {
                            info!("Extracted artifact: type={}, confidence={}", 
                                artifact.artifact_type, artifact.confidence);
                            // In real implementation, send to Python engine
                        }
                    }
                }
            }
        }
    });
    
    // Main event loop
    info!("Shinra Defense Agent running. Press Ctrl+C to stop.");
    
    // Simulate event processing (in real implementation, this would read from ring buffer)
    tokio::signal::ctrl_c().await?;
    info!("Shutting down...");
    
    Ok(())
}
