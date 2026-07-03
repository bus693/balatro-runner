from argparse import ArgumentParser
from pathlib import Path
from subprocess import run

MODS_SRC_PATH = "~/Documents/balatro/mods/"
MODS_INSTALL_PATH = "~/Library/Application Support/Balatro/Mods/"
LOVELY_RUNNER_PATH = "~/Library/Application Support/Steam/steamapps/common/Balatro/run_lovely_macos.sh"

# no_mods: no mods at all, not even lovely
# core: vanilla with a few QOL mods
# all: all the mods, toggle individual mods using smods in-game mod selector
RUN_TYPES = ["no_mods", "core", "all"]

verbose = None

def __clean_up_mods():
  mods_install_root_path = Path(MODS_INSTALL_PATH).expanduser()
  for item in mods_install_root_path.iterdir():
    if not item.is_symlink():
      continue
    if verbose:
      print(f"Removing symlink for {item.name}")
    item.unlink()

def __install(dir_name):
  src_folder_path = Path(f"{MODS_SRC_PATH}{dir_name}/").expanduser()
  for item in src_folder_path.iterdir():
    if not item.is_dir():
      continue
    posix_target = Path(f"{MODS_INSTALL_PATH}/{item.name}").expanduser()
    posix_source = item
    posix_target.symlink_to(item)
    if verbose:
      print(f"Creating symlink for {item.name}")
      
def main():
  parser = ArgumentParser()
  parser.add_argument("run_type", nargs="?", default="no_mods", choices=["no_mods", "core", "all"])
  parser.add_argument("-v", "--verbose", action="store_true")
  args = parser.parse_args()
  global verbose
  verbose = args.verbose

  print("Running Balatro via bus693/balatro-runner")

  if args.run_type == "no_mods":
    run(["open", "-a", "Balatro"])
    return

  if verbose:
    print("Installing mods...")
  __clean_up_mods()

  if args.run_type == "core":
    __install("core")
  elif args.run_type == "all":
    __install("all")
    __install("core")

  if verbose:
    print("Done installing mods.")

  if verbose:
    print("Running Balatro...")

  run(["sh", Path(LOVELY_RUNNER_PATH).expanduser()])

   

main()
