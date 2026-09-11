# Roblox RBXLX Extractor (Standalone)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)]()
[![GUI](https://img.shields.io/badge/Desktop%20GUI-Modern%20Dark-blueviolet.svg)]()
[![Executable](https://img.shields.io/badge/Windows%20EXE-Portable-success.svg)]()
[![Roblox-Studio](https://img.shields.io/badge/Roblox%20Studio-NOT%20Required-success.svg)]()

A high-performance, standalone tool to parse Roblox `.rbxlx` XML place files (and `.rbxmx` models) into an in-memory **Roblox Instance Tree** and export the entire project to the local filesystem with separated Lua/Luau scripts (`.server.lua`, `.client.lua`, `.lua`) and rich metadata (`instance.json`).

**100% Standalone:** Runs entirely without Roblox Studio, Studio CLI, or any Studio API. Available both as a **Portable Windows Executable (`.exe`) with a Modern Desktop GUI** and as a **Python CLI / Module**.

---

## Architecture Overview

```
save.rbxlx / model.rbxmx
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
│  - Full Mode vs. Simple Mode           │
│  - Path sanitization & collision logic │
│  - Scripts (.server.lua, .client.lua)  │
│  - Metadata (instance.json)            │
│  - Manifest (manifest.json)            │
│  - Warnings (warnings.log)             │
└────────────────────────────────────────┘
```

---

## Desktop GUI Application (`RBXLX_Extractor.exe`)

For users who prefer a graphical interface or want to run on machines without Python installed, the project includes a standalone Windows executable.

### How to Run:
- **Direct Executable (No Python Needed)**: Double-click [`RBXLX_Extractor.exe`](file:///d:/rbx/RBXLX_Extractor.exe)
- **From Source**: Run `python gui.py`

### Modern 2-Column Widescreen UI:
```text
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│  Roblox RBXLX Extractor                                                                        │
│  สกัดไฟล์ .rbxlx และ .rbxmx ออกมาเป็นโฟลเดอร์และ Lua/Luau Scripts                               │
├────────────────────────────────────────┬───────────────────────────────────────────────────────┤
│  [ ฝั่งซ้าย: เมนูควบคุม & ตั้งค่า ]    │  [ ฝั่งขวา: บันทึกการทำงาน (Live Console Log) ]        │
│                                        │                                                       │
│  📁 ไฟล์ต้นทาง (Input File)            │  📋 บันทึกการทำงาน                     [ล้าง Log]     │
│  [ Path/to/file.rbxlx  ] [Browse...]   │  ┌─────────────────────────────────────────────────┐ │
│                                        │  │ [PARSER] Opening 'save.rbxlx' (102.0 MB)...    │ │
│  📂 โฟลเดอร์ปลายทาง (Output Directory) │  │ [PARSER] Successfully parsed 34628 instances... │ │
│  [ Path/to/output_dir  ] [Browse...]   │  │ [RESOLVER] Resolved 3506/27232 references...   │ │
│                                        │  │ [EXPORTER] Export completed: 767 scripts...     │ │
│  ⚙️ เลือกโหมดการทำงาน (2 โหมด):        │  │ Manifest saved to: output\manifest.json         │ │
│  (o) ⚡ โหมดแบบง่าย (Scripts Only)     │  │                                                 │ │
│  ( ) 📁 โหมดโครงสร้างเดิม (Full)       │  │                                                 │ │
│                                        │  │                                                 │ │
│  [v] จัดรูปแบบ JSON ให้อ่านง่าย        │  │                                                 │ │
│                                        │  │                                                 │ │
│  [ 🚀 เริ่มแตกไฟล์ ] [ 📂 เปิดโฟลเดอร์ ]│  │                                                 │ │
│  สถานะ: พร้อมทำงาน (Ready)             │  │                                                 │ │
│  [========= Progress Bar =========]    │  └─────────────────────────────────────────────────┘ │
└────────────────────────────────────────┴───────────────────────────────────────────────────────┘
```

### The 2 Extraction Modes:
1. **⚡ โหมดแบบง่าย (Simple Mode - เฉพาะ Scripts & Code)**:
   - สกัดเฉพาะโค้ดและสคริปต์ (`.server.lua`, `.client.lua`, `.lua`) จัดโครงสร้างตาม Service โฟลเดอร์
   - **รวดเร็วมาก**: ไม่สร้างโฟลเดอร์พาร์ทที่ว่างเปล่า และไม่สร้างไฟล์ `instance.json` นับหมื่นไฟล์ เหมาะมากสำหรับคนที่ต้องการแค่อ่านโค้ด ศึกษา หรือแก้ไขสคริปต์
2. **📁 โหมดโครงสร้างเดิม (Full Hierarchy + Metadata)**:
   - แตกโครงสร้างเต็มรูปแบบ 100% เหมือนใน Studio ทุกชิ้น (Parts, Models, Folders, GUI, Attachments)
   - มีไฟล์ `instance.json` บันทึก properties/referent อย่างละเอียดทุกชิ้น เหมาะสำหรับนำไปวิเคราะห์หรือ Reconstruct โปรเจกต์กลับในอนาคต

### Built-in Error Checking & Notifications:
- ⚠️ **Missing Input/Output Warning**: เด้งหน้าต่างแจ้งเตือนทันทีหากยังไม่ได้เลือกไฟล์หรือระบุโฟลเดอร์
- 🚫 **.rbxl Binary Warning**: หากผู้ใช้เผลอเลือกไฟล์ Binary `.rbxl` แทนที่จะเป็น XML `.rbxlx` โปรแกรมจะเด้งหน้าต่างแนะนำวิธีการ Save as `.rbxlx` จาก Roblox Studio ให้อย่างละเอียด
- ❌ **Runtime Crash Prevention**: ครอบคลุม Exception ป้องกันการดับเอง พร้อมแสดง Error Message ชัดเจน
- 📋 **Live Warning Tracker**: แสดงคำเตือน `[WARNING]` ในหน้าต่าง Log แบบ Real-time และสรุปลงใน `warnings.log`
- ✅ **Success Dialog**: แสดงเวลารวม จำนวน Script ที่ได้ พร้อมปุ่มกดเปิดโฟลเดอร์ผลลัพธ์ทันที

---

## Comparison: GUI Choices vs. CLI Commands

| ตัวเลือกบนหน้าต่างโปรแกรม (GUI) | เทียบเท่ากับคำสั่ง CLI | คำอธิบาย |
| :--- | :--- | :--- |
| **📁 ไฟล์ต้นทาง (Input File)** | `"path/to/game.rbxlx"` | ระบุ Path ไฟล์ `.rbxlx` หรือ `.rbxmx` |
| **📂 โฟลเดอร์ปลายทาง (Output Directory)** | `-o "output/"` หรือ `--output "output/"` | ระบุตำแหน่งโฟลเดอร์สำหรับบันทึกผลลัพธ์ |
| **⚡ โหมดแบบง่าย (Simple)** | `--simple` หรือ `--mode simple` | สกัดเฉพาะไฟล์ Scripts และโฟลเดอร์ที่เกี่ยวข้อง |
| **📁 โหมดโครงสร้างเดิม (Full)** | `--mode full` *(ค่าเริ่มต้น)* | แตกทุกชิ้น ทุกโมเดล ทุกพาร์ท พร้อมไฟล์ `instance.json` |
| **☑️ จัดรูปแบบ JSON ให้อ่านง่าย** | `-p` หรือ `--pretty` | สั่งให้ `instance.json` และ `manifest.json` ย่อหน้าสวยงาม |
| **⬜ ไม่ติ๊ก JSON ให้อ่านง่าย** | *(ไม่ต้องใส่ flag `--pretty`)* | บันทึก JSON บรรทัดเดียวเพื่อความเร็วสูงสุดและประหยัดพื้นที่ดิสก์ |

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
   - Vector2, Vector3, CoordinateFrame (CFrame matrix + position), OptionalCoordinateFrame, Color3, Color3uint8, BrickColor, UDim, UDim2, NumberRange, NumberSequence, ColorSequence, Rect2D, Font, PhysicalProperties, Ref, Content, BinaryString, SharedString, UniqueId, SecurityCapabilities.
   - Any unknown datatype is stored in `rawProperties` so **zero data is lost**.
7. **Asset ID Detection**:
   - Detects asset references (`MeshId`, `TextureID`, `SoundId`, `AnimationId`, `Image`, `rbxassetid://`, etc.) and surfaces them in metadata.
8. **Bidirectional Reconstruction Ready**:
   - All referent IDs, original names, parent paths, and property structures are recorded in `instance.json` and `manifest.json`, allowing a future importer to reconstruct the place without Studio.

---

## Directory Layout

```
d:/rbx/
├── RBXLX_Extractor.exe             # Standalone Windows GUI executable (Portable, no Python needed)
├── gui.py                          # Modern Desktop GUI application source code
├── extractor.py                    # Root CLI entry point
├── pyproject.toml                  # Package configuration & console script
├── requirements.txt                # Development dependencies
├── README.md                       # Comprehensive documentation
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

## Installation & Setup

### Option 1: Standalone Windows .EXE (Fastest - No Python Needed)
You can directly run the pre-built standalone executable:
```powershell
.\RBXLX_Extractor.exe
```
This opens the modern desktop GUI window. It requires **zero Python installation** on the machine.

### Option 2: Run via Python
- Requires Python 3.10, 3.11, or 3.12.
- Core CLI extractor has **zero dependencies**.
- If running the GUI via source, install CustomTkinter:
  ```powershell
  pip install customtkinter
  python gui.py
  ```

### Option 3: Install as System CLI Tool
```powershell
pip install -e .
```
This enables the `rbxlx-extractor` command directly in your shell.

---

## CLI Usage

### Basic Extraction
```powershell
# Full hierarchy mode (default)
python extractor.py save.rbxlx --output output/

# Simple mode (scripts only - fast & clean)
python extractor.py save.rbxlx -o output/ --simple

# With pretty-printed JSON
python extractor.py save.rbxlx -o output/ --pretty
```

### Options Reference

| Option | Description |
| :--- | :--- |
| `input` | Path to input `.rbxlx` or `.rbxmx` file *(required)* |
| `-o`, `--output` | Destination output directory (default: `output/`) |
| `--mode` | Export mode: `full` (default) or `simple` (scripts only) |
| `--simple` | Shortcut for `--mode simple` (fast, scripts-only export) |
| `-v`, `--verbose` | Enable verbose logging and include full instance index in manifest |
| `-p`, `--pretty` | Pretty-print JSON files (`indent=2`) instead of compact single-line JSON |
| `--services` | Comma-separated list of top-level services to export (e.g. `--services ServerScriptService,ReplicatedStorage`) |
| `--rojo-style` | Use `init.server.lua` / `init.client.lua` / `init.lua` for scripts with children |
| `--no-properties`| Exclude properties block from `instance.json` metadata |
| `--no-scripts`   | Skip extracting script source files (export metadata only) |
| `--strict`       | Treat any warning or broken reference as a fatal error |

### CLI Examples

#### 1. Extract scripts only with pretty JSON (Fast):
```powershell
python extractor.py save.rbxlx -o output/ --simple --pretty
```

#### 2. Extract only game services:
```powershell
python extractor.py save.rbxlx -o output/ --services ServerScriptService,StarterPlayer,ReplicatedStorage --pretty
```

#### 3. Full place extraction with pretty JSON:
```powershell
python extractor.py save.rbxlx -o output/ --pretty
```

#### 4. Rojo-compatible script structure:
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
    "sizeBytes": 107003837
  },
  "exportTimestamp": "2026-09-10T04:03:33.758488+00:00",
  "stats": {
    "totalInstances": 34628,
    "totalScripts": 767,
    "serverScripts": 278,
    "localScripts": 235,
    "moduleScripts": 254,
    "totalProperties": 1498829,
    "totalReferences": 27232,
    "totalWarnings": 0
  },
  "services": [
    "Workspace",
    "ServerScriptService",
    "ReplicatedStorage",
    "StarterPlayer",
    "StarterGui"
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

---

## Testing & Quality Assurance

A comprehensive test suite covers all scenarios requested in the specification:
```powershell
python -m pytest tests/ -v
```

Output:
```
tests/test_datatypes.py::test_complex_datatypes PASSED                   [  5%]
tests/test_exporter.py::test_full_export_pipeline PASSED                 [ 11%]
tests/test_exporter.py::test_simple_mode_export PASSED                   [ 17%]
tests/test_parser.py::test_parse_empty_place PASSED                      [ 23%]
tests/test_parser.py::test_parse_simple_part PASSED                      [ 29%]
tests/test_parser.py::test_parse_nested_model PASSED                     [ 35%]
tests/test_references.py::test_object_references_resolution PASSED       [ 41%]
tests/test_sanitization.py::test_sanitize_basic PASSED                   [ 47%]
tests/test_sanitization.py::test_sanitize_invalid_characters PASSED      [ 52%]
tests/test_sanitization.py::test_sanitize_reserved_windows_names PASSED  [ 58%]
tests/test_sanitization.py::test_sanitize_trailing_spaces_and_dots PASSED [ 64%]
tests/test_sanitization.py::test_sibling_collision_resolver PASSED       [ 70%]
tests/test_sanitization.py::test_sibling_collision_with_extensions PASSED [ 76%]
tests/test_sanitization.py::test_ensure_extended_path PASSED             [ 82%]
tests/test_special_cases.py::test_duplicate_names_export PASSED          [ 88%]
tests/test_special_cases.py::test_special_characters_export PASSED       [ 94%]
tests/test_special_cases.py::test_unknown_class_and_property PASSED      [100%]

============================= 17 passed in 0.31s ==============================
```
