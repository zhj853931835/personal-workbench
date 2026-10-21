# -*- coding: utf-8 -*-
"""push.py - precheck, stage, commit, push. Never force-pushes.

Usage:
    python tools/push.py -m "commit message"
    python tools/push.py -m "msg" --dry-run
    python tools/push.py -m "msg" --no-precheck
"""
import argparse
import io
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*args, check=False):
    r = subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    if check and r.returncode != 0:
        print("  git %s FAILED: %s" % (" ".join(args), out))
        sys.exit(1)
    return r.returncode, out


def section(title):
    print("")
    print("-" * 58)
    print(title)
    print("-" * 58)


def precheck():
    section("1/4 PRECHECK")
    _, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    print("  branch: " + branch)
    if branch != "main":
        print("  ERROR: not on main branch")
        return False

    code, out = git("fetch", "origin")
    if code != 0:
        print("  ERROR: fetch failed -> " + out[:200])
        return False
    print("  fetch ok")

    _, local = git("rev-parse", "HEAD")
    _, remote = git("rev-parse", "origin/main")

    if local == remote:
        print("  local == remote")
        return True

    _, ahead = git("log", "--oneline", "HEAD..origin/main")
    if ahead.strip():
        print("  REMOTE AHEAD - refusing to push blindly:")
        for line in ahead.splitlines():
            if line.strip():
                print("     " + line)
        print("")
        print("  Run: git pull --rebase origin main")
        return False

    _, behind = git("log", "--oneline", "origin/main..HEAD")
    n = len([l for l in behind.splitlines() if l.strip()])
    print("  local ahead by %d commit(s), will push" % n)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--message", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-precheck", action="store_true")
    args = ap.parse_args()

    print("=" * 58)
    print("REPO: " + REPO)
    print("=" * 58)

    if not args.no_precheck and not precheck():
        print("")
        print("ABORTED at precheck")
        return 1

    section("2/4 STAGE")
    _, out = git("status", "--porcelain")
    changed = [l for l in out.splitlines() if l.strip()]
    if not changed:
        print("  nothing to commit")
        section("3/4 SKIP")
        section("4/4 DONE")
        return 0
    for line in changed:
        print("  " + line)
    git("add", "-A", check=True)
    print("  staged %d file(s)" % len(changed))

    if args.dry_run:
        section("3/4 DRY-RUN")
        print("  would commit: " + args.message)
        git("reset")
        return 0

    section("3/4 COMMIT")
    msgfile = os.path.join(os.environ.get("TEMP", "."), "_pushmsg.txt")
    with io.open(msgfile, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(args.message)
    code, out = git("commit", "-F", msgfile)
    try:
        os.remove(msgfile)
    except OSError:
        pass
    if code != 0:
        print("  commit FAILED: " + out[:300])
        return 1
    print("  " + out.splitlines()[0])

    section("4/4 PUSH")
    for attempt in range(1, 4):
        code, out = git("push", "origin", "main")
        if code == 0:
            print("  pushed ok")
            _, sha = git("rev-parse", "--short", "HEAD")
            print("  HEAD: " + sha)
            return 0
        print("  attempt %d failed: %s" % (attempt, out[:200]))
        if attempt < 3:
            time.sleep(3)
    print("  PUSH FAILED after 3 attempts")
    return 1


if __name__ == "__main__":
    sys.exit(main())