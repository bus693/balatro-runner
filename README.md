# balatro-runner

Run Balatro with groups of mods.

## Why

You may want to switch up which mods you use. In-game, you can do this with steamodded's mod list, but what if you also want to load the game without smods sometimes? balatro-runner allows you to do this.

## Support

This script only works on macOS and requires python3. (It's tested on system python3 but any python3 should work.)

## Install

1. Edit the `MODS_SRC_PATH` to set it to a folder that will contain your mods, but wait before you move your mods.

2. This script expects your mods to be in subfolders within `MODS_SRC_PATH`:

Here is an example of what your mods setup could look like.

<img src="example_folder_setup.png" width="200">

## Run

First, follow the install instructions. The runner will not work if it can't find your mods.

Then, you can choose between the following commands.

- `python3 run_balatro.py`: Including no groups runs the game without any mods. It does not use the lovely run script.
- `python3 run_balatro.py core all`: You can include any number of groups. Including groups installs all the mods within those groups. Mods within lovely's `blacklist.txt` are still disabled. For verbose mode, `python3 run_balatro.py core all -v`.
- `python3 run_balatro.py core all --clear-blacklist`: By default, any mods on the blacklist (typically, this is from disabling the mod using smods' in-game mod selector) will not run. Clearing the blacklist enables all the mods in your groups.

## Troubleshooting

Contact `Bus693` on Balatro Discord. Include the command output in verbose mode.