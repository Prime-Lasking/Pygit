import os
import sys
import hashlib
import json
from datetime import datetime

# === Constants ===
REPO_DIR = ".pygit"
OBJECTS_DIR = os.path.join(REPO_DIR, "objects")
INDEX_FILE = os.path.join(REPO_DIR, "index.json")
HEAD_FILE = os.path.join(REPO_DIR, "HEAD")

# === Helper Functions ===

def is_repo():
    return os.path.exists(REPO_DIR)

def repo_required(func):
    def wrapper(*args, **kwargs):
        if not is_repo():
            print("Error: Not a pygit repository. Run 'pygit init' first.")
            return
        return func(*args, **kwargs)
    return wrapper

def hash_content(content):
    return hashlib.sha1(content.encode()).hexdigest()

def write_object(data):
    content = json.dumps(data, sort_keys=True)
    oid = hash_content(content)
    path = os.path.join(OBJECTS_DIR, oid)
    with open(path, "w") as f:
        f.write(content)
    return oid

def read_object(oid):
    path = os.path.join(OBJECTS_DIR, oid)
    with open(path, "r") as f:
        return json.load(f)

# === Commands ===

def init():
    if is_repo():
        print("Repository already initialized.")
        return
    os.makedirs(OBJECTS_DIR)
    with open(INDEX_FILE, "w") as f:
        json.dump([], f)
    with open(HEAD_FILE, "w") as f:
        f.write("")
    print("Initialized empty pygit repository.")

@repo_required
def add(filename):
    if not os.path.exists(filename):
        print(f"File '{filename}' does not exist.")
        return
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)
    if filename not in index:
        index.append(filename)
        with open(INDEX_FILE, "w") as f:
            json.dump(index, f)
    print(f"Added '{filename}' to staging area.")

@repo_required
def commit(message):
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)
    if not index:
        print("Nothing to commit.")
        return

    snapshot = {}
    for filename in index:
        if not os.path.exists(filename):
            continue
        with open(filename, "r") as f:
            content = f.read()
        oid = hash_content(content)
        with open(os.path.join(OBJECTS_DIR, oid), "w") as obj:
            obj.write(content)
        snapshot[filename] = oid

    parent = None
    if os.path.exists(HEAD_FILE):
        with open(HEAD_FILE, "r") as f:
            parent = f.read().strip() or None

    commit_obj = {
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "snapshot": snapshot,
        "parent": parent
    }

    commit_hash = write_object(commit_obj)

    with open(HEAD_FILE, "w") as f:
        f.write(commit_hash)
    with open(INDEX_FILE, "w") as f:
        json.dump([], f)

    print(f"[{commit_hash[:7]}] {message}")

@repo_required
def log():
    if not os.path.exists(HEAD_FILE):
        print("No commits yet.")
        return

    with open(HEAD_FILE, "r") as f:
        current = f.read().strip()

    if not current:
        print("No commits yet.")
        return

    while current:
        commit = read_object(current)
        print(f"commit {current}")
        print(f"Date: {commit['timestamp']}")
        print(f"    {commit['message']}")
        print()
        current = commit.get("parent")

@repo_required
def status():
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)
    print("Staged files:")
    for f in index:
        print(f"  {f}")
    if not index:
        print("  (none)")

# === CLI Parser ===

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]

    if cmd == "init":
        init()
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Usage: pygit add <file>")
        else:
            add(sys.argv[2])
    elif cmd == "commit":
        if len(sys.argv) < 3:
            print("Usage: pygit commit <message>")
        else:
            commit(" ".join(sys.argv[2:]))
    elif cmd == "log":
        log()
    elif cmd == "status":
        status()
    else:
        print_help()

def print_help():
    print("Usage:")
    print("  pygit init               Initialize a new repository")
    print("  pygit add <file>         Add a file to staging")
    print("  pygit commit <message>   Commit staged files")
    print("  pygit log                Show commit history")
    print("  pygit status             Show staged files")

if __name__ == "__main__":
    main()
