{
  config,
  pkgs,
  lib,
  ...
}:
let
  pythonVersion = lib.strings.trim (builtins.readFile ./.python-version);
  application = builtins.fromTOML (builtins.readFile ./pyproject.toml);
in
{
  assertions = [
    {
      assertion = pkgs.python315.version == pythonVersion;
      message = "The locked Nix Python must match .python-version.";
    }
    {
      assertion = application.tool.mypy.python_version == lib.versions.majorMinor pythonVersion;
      message = "Mypy's Python target must match .python-version.";
    }
    {
      assertion =
        application.tool.ruff.target-version
        == "py${lib.replaceStrings [ "." ] [ "" ] (lib.versions.majorMinor pythonVersion)}";
      message = "Ruff's Python target must match .python-version.";
    }
  ];

  languages.python = {
    enable = true;
    package = pkgs.python315;
    lsp.enable = false;
    uv = {
      enable = true;
      sync.enable = false;
    };
  };

  packages = [
    pkgs.nixfmt
    pkgs.actionlint
  ];
  dotenv.enable = false;
  env.UV_PROJECT_ENVIRONMENT = lib.mkForce "${config.devenv.root}/.venv";
  env.UV_NO_ENV_FILE = "1";

  tasks = {
    "app:install" = {
      description = "Install the CLI and locked development dependencies";
      wantedBy = [ ];
      exec = "uv sync --locked --all-groups --python ${config.languages.python.package}/bin/python";
    };

    "app:lint" = {
      description = "Check Python lint and formatting";
      wantedBy = [ ];
      after = [ "app:install" ];
      exec = ''
        uv run --no-sync ruff check .
        uv run --no-sync ruff format --check .
      '';
    };

    "app:typecheck" = {
      description = "Check Python types";
      wantedBy = [ ];
      after = [ "app:install" ];
      exec = "uv run --no-sync mypy";
    };

    "app:test" = {
      description = "Run the application and installed entry point tests";
      wantedBy = [ ];
      after = [ "app:install" ];
      exec = "uv run --no-sync pytest";
    };

    "app:config-check" = {
      description = "Check Nix formatting and GitHub workflow syntax";
      wantedBy = [ ];
      exec = ''
        nixfmt --check flake.nix devenv.nix
        actionlint
      '';
    };

    "app:nix-check" = {
      description = "Build and exercise the standalone Nix CLI package";
      wantedBy = [ ];
      exec = "nix flake check --impure --no-update-lock-file";
    };

    "app:check" = {
      description = "Run all quality gates before packaging";
      wantedBy = [ ];
      after = [
        "app:lint"
        "app:typecheck"
        "app:test"
        "app:config-check"
        "app:nix-check"
      ];
    };

    "app:build" = {
      description = "Build the source archive and its wheel using the locked backend";
      wantedBy = [ ];
      after = [ "app:check" ];
      exec = ''
        rm -rf dist
        uv run --no-sync python -m build --no-isolation
      '';
    };

    "app:verify" = {
      description = "Install the built wheel and test it outside the checkout";
      wantedBy = [ ];
      after = [ "app:build" ];
      exec = ''
        export VERIFY_DIR=$(mktemp -d)
        trap 'rm -rf "''${VERIFY_DIR}"' EXIT
        uv export --locked --all-groups --no-emit-project --output-file "''${VERIFY_DIR}/requirements.txt"
        uv venv --python ${config.languages.python.package}/bin/python "''${VERIFY_DIR}/venv"
        uv pip sync --python "''${VERIFY_DIR}/venv/bin/python" --require-hashes "''${VERIFY_DIR}/requirements.txt"
        uv run --no-sync python scripts/verify_artifact.py "''${VERIFY_DIR}"
      '';
    };

    "app:ci" = {
      description = "Validate, package, and verify the installable Python CLI";
      wantedBy = [ "devenv:enterTest" ];
      before = [ "devenv:enterTest" ];
      after = [ "app:verify" ];
    };
  };
}
