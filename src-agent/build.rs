use aya_build::BpfBuilder;

fn main() {
    BpfBuilder::new()
        .cargo_linker()
        .source_file("ebpf/main.bpf.c")
        .generate()
        .expect("Failed to build BPF program");
}
