{
  description = "Newspaper3kli Python CLI development and CI environment";

  nixConfig = {
    extra-substituters = [ "https://devenv.cachix.org" ];
    extra-trusted-public-keys = [
      "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv = {
      url = "github:cachix/devenv/v2.4.0";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      devenv,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      ...
    }@inputs:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
      pythonSets = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        (pkgs.callPackage pyproject-nix.build.packages { python = pkgs.python315; }).overrideScope (
          nixpkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.wheel
            (workspace.mkPyprojectOverlay { sourcePreference = "wheel"; })
            (final: prev: {
              # PyYAML has no wheel for every declared Python/platform combination.
              pyyaml = prev.pyyaml.overrideAttrs (old: {
                nativeBuildInputs =
                  (old.nativeBuildInputs or [ ])
                  ++ final.resolveBuildSystem {
                    setuptools = [ ];
                    cython = [ ];
                  };
                buildInputs = (old.buildInputs or [ ]) ++ [ pkgs.libyaml ];
              });
            })
          ]
        )
      );
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          environment = pythonSets.${system}.mkVirtualEnv "newspaper3kli-env" workspace.deps.default;
          application = pkgs.writeShellApplication {
            name = "newspaper3kli";
            text = ''exec ${environment}/bin/newspaper3kli "$@"'';
          };
        in
        {
          default = application;
          newspaper3kli = application;
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/newspaper3kli";
          meta.description = "Download and extract articles with Newspaper3kli";
        };
      });

      checks = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          testEnvironment = pythonSets.${system}.mkVirtualEnv "newspaper3kli-test-env" (
            workspace.deps.default
            // {
              pytest = [ ];
              pytest-asyncio = [ ];
            }
          );
        in
        {
          cli = pkgs.runCommand "newspaper3kli-install-check" { } ''
            ${self.packages.${system}.default}/bin/newspaper3kli --help
            cp -r ${./tests} tests
            cp ${./pyproject.toml} pyproject.toml
            ${testEnvironment}/bin/python -I -m pytest
            touch "$out"
          '';
        }
      );

      devShells = forAllSystems (system: {
        default = devenv.lib.mkShell {
          inherit inputs;
          pkgs = nixpkgs.legacyPackages.${system};
          modules = [ ./devenv.nix ];
        };
      });

      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt);
    };
}
