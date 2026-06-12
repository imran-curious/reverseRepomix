from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from pathlib import Path
import re
import sys

def hardened_unpack(xml_path, output_dir, overwrite=False):
    """
    A hardened best-effort extractor for Repomix XML generated with --parsable-style.
    """
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Reading and parsing: {xml_path}")
    
    if not Path(xml_path).exists():
        print(f"Error: The file {xml_path} does not exist.")
        return

    try:
        raw_content = Path(xml_path).read_text(encoding="utf-8")
        raw_content = re.sub(r"^\s*<\?xml[^?]*\?>", "", raw_content, count=1)
        wrapped_xml = f"<root>\n{raw_content}\n</root>"
        root = ET.fromstring(wrapped_xml)

    except DefusedXmlException as e:
        sys.exit(f"Security: Blocked unsafe XML content: {e}")
    except ET.ParseError as e:
        print(f"Critical XML Parsing Error: {e}")
        print("Ensure your XML file has a closing tag and code sections use CDATA blocks if needed.")
        return

    # Incorporating the LLM's broader search pattern
    files = root.findall('.//file')
    if not files and root.tag == 'file':
        files = [root]

    print(f"Found {len(files)} file entries in the XML matrix.")
    extracted_count = 0

    for file_node in files:
        rel_path = file_node.get("path")
        if not rel_path:
            continue

        target_path = (out_path / rel_path).resolve()

        # Security: Enforce strict path confinement
        try:
            target_path.relative_to(out_path)
        except ValueError:
            print(f"Security Warning: Blocked unsafe path traversal -> {rel_path}")
            continue

        if target_path.exists() and not overwrite:
            print(f"Skipped existing file: {rel_path}")
            continue

        # Extract code contents safely
        # NOTE: We intentionally removed .strip() here because stripping whitespace 
        # destroys exact formatting and newlines at the start/end of code files.
        content = file_node.text if file_node.text else ""
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            target_path.write_text(content, encoding="utf-8")
            print(f"Extracted: {rel_path}")
            extracted_count += 1
        except Exception as e:
            print(f"Failed to write destination asset {rel_path}: {e}")

    print("--------------------------------------------------")
    print(f"Safely extracted {extracted_count} text files to {out_path}")
    print("Reminder: Ignored files, binaries, metadata, permissions, and symlinks cannot be recovered.")

if __name__ == "__main__":
    hardened_unpack("repomix-output.xml", "restored-project")
