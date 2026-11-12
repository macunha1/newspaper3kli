# Newspaper3kli installation with Nix

Nix supplies Python and the CLI's dependencies, so no system Python or activated
virtual environment is required. Install Nix with flakes and `nix-command` enabled.

For installation with Python and pip alone, see [the pip guide](pip-install.md).

## Install and run

```bash
git clone https://github.com/macunha1/newspaper3kli.git
cd newspaper3kli
nix run --no-update-lock-file . -- --help
nix profile install .
newspaper3kli --help
```

`nix run` runs the CLI directly. Installing it into your profile makes
`newspaper3kli` available from any directory. Ensure your Nix profile's `bin`
directory is on `PATH` (normally configured by the Nix installer).

With the CLI installed:

```bash
newspaper3kli --output articles https://example.com/article
cat urls.txt | newspaper3kli --output articles --concurrency 8
```

See the [README](../README.md) for options, output files, and exit codes.

## Build without installing

```bash
nix build --no-update-lock-file
./result/bin/newspaper3kli --help
```

This creates a `result` link to the package without adding it to your profile.

## Requirements and downloads

Configurations are available for `x86_64-linux`, `aarch64-linux`, and
`aarch64-darwin`. Installation downloads the pinned tools and dependencies and
may build packages that are not available from a binary cache.

Review the flake's binary cache settings if Nix prompts for approval. A multi-user
Nix installation may require its administrator to configure trust for that cache.
The default official Nix cache remains enabled.
