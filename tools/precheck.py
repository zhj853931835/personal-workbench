# -*- coding: utf-8 -*-
import subprocess, sys
REPO = r"E:\Zcode项目\数字商品\C-工作台\github-repo"
def run(cmd):
    r = subprocess.run(cmd, cwd=REPO, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
def main():
    print("=" * 60)
    print("GitHub repo precheck")
    print("=" * 60)
    c, o = run("git rev-parse --abbrev-ref HEAD"); print("\n[branch] " + o)
    c, o = run("git status --porcelain")
    dirty = [l for l in o.split("\n") if l.strip()]
    print("\n[working tree] " + ("%d changed" % len(dirty) if dirty else "clean"))
    for l in dirty[:20]: print("   " + l)
    c, o = run("git fetch origin")
    if c != 0:
        print("\n[fetch] FAILED: " + o[:200]); return 1
    print("\n[fetch] ok")
    c, remote = run("git rev-parse origin/main")
    c, local = run("git rev-parse HEAD")
    print("\n[compare]")
    print("   local  HEAD: " + local[:16])
    print("   remote main: " + remote[:16])
    if local == remote:
        print("   IDENTICAL - safe to modify")
    else:
        c, o = run("git log --oneline HEAD..origin/main")
        ahead = [l for l in o.split("\n") if l.strip()]
        if ahead:
            print("\n   REMOTE HAS %d NEW COMMITS:" % len(ahead))
            for l in ahead: print("      " + l)
            c, o = run("git diff --stat HEAD..origin/main")
            print("\n   changed files:\n" + o)
        c, o = run("git log --oneline origin/main..HEAD")
        behind = [l for l in o.split("\n") if l.strip()]
        if behind:
            print("\n   LOCAL HAS %d UNPUSHED:" % len(behind))
            for l in behind: print("      " + l)
    print("\n" + "=" * 60)
    return 0
if __name__ == "__main__":
    sys.exit(main())
