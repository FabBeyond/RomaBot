{
  description = "RomaBot dev environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {inherit system;};
    in {
      devShells.default = pkgs.mkShell {
        packages = [
          pkgs.python311
          pkgs.python311Packages.pip
          pkgs.pyright
          pkgs.ruff
        ];

        shellHook = ''
          [ -d .venv ] || python -m venv .venv
          source .venv/bin/activate
          pip install -q -r requirements.txt
          echo "RomaBot dev shell (venv) — python: $(python --version)"
        '';
      };
    });
}
