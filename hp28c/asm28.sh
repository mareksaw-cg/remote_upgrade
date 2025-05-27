#!/usr/bin/env bash
#
# asm28.sh — assemble a Saturn source, insert spaces,
#             and display the .o file content
# Usage: asm28.sh filename.a
#

# 1. Check arguments
if [ -z "$1" ]; then
  echo "Usage: ${0##*/} filename.a" >&2
  exit 1
fi

infile="$1"
base="${infile%.*}"     # strip extension, e.g. foo.a → foo
objfile="${base}.o"     # e.g. foo.o

# 2. Verify input file exists
if [ ! -f "$infile" ]; then
  echo "Error: File '$infile' not found." >&2
  exit 1
fi

# 3. Check that 'sasm' is in PATH
if ! command -v sasm >/dev/null 2>&1; then
  echo "Error: 'sasm' not found. Please install your Saturn assembler." >&2
  exit 1
fi

# 4. Assemble with SASM in host mode
echo "Assembling '$infile'..."
if ! sasm -h "$infile"; then
  echo
  echo "*** SASM reported errors." >&2
  exit 1
fi

# 5. Insert a space after every 5 characters in the .o file
if [ ! -f "$objfile" ]; then
  echo "Error: Expected output '$objfile' not found." >&2
  exit 1
fi

if ! sed -E 's/.{5}/& /g' "$objfile" > "${objfile}.tmp"; then
  echo
  echo "*** Failed to post-process $objfile." >&2
  exit 1
fi
mv "${objfile}.tmp" "$objfile"

# 6. Display the content of the spaced .o file
echo
echo "--- Contents of $objfile ---"
cat "$objfile"
echo
echo "*** Done. Assembled, spaced, and displayed: $objfile"
