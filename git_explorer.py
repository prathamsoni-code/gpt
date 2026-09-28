import subprocess
import os
from collections import Counter
from datetime import datetime


# -----------------------------
# Terminal styling
# -----------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
GRAY = "\033[90m"
RED = "\033[91m"


def run_git(*args):
    """Run a git command and return its output."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError:
        return None


def verify_repository():
    result = run_git("rev-parse", "--is-inside-work-tree")

    if result != "true":
        print(f"{RED}This folder is not a Git repository.{RESET}")
        print("Run this script inside one of your repositories.")
        raise SystemExit(1)


def repo_name():
    root = run_git("rev-parse", "--show-toplevel")
    return os.path.basename(root)


def load_commits():
    # Separator characters make parsing safer than splitting on spaces.
    format_string = "%H%x1f%h%x1f%an%x1f%ae%x1f%ad%x1f%s%x1e"

    output = run_git(
        "log",
        "--date=iso",
        f"--pretty=format:{format_string}"
    )

    if not output:
        return []

    commits = []

    for record in output.strip("\x1e\n").split("\x1e"):
        fields = record.strip().split("\x1f")

        if len(fields) != 6:
            continue

        full_hash, short_hash, author, email, date, message = fields

        commits.append({
            "hash": full_hash,
            "short_hash": short_hash,
            "author": author,
            "email": email,
            "date": date,
            "message": message,
        })

    return commits


def print_header():
    print()
    print(f"{BOLD}{CYAN}{'=' * 65}{RESET}")
    print(f"{BOLD}  GIT REPOSITORY EXPLORER{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 65}{RESET}")
    print(f"Repository: {GREEN}{repo_name()}{RESET}")
    print()


def display_commits(commits, limit=10):
    print(f"\n{BOLD}Recent commits{RESET}\n")

    for i, commit in enumerate(commits[:limit], start=1):
        date = commit["date"][:10]

        print(
            f"{YELLOW}{i:>2}.{RESET} "
            f"{MAGENTA}{commit['short_hash']}{RESET} "
            f"{commit['message']}"
        )

        print(
            f"    {GRAY}{commit['author']} | {date}{RESET}"
        )


def repository_stats(commits):
    print(f"\n{BOLD}Repository statistics{RESET}\n")

    if not commits:
        print("No commits found.")
        return

    authors = Counter(commit["author"] for commit in commits)

    dates = []

    for commit in commits:
        try:
            date_string = commit["date"][:10]
            dates.append(datetime.strptime(date_string, "%Y-%m-%d"))
        except ValueError:
            pass

    print(f"Total commits : {GREEN}{len(commits)}{RESET}")
    print(f"Contributors  : {GREEN}{len(authors)}{RESET}")

    if dates:
        first = min(dates).strftime("%d %b %Y")
        latest = max(dates).strftime("%d %b %Y")

        print(f"First commit  : {first}")
        print(f"Latest commit : {latest}")

    print(f"\n{BOLD}Top contributors{RESET}")

    for author, count in authors.most_common(5):
        print(f"  {author:<25} {count} commits")


def inspect_commit(commits):
    display_commits(commits, 15)

    try:
        choice = int(input("\nSelect commit number: ")) - 1
        commit = commits[choice]

    except (ValueError, IndexError):
        print(f"{RED}Invalid selection.{RESET}")
        return

    print(f"\n{BOLD}{CYAN}Commit details{RESET}")
    print(f"Hash    : {commit['hash']}")
    print(f"Author  : {commit['author']}")
    print(f"Email   : {commit['email']}")
    print(f"Date    : {commit['date']}")
    print(f"Message : {commit['message']}")

    print(f"\n{BOLD}Files changed{RESET}\n")

    files = run_git(
        "show",
        "--stat",
        "--oneline",
        commit["hash"]
    )

    print(files)


def search_commits(commits):
    query = input("\nSearch commit messages: ").lower().strip()

    matches = [
        commit
        for commit in commits
        if query in commit["message"].lower()
        or query in commit["author"].lower()
    ]

    if not matches:
        print(f"{YELLOW}No commits found matching '{query}'.{RESET}")
        return

    display_commits(matches, len(matches))


def menu(commits):

    while True:

        print(f"""
{BOLD}Choose an action:{RESET}

  {CYAN}1{RESET}  Recent commits
  {CYAN}2{RESET}  Repository statistics
  {CYAN}3{RESET}  Inspect commit
  {CYAN}4{RESET}  Search history
  {CYAN}5{RESET}  Exit
""")

        choice = input("> ").strip()

        if choice == "1":
            display_commits(commits)

        elif choice == "2":
            repository_stats(commits)

        elif choice == "3":
            inspect_commit(commits)

        elif choice == "4":
            search_commits(commits)

        elif choice == "5":
            print(f"\n{GREEN}Later 👋{RESET}")
            break

        else:
            print(f"{RED}Unknown option.{RESET}")


def main():
    verify_repository()

    commits = load_commits()

    print_header()

    if not commits:
        print("Repository has no commits yet.")
        return

    menu(commits)


if __name__ == "__main__":
    main()