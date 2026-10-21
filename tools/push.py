# -*- coding: utf-8 -*-
\"\"\"
push.py - one-shot: precheck -> stage -> commit -> push
Usage:
    python push.py -m "commit message"
    python push.py -m "msg" --dry-run
    python push.py -m "msg" --no-precheck
Exits nonzero on any failure. Never force-pushes.
\"\"\"
import subprocess, sys, os, argparse

REPO = r"E:\Zcode项目\数字商品\C-工作台\github-repo"

def git(*args, check=False):
    r = subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    if check and r.returncode != 0:
        print("  git %s FAILED: %s" % (" ".join(args), out))
        sys.exit(1)
    return r.returncode, out

def section(t):
    print("\n" + "-" * 58)
    print(t)
    print("-" * 58)

def precheck():
    section("1/4 PRECHECK")
    _, br = git("rev-parse", "--abbrev-ref", "HEAD")
    print("  branch: " + br)
    if br != "main":
        print("  ERROR: not on main branch")
        return False
    code, out = git("fetch", "origin")
    if code != 0:
        print("  ERROR: fetch failed -> " + out[:200])
        return False
    print("  fetch ok")
    _, local = git("rev-parse", "HEAD")
    _, remote = git("rev-parse", "origin/main")
    if local != remote:
        _, ahead = git("log", "--oneline", "HEAD..origin/main")
        if ahead:
            print("  REMOTE AHEAD - refusing to push blindly:")
            for l in ahead.split("\n"):
                print("     " + l)
            print("\n  Run: git pull --rebase origin main")
            return False
        _, behind = git("log", "--oneline", "origin/main..HEAD")
        print("  local ahead by %d commit(s), will push" % len([l for l in behind.split("\n") if l.strip()]))
    else:
        print("  local == remote")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--message", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-precheck", action="store_true")
    a = ap.parse_args()

    print("=" * 58)
    print("REPO: " + REPO)
    print("=" * 58)

    if not a.no_precheck and not precheck():
        print("\nABORTED at precheck")
        return 1

    section("2/4 STAGE")
    code, out = git("status", "--porcelain")
    changed = [l for l in out.split("\n") if l.strip()]
    if not changed:
        print("  nothing to commit")
        section("3/4 SKIP")
        print("  no changes")
        section("4/4 DONE")
        return 0
    for l in changed:
        print("  " + l)
    git("add", "-A", check=True)
    print("  staged %d file(s)" % len(changed))

    if a.dry_run:
        section("3/4 DRY-RUN")
        print("  would commit: " + a.message)
        git("reset")
        return 0

    section("3/4 COMMIT")
    msgfile = os.path.join(os.environ.get("TEMP", "."), "_pushmsg.txt")
    with io.open(msgfile, "w", encoding="utf-8", newline="\n") as f:
        f.write(a.message)
    code, out = git("commit", "-F", msgfile)
    try: os.remove(msgfile)
    except Exception: pass
    if code != 0:
        print("  commit FAILED: " + out[:300])
        return 1
    print("  " + out.split("\n")[0])

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
            import time; time.sleep(3)
    print("  PUSH FAILED after 3 attempts")
    return 1

if __name__ == "__main__":
    sys.exit(main())
