#!/usr/bin/env python3
import sys, re, os

def load_entries(entries_path):
    """
    Parse entries.a (lines like "=NAME    #HEX ...") and return a dict:
        mapping["=NAME"] = "#HEX"
    """
    mapping = {}
    with open(entries_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("="):
                continue
            parts = re.split(r"\s+", line)
            if len(parts) < 2:
                continue
            name = parts[0]         # e.g. "=POP#"
            hexcode = parts[1]      # e.g. "#01234"
            mapping[name] = hexcode
    return mapping

def replace_in_source(source_path, entries_path, output_path):
    """
    Read source_path, replace every literal "=NAME" (keys of mapping)
    with "#HEX", and write to output_path. Matches names exactly,
    regardless of trailing '#' or other punctuation.
    """
    mapping = load_entries(entries_path)
    text = open(source_path, "r", encoding="utf-8").read()

    if mapping:
        # Sort keys by length desc so longer names like "=POP#" match
        keys = sorted(mapping.keys(), key=len, reverse=True)
        # Escape each key for literal regex matching
        escaped_keys = [re.escape(k) for k in keys]
        # Build a pattern that matches any of those literals, no \b
        combined = re.compile(r"(" + "|".join(escaped_keys) + r")")

        def _repl(m):
            return mapping[m.group(0)]

        new_text = combined.sub(_repl, text)
    else:
        new_text = text

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_text)

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} source.a entries.a output.a")
        sys.exit(1)

    src_file     = sys.argv[1]
    entries_file = sys.argv[2]
    out_file     = sys.argv[3]

    if not os.path.isfile(src_file):
        print(f"Error: source file '{src_file}' not found.")
        sys.exit(1)
    if not os.path.isfile(entries_file):
        print(f"Error: entries file '{entries_file}' not found.")
        sys.exit(1)

    replace_in_source(src_file, entries_file, out_file)
    print(f"Preprocessed '{src_file}' → '{out_file}'.")

if __name__ == "__main__":
    main()
