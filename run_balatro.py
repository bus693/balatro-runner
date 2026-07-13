from argparse import ArgumentParser
from enum import Enum
from json import dumps, loads
from pathlib import Path
from subprocess import run
from sys import excepthook, exit, stderr

MODS_SRC_PATH = Path("~/Documents/balatro/mods/").expanduser()
MODS_INSTALL_PATH = Path("~/Library/Application Support/Balatro/Mods/").expanduser()
LOVELY_BLACKLIST_PATH = "~/Library/Application Support/Balatro/Mods/lovely/blacklist.txt"
LOVELY_RUNNER_PATH = "~/Library/Application Support/Steam/steamapps/common/Balatro/run_lovely_macos.sh"

class EXIT_CODES(Enum):
  DEPTH_EXCEEDED = 3,
  MOD_OUTSIDE_MODS_FOLDER = 4,
  SIGINT = 130,

verbose = None

def __clean_up_mods():
  if verbose:
    print("Cleaning up")
  mods_install_root_path = Path(MODS_INSTALL_PATH).expanduser()
  for item in mods_install_root_path.iterdir():
    if not item.is_symlink():
      continue
    if verbose:
      print(f"  Removing symlink for {item.name}")
    item.unlink()

def __install(group_name, mods):
  for mod in mods:
    src_folder = MODS_SRC_PATH / mod
    # no directory traversal outside MODS_SRC_PATH
    is_safe_location = src_folder.resolve().is_relative_to(MODS_SRC_PATH)
    if not is_safe_location:
      print(f"Location not allowed {mod}", file=stderr)
      print("Aborting", file=stderr)
      exit(EXIT_CODES.MOD_OUTSIDE_MODS_FOLDER.value)

    if not src_folder.resolve().is_dir():
      # TODO: install
      print(f"Cannot find mod {mod}, skipping", file=stderr)

    target_mod_name = "@".join(mod.split("/"))
    posix_target = MODS_INSTALL_PATH / target_mod_name
    if verbose:
      print(f"  Creating symlink for {mod}")
    posix_target.symlink_to(src_folder)

def __get_group_mods_from_config():
  groups_config_path = Path(__file__).parent / "groups.json"
  with open(groups_config_path) as f:
    groups_config = loads("".join(f.readlines()))
  group_mods = {}
  for group_name in groups_config:
    group_mods[group_name] = __get_group_mods(group_name, groups_config)
  return group_mods

def __get_group_mods(group_name, groups_config, depth=0):
  max_depth = 10
  if depth > max_depth:
    print(f"{group_name} within the configs is nested too deep", file=stderr)
    print(f"Aborting", file=stderr)
    exit(EXIT_CODES.DEPTH_EXCEEDED.value)
  mods = []
  group = groups_config[group_name]
  if "mods" in group:
    mods.extend(group["mods"])
  if "groups" in group:
    # TODO: memoize
    for subgroup in group["groups"]:
      mods.extend(__get_group_mods(subgroup, groups_config, depth+1))
  return mods

def __clear_blacklist():
  blacklist_loc = Path("~/Library/Application Support/Balatro/Mods/lovely/blacklist.txt").expanduser()
  if not blacklist_loc.exists():
    print("  blacklist.txt does not exist; did not clear.", file=stderr)
    return
  if not blacklist_loc.is_file():
    print("  blacklist.txt is not a file; did not clear.", file=stderr)
    return
  blacklist_loc.write_text("")

def main():
  parser = ArgumentParser()
  parser.add_argument("groups", nargs="*")
  parser.add_argument("-v", "--verbose", action="store_true")
  parser.add_argument("--clear-blacklist", action="store_true")
  args = parser.parse_args()
  global verbose
  verbose = args.verbose

  print("Running Balatro via bus693/balatro-runner")

  if not len(args.groups):
    if args.clear_blacklist:
      print("Running the game without mods; skipped clearing blacklist")
    run(["open", "-a", "Balatro"])
    return

  if verbose:
    print("Parsing config")
  group_mods = __get_group_mods_from_config()
  if verbose:
    print(dumps(group_mods, indent=2))

  if verbose:
    print("Installing mods...")
  __clean_up_mods()

  for group_name in args.groups:
    if verbose:
      print(f"Installing group {group_name}")
    __install(group_name, group_mods[group_name])

  if args.clear_blacklist:
    if verbose:
      print("Clearing blacklist.")
    __clear_blacklist()

  if verbose:
    print("Done installing mods.")

  if verbose:
    print("Running Balatro...")

  run(["sh", Path(LOVELY_RUNNER_PATH).expanduser()])

   
try:
  main()
except KeyboardInterrupt:
  print("\nInterrupted by user, closing Balatro.", file=stderr)
  exit(EXIT_CODES.SIGINT.value)
