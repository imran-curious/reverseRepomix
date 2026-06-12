from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from pathlib import Path
import re
import sys

def hardened_unpack(xml_path, output_dir, overwrite=False):
    """
    A hardened best-effort extractor for Repomix XML generated with --parsable-style.
    Not a true reverse-Repomix tool, not a full project restore.
    """
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    try:
        raw_content = Path(xml_path).read_text(encoding="utf-8")

        # Defensive stripping: Remove XML declaration if present
        raw_content = re.sub(r"^\s*<\?xml[^?]*\?>", "", raw_content, count=1)

        # Wrap in a synthetic root to handle Repomix's multi-section structure
        wrapped_xml = f"<root>\n{raw_content}\n</root>"
        root = ET.fromstring(wrapped_xml)

    except DefusedXmlException as e:
        sys.exit(f"Security: Blocked unsafe XML content: {e}")
    except ET.ParseError as e:
        sys.exit(f"Failed to parse XML: {e}\nCritical: Ensure file was generated with: npx repomix --style xml --parsable-style")
    except FileNotFoundError:
        sys.exit(f"File not found: {xml_path}")

    extracted_count = 0

    # Locate the <files> section explicitly
    for file_elem in root.findall("./files/file"):
        rel_path = file_elem.get("path")
        if not rel_path:
            continue

        target_path = (out_path / rel_path).resolve()

        # Security: Enforce strict path confinement
        try:
            target_path.relative_to(out_path)
        except ValueError:
            print(f"Security Warning: Blocked unsafe path traversal -> {rel_path}")
            continue

        # UX: Prevent accidental overwrites
        if target_path.exists() and not overwrite:
            print(f"Skipped existing file: {rel_path}")
            continue

        content = file_elem.text or ""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        extracted_count += 1

    print(f"Safely extracted {extracted_count} text files to {out_path}")
    print("Reminder: Ignored files, binaries, metadata, permissions, and symlinks cannot be recovered.")

if __name__ == "__main__":
    hardened_unpack("repomix-output.xml", "restored-project")
