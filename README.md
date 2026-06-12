# Reverse Repomix Workflow Guide

When working with large language models (LLMs) and tools like [Repomix](https://repomix.com) to generate context, modifying large codebases effectively can be challenging. This repository provides the recommended workflows and tools for applying LLM-edited code back to your original project.

---

## 🌟 Phase 1: The Ideal Workflow (Git Patches)

If you are actively prompting an AI to modify your codebase using Repomix context, **do not ask the AI to output an edited Repomix XML.** Instead, use Git diffs. This is the only native, failsafe way to handle creations, renames, deletions, and line-specific edits without touching your ignored or binary files.

### The Execution:

1. **Generate context:**
   ```bash
   npx repomix --style xml --parsable-style
   ```

2. **Prompt the AI:** Provide the XML to the AI, but explicitly instruct it:
   > *"Return your modifications exclusively as a standard unified Git diff (.patch file)."*

3. **Apply the changes safely:**
   ```bash
   git checkout -b ai-edit
   # Save AI output to changes.patch
   git apply --check changes.patch  # Validate first
   git apply changes.patch          # Apply if safe
   git status                       # Review
   ```

---

## 🛠️ Phase 2: The Fallback Extractor (XML to Files)

If you are forced to extract files from an existing `repomix-output.xml` (e.g., you lost the original project, or you are downloading an AI's output artifact), use the included hardened Python script: `unpack_repomix.py`.

### ⚠️ Constraints & Limitations
* **It is a best-effort extractor, not a full restorer.**
* It will extract the text files safely, but you permanently lose:
  * Ignored files
  * Binaries (images, compiled code, etc.)
  * Original timestamps
  * Symlinks
  * Exact file permissions
* **It will not reliably handle:** Deleted files, renamed files, or AI-intended removal of old files.

### Prerequisites

You need Python installed. Install the required dependency:
```bash
pip install -r requirements.txt
# or directly: pip install defusedxml
```

### Usage

Run the script to safely extract the files:
```bash
python unpack_repomix.py
```

*By default, the script looks for `repomix-output.xml` and outputs to `restored-project`.*

---

## 🧠 The Mechanism & Ultimate Takeaway

Treat Repomix exactly like a "compiler" for LLM context—it goes one way. Use the Git patch method to bring code *back* into your project, and only rely on XML extraction scripts as an emergency recovery tool for raw text files.

To effectively use the fallback extractor while preserving your binary/ignored files, you must use an **overlay mechanism**:

```text
unedited mother project
        +
edited repomix-output.xml
        =
new full edited project folder
```

### How Overlaying Works:

1. **Copy the full unedited project folder first.**
   This preserves ignored files, binaries, `.env`, images, assets, etc. (Repomix itself may omit these during context generation).

2. **Overlay edited text files from `repomix-output.xml`.**
   Repomix XML contains files under a `<files>` section. The fallback script extracts these files, allowing you to write them over the copied project.

### Example Result:

```text
mother-project/
  src/app.js              (old version)
  .env                    (ignored, not in Repomix)
  public/logo.png         (binary, not in Repomix)
  node_modules/           (ignored)

edited repomix-output.xml
  src/app.js              (edited version)

---------------------------------------------------

edited-project/
  src/app.js              (edited version from XML overlay)
  .env                    (copied from mother-project)
  public/logo.png         (copied from mother-project)
  node_modules/           (copied from mother-project)
```

### Summary for Serious Workflows:

* **Best:** `original project` + `AI-generated git patch`
* **Fallback:** `original project copy` + `edited Repomix XML overlay`
* **Avoid:** Treating `repomix-output.xml` as a complete archive
