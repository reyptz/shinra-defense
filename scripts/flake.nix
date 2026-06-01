{
  description = "Shinra Defense - Active Defense Platform";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay.url = "github:oxalica/rust-overlay";
    rust-overlay.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, rust-overlay, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };
        
        rustToolchain = pkgs.rust-bin.stable.latest.default.override {
          extensions = [ "rust-src" "rust-analyzer" "rustfmt" "clippy" ];
        };
        
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          fastapi
          uvicorn
          sqlalchemy
          chromadb
          sentence-transformers
          celery
          redis
          docker
          websockets
          pydantic
          aiofiles
          httpx
          numpy
        ]);
        
        buildInputs = with pkgs; [
          rustToolchain
          pythonEnv
          clang
          llvm
          libelf
          libbpf
          docker
          podman
          sqlite
        ];
        
        nativeBuildInputs = with pkgs; [
          pkg-config
          rustToolchain
        ];
      in {
        devShells.default = pkgs.mkShell {
          inherit buildInputs nativeBuildInputs;
          
          shellHook = ''
            echo "Shinra Defense Development Environment"
            echo "Rust: $(rustc --version)"
            echo "Python: $(python --version)"
            
            export RUSTFLAGS="-C link-arg=-fuse-ld=lld"
            export PYTHONPATH="${pythonEnv}/lib/python3.11/site-packages:$PYTHONPATH"
          '';
        };
        
        packages = {
          shinra-agent = pkgs.rustPlatform.buildRustPackage {
            pname = "shinra-agent";
            version = "0.1.0";
            src = ./../src-agent;
            cargoLock = ./../src-agent/Cargo.lock;
            nativeBuildInputs = nativeBuildInputs;
            buildInputs = buildInputs;
          };
          
          shinra-engine = pkgs.python311Packages.buildPythonPackage {
            pname = "shinra-engine";
            version = "0.1.0";
            src = ./../src-engine;
            propagatedBuildInputs = with pkgs.python311Packages; [
              fastapi
              uvicorn
              sqlalchemy
              chromadb
              sentence-transformers
              celery
              redis
              docker
              websockets
              pydantic
              aiofiles
              httpx
              numpy
            ];
          };
        };
      }
    );
}
