#!/usr/bin/env python3
"""Install veraPDF headless by driving its izpack console installer via a pty.

Why this exists: veraPDF only ships binaries as an izpack GUI installer zip
(https://software.verapdf.org/rel/verapdf-installer.zip). There is no fat jar on
Maven Central, no `apt`/`brew`/`snap` package, and no GitHub Release with a
direct download. Izpack has a `-console` mode but its mixed line/char prompts
race against piped stdin, so a pty is the reliable path.

Usage:
    python3 install_verapdf_headless.py [--target DIR] [--version VERSION]

Defaults: ~/.local/opt/verapdf , latest release.

After install, run `~/.local/opt/verapdf/verapdf --version` to verify. The
installer leaves a 16 MB shaded jar at bin/cli-<ver>.jar; the `verapdf`
wrapper script invokes `java -jar` on it.
"""
import argparse
import os
import pty
import select
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path


INSTALLER_URL = "https://software.verapdf.org/rel/verapdf-installer.zip"


def download_installer(dest: Path) -> Path:
    print(f"Downloading veraPDF installer from {INSTALLER_URL} ...", flush=True)
    with urllib.request.urlopen(INSTALLER_URL) as r, dest.open("wb") as f:
        shutil.copyfileobj(r, f)
    size_mb = dest.stat().st_size / 1_000_000
    print(f"  -> {dest} ({size_mb:.1f} MB)", flush=True)
    return dest


def extract_installer(zip_path: Path, workdir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(workdir)
    inner = next(p for p in workdir.iterdir() if p.is_dir() and p.name.startswith("verapdf-greenfield-"))
    jar = next(inner.glob("verapdf-izpack-installer-*.jar"))
    print(f"Installer jar: {jar.name}", flush=True)
    return jar


def run_installer(jar: Path, target: Path, timeout: int = 180) -> None:
    """Drive the izpack console installer via a pty, selecting ONLY the CLI pack."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp("java", ["java", "-jar", str(jar), "-console"])

    buf = ""
    state = {
        "welcome": False,
        "info": False,
        "path": False,
        "create": False,
        "packs_sent": 0,
        "packs_confirm": False,
        "install_confirm": False,
    }
    pack_answers = ["N", "Y", "N", "N"]  # GUI, CLI, Docs, Plugins
    deadline = time.time() + timeout

    def send(s: str) -> None:
        print(f"  [send] {s!r}", flush=True)
        os.write(fd, (s + "\n").encode())

    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], 0.5)
        if not r:
            continue
        try:
            chunk = os.read(fd, 4096).decode(errors="replace")
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
        tail = buf[-800:]
        if "Press 1 to continue" in tail and not state["welcome"]:
            time.sleep(0.3); send("1"); state["welcome"] = True; buf = ""; continue
        if "Press 1 to continue" in tail and state["welcome"] and not state["info"]:
            time.sleep(0.3); send("1"); state["info"] = True; buf = ""; continue
        if "Select the installation path" in tail and not state["path"]:
            time.sleep(0.3); send(str(target)); state["path"] = True; buf = ""; continue
        if "Enter O for OK" in tail and not state["create"]:
            time.sleep(0.3); send("O"); state["create"] = True; buf = ""; continue
        if "Enter Y for Yes, N for No" in tail and state["packs_sent"] < 4:
            answer = pack_answers[state["packs_sent"]]
            time.sleep(0.3); send(answer); state["packs_sent"] += 1; buf = ""; continue
        if "Press 1 to continue" in tail and state["packs_sent"] >= 4 and not state["packs_confirm"]:
            time.sleep(0.3); send("1"); state["packs_confirm"] = True; buf = ""; continue
        if "Installation Finished" in buf and not state["install_confirm"]:
            time.sleep(0.3); send("N"); state["install_confirm"] = True; buf = ""; break
        if "ABORTED" in tail or "FAILED" in tail:
            raise RuntimeError("Installer reported ABORTED/FAILED. Check output.")

    os.close(fd)
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=str(Path.home() / ".local" / "opt" / "verapdf"))
    args = ap.parse_args()

    if shutil.which("java") is None:
        print("ERROR: java not found on PATH. veraPDF requires Java 11+.", file=sys.stderr)
        return 2

    target = Path(args.target)
    if target.exists():
        print(f"Removing existing install at {target} ...", flush=True)
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zip_path = download_installer(tmp_path / "verapdf-installer.zip")
        jar = extract_installer(zip_path, tmp_path / "extracted")
        print(f"Installing to {target} ...", flush=True)
        run_installer(jar, target)

    wrapper = target / "verapdf"
    if not wrapper.exists():
        print(f"ERROR: install did not produce {wrapper}", file=sys.stderr)
        return 3
    out = subprocess.check_output([str(wrapper), "--version"], text=True)
    print("\nInstalled:", out.splitlines()[0])
    print(f"Wrapper: {wrapper}")
    print("\nAdd to PATH, or alias in your shell:")
    print(f'  alias verapdf="{wrapper}"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
