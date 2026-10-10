#!/bin/sh
# Compile src/ into the code cave: out/cave.elf + out/cave.bin
set -e
cd "$(dirname "$0")"
mkdir -p out
arm-none-eabi-gcc -mcpu=cortex-m7 -mthumb -mfloat-abi=hard -mfpu=fpv5-d16 -Os -ffreestanding -nostdlib \
  -fno-builtin -Wall -Wextra -Werror -T src/cave.ld -Wl,-e,0 -o out/cave.elf src/filter.c src/filter_thunk.S src/padpages.c src/padpages_thunk.S src/clipshift.c src/clipshift_thunk.S
arm-none-eabi-objcopy -O binary -j .cave out/cave.elf out/cave.bin
arm-none-eabi-size -A out/cave.elf | grep -E 'cave|ram'
