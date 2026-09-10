# Roblox RBXLX Extractor (Standalone)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed-brightgreen.svg)]()
[![Roblox-Studio](https://img.shields.io/badge/Roblox%20Studio-NOT%20Required-success.svg)]()

A high-performance, standalone Python tool to parse Roblox `.rbxlx` XML place files into an in-memory **Roblox Instance Tree** and export the entire project to the local filesystem with separated Lua/Luau scripts (`.server.lua`, `.client.lua`, `.lua`) and rich metadata (`instance.json`).

**100% Standalone:** Runs entirely without Roblox Studio, Studio CLI, or any Studio API.

---

## Architecture Overview

```
save.rbxlx
    │
    ▼
┌────────────────────────────────────────┐
│  Stream Sanitizer (CleanReader)        │
│  - Filters invalid XML 1.0 control     │
│    characters (\x00-\x08, \x16, etc.)  │
│  - Incremental UTF-8 decoder           │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│  Streaming XML Parser (RbxlxParser)   │
│  - Low memory footprint iterparse      │
│  - Parses 20+ Roblox datatypes         │
│  - Decodes Tags & Attributes           │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│  Roblox Instance Tree (In-Memory)      │
│  - Parent-Child hierarchy              │
│  - ClassName, Name, Properties         │
│  - Script Source, Assets, Tags         │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│  Reference Resolver (ReferenceResolver)│
│  - Resolves Ref referents (RBX...)     │
│  - Maps target paths and names         │
│  - Catches broken/dangling references  │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│  Filesystem Exporter                   │
│  - Path sanitization & collision logic │
│  - Scripts (.server.lua, .client.lua)  │
│  - Metadata (instance.json)            │
│  - Manifest (manifest.json)            │
│  - Warnings (warnings.log)             │
└────────────────────────────────────────┘
```

---

## Key Features

1. **Zero External Dependencies**: Core engine uses only Python standard library modules (`xml.etree.ElementTree`, `struct`, `base64`, `json`, `codecs`, `re`, `argparse`).
2. **Crash-Proof XML Stream Sanitizer (`CleanReader`)**:
   - Roblox place files saved from Studio or obfuscated places often contain raw binary bytes and illegal XML 1.0 control characters (`\x00-\x08`, `\x0b-\x0c`, `\x0e-\x1f`) inside `<![CDATA[...]]>`.
   - Standard XML parsers crash with `ParseError: not well-formed (invalid token)`. Our `CleanReader` filters these on-the-fly without corrupting script contents.
3. **High Performance & Low Memory**:
   - Tested on a real **369 MB place file (`save.rbxlx`)** with **139,018 instances** and **4,962,084 properties**.
   - Streams XML elements and clears DOM nodes immediately, keeping RAM consumption under 450 MB.
4. **Script Extraction & Preservation**:
   - `Script` $\rightarrow$ `.server.lua`
   - `LocalScript` $\rightarrow$ `.client.lua`
   - `ModuleScript` $\rightarrow$ `.lua`
   - Verbatim extraction preserving exact newlines, tabs, and indentation.
   - **Scripts with children** (e.g. scripts holding configurations or RemoteEvents) are exported as a directory containing the script file, `instance.json`, and child instance subdirectories.
5. **Cross-Platform Sanitization & Collision Handling**:
   - Sanitizes Windows/Linux illegal characters (`< > : " / \ | ? *` and control chars).
   - Escapes Windows reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).
   - Sibling collision resolver automatically appends `_2`, `_3` for instances sharing identical names under the same parent folder, while preserving the true name in `instance.json`.
   - Automatic `\\?\` prefix support on Windows to bypass the 260-character `MAX_PATH` limit on deeply nested hierarchies.
6. **Robust Datatype Support**:
   - Vector2, Vector3, CoordinateFrame (CFrame matrix + position), Color3, Color3uint8, BrickColor, UDim, UDim2, NumberRange, NumberSequence, ColorSequence, Rect2D, Font, PhysicalProperties, Ref, Content, BinaryString, SharedString.
   - Any unknown datatype is stored in `rawProperties` so **zero data is lost**.
7. **Asset ID Detection**:
   - Detects asset references (`MeshId`, `TextureID`, `SoundId`, `AnimationId`, `Image`, `rbxassetid://`, etc.) and surfaces them in metadata.
8. **Bidirectional Reconstruction Ready**:
   - All referent IDs, original names, parent paths, and property structures are recorded in `instance.json` and `manifest.json`, allowing a future importer to reconstruct the place without Studio.

---

## Directory Layout

```
d:/rbx/
├── extractor.py                    # Root CLI entry point
├── pyproject.toml                  # Package configuration & console script
├── requirements.txt                # Development dependencies
├── README.md                       # Documentation
├── src/
│   ├── __init__.py
│   ├── main.py                     # CLI handler and pipeline coordinator
│   ├── parser/
│   │   ├── stream_sanitizer.py     # CleanReader streaming UTF-8 cleaner
│   │   ├── rbxlx_parser.py         # Pull-parsing instance tree builder
│   │   ├── xml_parser.py           # XML DOM node helpers
│   │   └── property_parser.py      # Datatype parsing and tag decoding
│   ├── model/
│   │   ├── instance.py             # RobloxInstance tree model
│   │   ├── property.py             # RobloxProperty representation
│   │   └── datatype.py             # Dataclasses for CFrame, Vector3, etc.
│   ├── resolver/
│   │   └── reference_resolver.py   # Ref property linker & broken ref detector
│   ├── exporter/
│   │   ├── filesystem_exporter.py  # Walks tree, creates folders & files
│   │   ├── script_exporter.py      # Writes Lua/Luau script files
│   │   ├── metadata_exporter.py    # Serializes instance.json
│   │   └── manifest_exporter.py    # Writes manifest.json and stats
│   └── utils/
│       ├── sanitize.py             # Filename sanitization & collision resolver
│       └── logger.py               # Warning collector & formatted output
└── tests/
    ├── conftest.py
    ├── test_parser.py
    ├── test_datatypes.py
    ├── test_references.py
    ├── test_sanitization.py
    ├── test_exporter.py
    ├── test_special_cases.py
    └── fixtures/                   # RBXLX test fixture files
```

---

## Installation

### Requirements
- Python 3.10, 3.11, or 3.12.
- No external libraries required for running the extractor.

### Optional: Install as CLI tool
```powershell
pip install -e .
```
This enables the `rbxlx-extractor` command directly in your shell.

### Optional: Install test runner
```powershell
pip install -r requirements.txt
```

---

## CLI Usage

### Basic Extraction
```powershell
python extractor.py save.rbxlx --output output/
```
Or if installed via pip:
```powershell
rbxlx-extractor save.rbxlx -o output/
```

### Options Reference

| Option | Description |
| :--- | :--- |
| `input` | Path to input `.rbxlx` file *(required)* |
| `-o`, `--output` | Destination output directory (default: `output/`) |
| `-v`, `--verbose` | Enable verbose logging and include full instance index in manifest |
| `-p`, `--pretty` | Pretty-print JSON files (`indent=2`) instead of compact single-line JSON |
| `--services` | Comma-separated list of top-level services to export (e.g. `--services ServerScriptService,ReplicatedStorage`) |
| `--rojo-style` | Use `init.server.lua` / `init.client.lua` / `init.lua` for scripts with children |
| `--no-properties`| Exclude properties block from `instance.json` metadata |
| `--no-scripts`   | Skip extracting script source files (export metadata only) |
| `--strict`       | Treat any warning or broken reference as a fatal error |

### Examples

#### 1. Extract only game scripts & modules (Fast):
```powershell
python extractor.py save.rbxlx -o output/ --services ServerScriptService,StarterPlayer,ReplicatedStorage --pretty
```

#### 2. Full place extraction with pretty JSON:
```powershell
python extractor.py save.rbxlx -o output/ --pretty
```

#### 3. Rojo-compatible script structure:
```powershell
python extractor.py save.rbxlx -o output/ --rojo-style
```

---

## Filesystem Output Structure

```
output/
├── manifest.json                   # Project summary, stats, script index
├── warnings.log                    # Any parser warnings or broken references
├── Workspace/
│   ├── instance.json
│   ├── BasePlate/
│   │   └── instance.json
│   └── Map/
│       ├── instance.json
│       └── House/
│           ├── instance.json
│           ├── Door/
│           │   └── instance.json
│           └── Window/
│               └── instance.json
├── ServerScriptService/
│   ├── instance.json
│   ├── Main.server.lua             # Direct server script
│   └── GunManager/                 # Script with child instances
│       ├── GunManager.server.lua   # Script source
│       ├── instance.json           # GunManager metadata
│       └── AmmoConfig/             # Child instance
│           └── instance.json
├── StarterPlayer/
│   └── StarterPlayerScripts/
│       ├── instance.json
│       └── ClientHandler.client.lua # Direct client script
└── ReplicatedStorage/
    └── Modules/
        ├── instance.json
        └── MathUtils.lua           # Module script
```

---

## Schema Formats

### `instance.json`
Generated for every non-script instance and for scripts containing children or metadata:

```json
{
  "className": "Part",
  "name": "Door",
  "referent": "RBX_DOOR",
  "path": "Workspace.Map.House.Door",
  "filesystemName": "Door",
  "uniqueId": "00000000-0000-0000-0000-000000000000",
  "tags": [
    "Interactable",
    "Metal"
  ],
  "attributes": {
    "OpenAngle": 90,
    "Locked": false
  },
  "properties": {
    "Anchored": true,
    "CanCollide": true,
    "Color": [0.38824, 0.37255, 0.38431],
    "Position": [0, 5, 0],
    "Size": [4, 7, 1],
    "Transparency": 0.0
  },
  "assets": {
    "TextureID": "rbxassetid://987654321"
  }
}
```

### `manifest.json`
Generated at the root of the output directory:

```json
{
  "format": "rbxlx-export",
  "version": 1,
  "source": {
    "file": "save.rbxlx",
    "sizeBytes": 369455784
  },
  "exportTimestamp": "2026-09-10T03:44:13.195650+00:00",
  "stats": {
    "totalInstances": 139018,
    "totalScripts": 291,
    "serverScripts": 0,
    "localScripts": 81,
    "moduleScripts": 210,
    "totalProperties": 4962084,
    "totalReferences": 0,
    "totalWarnings": 0
  },
  "services": [
    "StarterPlayer"
  ],
  "scripts": [
    {
      "referent": "RBX62640",
      "className": "LocalScript",
      "name": "RbxCharacterSounds",
      "robloxPath": "StarterPlayer.StarterPlayerScripts.RbxCharacterSounds",
      "filesystemPath": "StarterPlayer/StarterPlayerScripts/RbxCharacterSounds/RbxCharacterSounds.client.lua",
      "lines": 547,
      "sizeBytes": 18683
    }
  ],
  "warningsSummary": {
    "total": 0,
    "byCategory": {}
  }
}
```

### `warnings.log`
Records any warnings collected during parsing and reference resolution:
```
# RBXLX Extractor Warnings Log
# Generated: 2026-09-10T03:44:13.197878+00:00
# Total warnings/errors: 1

## Summary by Category
- BrokenReference: 1

## Details
[WARNING][BrokenReference] [Workspace.Car.TargetValue] Property 'Value' references missing referent 'RBX_GHOST'
```

---

## Testing & Quality Assurance

A comprehensive test suite covers all 15 scenarios requested in the specification:
- Empty place
- Simple Part & property parsing
- Nested Model & Folder hierarchies
- Script types (`.server.lua`, `.client.lua`, `.lua`)
- Scripts with child instances
- Duplicate instance names (sibling collisions)
- Special & illegal filesystem characters (`: * ? " < > | \ /`, control chars)
- Reserved Windows device names (`CON`, `PRN`, `AUX`, `NUL`, etc.)
- Trailing spaces and dots
- Object references & broken reference detection
- 20+ Roblox datatypes (CFrame, Vector3, Color3, UDim2, NumberSequence, Font, etc.)
- Unknown instance classes (graceful degradation)
- Unknown property XML tags (raw data preservation)

### Run Tests:
```powershell
python -m pytest tests/ -v
```

Output:
```
tests/test_datatypes.py::test_complex_datatypes PASSED                   [  6%]
tests/test_exporter.py::test_full_export_pipeline PASSED                 [ 12%]
tests/test_parser.py::test_parse_empty_place PASSED                      [ 18%]
tests/test_parser.py::test_parse_simple_part PASSED                      [ 25%]
tests/test_parser.py::test_parse_nested_model PASSED                     [ 31%]
tests/test_references.py::test_object_references_resolution PASSED       [ 37%]
tests/test_sanitization.py::test_sanitize_basic PASSED                   [ 43%]
tests/test_sanitization.py::test_sanitize_invalid_characters PASSED      [ 50%]
tests/test_sanitization.py::test_sanitize_reserved_windows_names PASSED  [ 56%]
tests/test_sanitization.py::test_sanitize_trailing_spaces_and_dots PASSED [ 62%]
tests/test_sanitization.py::test_sibling_collision_resolver PASSED       [ 68%]
tests/test_sanitization.py::test_sibling_collision_with_extensions PASSED [ 75%]
tests/test_sanitization.py::test_ensure_extended_path PASSED             [ 81%]
tests/test_special_cases.py::test_duplicate_names_export PASSED          [ 87%]
tests/test_special_cases.py::test_special_characters_export PASSED       [ 93%]
tests/test_special_cases.py::test_unknown_class_and_property PASSED      [100%]

============================= 16 passed in 0.60s ==============================
```

---

## Limitations & Fallback Behavior

1. **BinaryMesh / CSG Union Geometry**:
   - In RBXLX, `UnionOperation` and `MeshPart` geometry data is stored as compressed binary blocks (`PhysicsData`, `InitialData`).
   - The extractor preserves this raw data in `rawProperties` without attempting lossy re-tessellation.
2. **Obfuscated Strings**:
   - When strings contain non-printable control characters, `CleanReader` sanitizes control bytes into safe unicode replacement characters (`\ufffd`) to prevent XML parser fatal errors.
3. **Broken Object References**:
   - If an `ObjectValue` or `Ref` property points to a referent that does not exist in the file, it is flagged as `"status": "broken"` and logged in `warnings.log` without halting extraction.
