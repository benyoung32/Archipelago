#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import glob
import json
import os
import pathlib
import shutil
import subprocess
import sys
import zipfile


def log(msg: str, prefix: str = "[*]") -> None:
    print(f"\033[1;34m{prefix}\033[0m {msg}")


def log_success(msg: str) -> None:
    print(f"\033[1;32m[+]\033[0m {msg}")


def log_error(msg: str) -> None:
    print(f"\033[1;31m[-]\033[0m {msg}", file=sys.stderr)


def get_default_ap_dir() -> pathlib.Path:
    # 1. Environment variable if set
    if "ARCHIPELAGO_INSTALL" in os.environ:
        return pathlib.Path(os.environ["ARCHIPELAGO_INSTALL"]).resolve()
    # 2. Standard ProgramData installation on Windows
    program_data_ap = pathlib.Path(r"C:\ProgramData\Archipelago")
    if program_data_ap.is_dir():
        return program_data_ap
    # 3. User home directory fallback
    home_ap = pathlib.Path.home() / "Archipelago"
    if home_ap.is_dir():
        return home_ap
    return program_data_ap


def build_apworld(world_dir: pathlib.Path, output_path: pathlib.Path) -> pathlib.Path:
    log("Building insaniquarium.apworld...")

    manifest_file = world_dir / "archipelago.json"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_file}")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Required APContainer version tags
    manifest["version"] = 7
    manifest["compatible_version"] = 7

    # Ensure data package has __init__.py so zipimport treats it as a module
    data_init = world_dir / "data" / "__init__.py"
    if not data_init.is_file():
        with open(data_init, "w", encoding="utf-8") as f:
            f.write('"""Data package for Insaniquarium Deluxe world."""\n')

    # Read ignore patterns
    ignore_patterns = [
        "__pycache__", "*.pyc", "test", "test/*", "*.yaml", ".git*",
        "APDefinitions.h", "generate_data.py", ".apignore", "build_insaniquarium.*",
        "release_insaniquarium.*", "*.ps1",
    ]
    apignore_file = world_dir / ".apignore"
    if apignore_file.is_file():
        with open(apignore_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignore_patterns.append(line.rstrip("/"))

    def is_ignored(rel_p: pathlib.Path) -> bool:
        parts = rel_p.parts
        posix = rel_p.as_posix()
        for pat in ignore_patterns:
            if any(fnmatch.fnmatch(part, pat) for part in parts):
                return True
            if fnmatch.fnmatch(posix, pat) or fnmatch.fnmatch(posix, f"*/{pat}"):
                return True
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")

    added_files = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # Write root manifest and world-prefixed manifest
        zf.writestr("archipelago.json", manifest_bytes)
        zf.writestr("insaniquarium/archipelago.json", manifest_bytes)

        for file_path in world_dir.rglob("*"):
            if file_path.is_file():
                rel = file_path.relative_to(world_dir)
                if rel.as_posix() == "archipelago.json":
                    continue
                if not is_ignored(rel):
                    arcname = f"insaniquarium/{rel.as_posix()}"
                    zf.write(file_path, arcname)
                    added_files += 1

    log_success(f"Built {output_path.name} ({added_files} files, {output_path.stat().st_size:,} bytes)")
    return output_path


def swap_into_launcher(apworld_path: pathlib.Path, ap_dir: pathlib.Path) -> None:
    log(f"Swapping APWorld into Archipelago Launcher at {ap_dir}...")

    custom_worlds_dir = ap_dir / "custom_worlds"
    custom_worlds_dir.mkdir(parents=True, exist_ok=True)

    dest_apworld = custom_worlds_dir / apworld_path.name
    shutil.copy2(apworld_path, dest_apworld)
    log_success(f"Installed to {dest_apworld}")


def generate_templates(ap_dir: pathlib.Path, repo_root: pathlib.Path, world_dir: pathlib.Path) -> pathlib.Path:
    log("Generating template options using Options.generate_yaml_templates...")

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    import tempfile
    from Options import generate_yaml_templates
    from worlds.AutoWorld import AutoWorldRegister

    game_name = "Insaniquarium Deluxe"
    if game_name not in AutoWorldRegister.world_types:
        import importlib
        importlib.import_module("worlds.insaniquarium")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # Restrict to Insaniquarium Deluxe so other unconfigured/broken worlds don't block generation
        old_world_types = AutoWorldRegister.world_types
        if game_name in AutoWorldRegister.world_types:
            AutoWorldRegister.world_types = {game_name: old_world_types[game_name]}
        try:
            generate_yaml_templates(temp_path, generate_hidden=True)
        finally:
            AutoWorldRegister.world_types = old_world_types

        generated_file = temp_path / f"{game_name}.yaml"
        if not generated_file.is_file():
            raise FileNotFoundError(
                f"Expected template '{game_name}.yaml' was not generated in {temp_path}."
            )

        # 1. Copy into Archipelago Templates directory
        templates_dir = ap_dir / "Players" / "Templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        dest_template = templates_dir / f"{game_name}.yaml"
        shutil.copy2(generated_file, dest_template)
        log_success(f"Updated template options in Archipelago at {dest_template}")

        # 2. Copy into workspace
        workspace_yaml = world_dir / "Insaniquarium.yaml"
        shutil.copy2(generated_file, workspace_yaml)
        log_success(f"Updated workspace template at {workspace_yaml}")

        # 3. Copy any generated presets
        temp_presets = temp_path / "Presets"
        if temp_presets.is_dir():
            ap_presets = templates_dir / "Presets"
            workspace_presets = world_dir / "Presets"
            for preset in temp_presets.glob(f"{game_name} - *.yaml"):
                ap_presets.mkdir(parents=True, exist_ok=True)
                workspace_presets.mkdir(parents=True, exist_ok=True)
                shutil.copy2(preset, ap_presets / preset.name)
                shutil.copy2(preset, workspace_presets / preset.name)
                log_success(f"Synchronized preset: {preset.name}")

    return dest_template


def run_generation(ap_dir: pathlib.Path, yaml_to_use: pathlib.Path, repo_root: pathlib.Path) -> None:
    log(f"Running Archipelago generation with {yaml_to_use.name}...")

    if not yaml_to_use.is_file():
        raise FileNotFoundError(f"Player YAML not found: {yaml_to_use}")

    # Prepare isolated generation folder for solo roll
    solo_dir = ap_dir / "Players" / "_solo_insaniquarium"
    if solo_dir.exists():
        shutil.rmtree(solo_dir)
    solo_dir.mkdir(parents=True, exist_ok=True)

    dest_yaml = solo_dir / "Insaniquarium.yaml"
    shutil.copy2(yaml_to_use, dest_yaml)

    generate_exe = ap_dir / "ArchipelagoGenerate.exe"
    output_dir = ap_dir / "output"

    # Track output folder state to find newly created archive
    before_files = set(glob.glob(str(output_dir / "AP_*.zip"))) if output_dir.is_dir() else set()

    if generate_exe.is_file():
        cmd = [str(generate_exe), "--player_files_path", str(solo_dir)]
    else:
        # Fallback to source Generate.py if frozen executable is not present
        cmd = [sys.executable, str(repo_root / "Generate.py"), "--player_files_path", str(solo_dir)]

    log(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, input="\n", text=True, capture_output=True)

    # Print relevant generation lines
    lines = result.stdout.splitlines()
    for line in lines:
        if any(keyword in line for keyword in [
            "Generating for", "Seed", "World Types", "Insaniquarium Deluxe",
            "Filling", "output files", "archive at", "Done."
        ]):
            print(f"  \033[2m{line}\033[0m")

    if result.returncode != 0 and "Done. Enjoy." not in result.stdout:
        log_error("Generation failed!")
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode or 1)

    # Identify output zip
    after_files = set(glob.glob(str(output_dir / "AP_*.zip"))) if output_dir.is_dir() else set()
    new_files = sorted(after_files - before_files, key=os.path.getmtime)
    if not new_files and after_files:
        new_files = [sorted(after_files, key=os.path.getmtime)[-1]]

    if new_files:
        latest_zip = pathlib.Path(new_files[-1])
        log_success(f"Generated seed archive: {latest_zip.name}")
        print(f"       Path: {latest_zip}")

        # Verify apinsani inside
        with zipfile.ZipFile(latest_zip, "r") as zf:
            apinsani_files = [f for f in zf.namelist() if f.endswith(".apinsani")]
            for apinsani in apinsani_files:
                print(f"       \033[1;32m[+]\033[0m Included container: {apinsani}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Insaniquarium APWorld, deploy to Archipelago Launcher, and run generation."
    )
    parser.add_argument(
        "--ap-dir",
        type=pathlib.Path,
        default=get_default_ap_dir(),
        help="Path to Archipelago installation (default: C:\\ProgramData\\Archipelago)",
    )
    parser.add_argument(
        "--yaml",
        type=pathlib.Path,
        default=None,
        help="Optional path to custom player YAML to generate with (default: auto-generated template)",
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Build, deploy, and generate templates without running seed generation.",
    )

    args = parser.parse_args()

    # Determine paths based on location of this script in worlds/insaniquarium
    world_dir = pathlib.Path(__file__).resolve().parent
    repo_root = world_dir.parent.parent

    build_output = repo_root / "build" / "apworlds" / "insaniquarium.apworld"

    print("\033[1;36m==================================================\033[0m")
    print("\033[1;36m   Insaniquarium APWorld: Build & Generate  \033[0m")
    print("\033[1;36m==================================================\033[0m")

    # 1. Build .apworld
    build_apworld(world_dir, build_output)

    # 2. Swap into Launcher
    swap_into_launcher(build_output, args.ap_dir)

    # 3. Auto-generate template options using Options.generate_yaml_templates and sync
    generated_template = generate_templates(args.ap_dir, repo_root, world_dir)

    # 4. Run Generation
    if not args.skip_generate:
        yaml_to_use = args.yaml if args.yaml else generated_template
        run_generation(args.ap_dir, yaml_to_use, repo_root)

    print("\033[1;32m==================================================\033[0m")
    print("\033[1;32m   Completed successfully!          \033[0m")
    print("\033[1;32m==================================================\033[0m")


if __name__ == "__main__":
    main()

