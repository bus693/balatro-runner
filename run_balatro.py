from argparse import ArgumentParser
from enum import Enum
from json import dumps, loads
from pathlib import Path
from subprocess import run
from sys import excepthook, exit, stderr

FOLDERS_JSON = Path(__file__).parent / "folders.json"
MODS_INSTALL_PATH = Path("~/Library/Application Support/Balatro/Mods/").expanduser()
LOVELY_BLACKLIST_PATH = Path("~/Library/Application Support/Balatro/Mods/lovely/blacklist.txt").expanduser()
LOVELY_RUNNER_PATH = Path("~/Library/Application Support/Steam/steamapps/common/Balatro/run_lovely_macos.sh").expanduser()

class EXIT_CODES(Enum):
  DEPTH_EXCEEDED = 3,
  MOD_OUTSIDE_MODS_FOLDER = 4,
  GROUP_DOES_NOT_EXIST_IN_CONFIG = 5,
  GROUP_DOES_NOT_EXIST_IN_INPUT = 6,
  SIGINT = 130,

verbose = None

def __setup_folders_json():
  yes = set(['y', 'yes'])
  exists = False
  should_create = False
  print("Welcome to balatro-runner. One setup step before we start.")
  while not (exists or should_create):
    mod_folder = input("Where are your mods?\n  Example: ~/Documents/balatro/mods\n> ")
    if mod_folder == "":
      print("Enter a valid folder.")
      continue
    if Path(mod_folder).expanduser().resolve().exists():
      exists = True
    else:
      should_create = input(f"{mod_folder} does not exist, would you like to create it (y/n)?\n> ").strip().lower() in yes
  if should_create:
    print(f"Creating folder at {mod_folder}")
    Path(mod_folder).expanduser().mkdir(parents=True, exist_ok=False)
  folders_json = {
    "mod_source": str(Path(mod_folder))
  }
  print(f"Writing folder settings to {FOLDERS_JSON}. You can change it here later.")
  with open(FOLDERS_JSON, "w", encoding="utf-8") as f:
    f.writelines(dumps(folders_json, indent=2))
  print("Setup complete. Run balatro-runner again to start the game.")
  exit(0)

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

def __install(mods):
  for mod in mods:
    with open(FOLDERS_JSON) as f:
      src_folder = Path(loads("".join(f.readlines()))["mod_source"]).expanduser()
    mod_src_folder = src_folder / mod
    # no directory traversal outside MODS_SRC_PATH
    is_safe_location = mod_src_folder.resolve().is_relative_to(src_folder)
    if not is_safe_location:
      print(f"Location not allowed {mod}", file=stderr)
      print("Aborting", file=stderr)
      exit(EXIT_CODES.MOD_OUTSIDE_MODS_FOLDER.value)

    if not mod_src_folder.resolve().is_dir():
      # TODO: install
      print(f"Cannot find mod {mod}, skipping", file=stderr)

    target_mod_name = "@".join(mod.split("/"))
    posix_target = MODS_INSTALL_PATH / target_mod_name
    if verbose:
      print(f"  Creating symlink for {mod}")
    posix_target.symlink_to(mod_src_folder)

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
      if not subgroup in groups_config:
        print(f"Group '{subgroup}' is referenced in '{group_name}' but is undefined", file=stderr)
        exit(EXIT_CODES.GROUP_DOES_NOT_EXIST_IN_CONFIG.value)
      mods.extend(__get_group_mods(subgroup, groups_config, depth+1))
  return mods

def __clear_blacklist():
  if not LOVELY_BLACKLIST_PATH.exists():
    print("  blacklist.txt does not exist; did not clear.", file=stderr)
    return
  if not LOVELY_BLACKLIST_PATH.is_file():
    print("  blacklist.txt is not a file; did not clear.", file=stderr)
    return
  LOVELY_BLACKLIST_PATH.write_text("")

def main():
  parser = ArgumentParser()
  parser.add_argument("groups", nargs="*")
  parser.add_argument("-v", "--verbose", action="store_true")
  parser.add_argument("--clear-blacklist", action="store_true")
  args = parser.parse_args()
  global verbose
  verbose = args.verbose

  folders_json = Path(__file__).parent / "folders.json"

  if not folders_json.exists():
    __setup_folders_json()

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

  # Check that all groups are valid before we install
  for group_name in args.groups:
    if not group_name in group_mods:
      print(f"Group '{group_name}' does not exist", file=stderr)
      exit(EXIT_CODES.GROUP_DOES_NOT_EXIST_IN_INPUT.value)

  if verbose:
    print("Installing mods...")
  __clean_up_mods()

  for group_name in args.groups:
    if verbose:
      print(f"Installing group {group_name}")
    __install(group_mods[group_name])

  if args.clear_blacklist:
    if verbose:
      print("Clearing blacklist.")
    __clear_blacklist()

  if verbose:
    print("Done installing mods.")

  if verbose:
    print("Running Balatro...")

  run(["sh", LOVELY_RUNNER_PATH])

   
try:
  main()
except KeyboardInterrupt:
  print("\nInterrupted by user, closing Balatro.", file=stderr)
  exit(EXIT_CODES.SIGINT.value)
