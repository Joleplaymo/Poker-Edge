"""Convert YOLOv8 .pt card model to ONNX (FP32) + INT8 quantized for browser deployment.

Usage:
    python scripts/convert_card_model.py

Inputs:
    models/cards/yolov8m_synthetic.pt

Outputs:
    models/cards/yolov8m_synthetic.onnx          (FP32, ~100 MB)
    models/cards/yolov8m_synthetic.int8.onnx     (INT8 dynamic, ~25 MB)
    models/cards/labels.json                     (52-class names)
"""

import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models" / "cards"
PT_PATH = MODEL_DIR / "yolov8m_synthetic.pt"
ONNX_PATH = MODEL_DIR / "yolov8m_synthetic.onnx"
INT8_PATH = MODEL_DIR / "yolov8m_synthetic.int8.onnx"
LABELS_PATH = MODEL_DIR / "labels.json"

if not PT_PATH.exists():
    sys.exit(f"Missing input: {PT_PATH}")

from ultralytics import YOLO

print(f"[1/3] Loading {PT_PATH.name}...")
model = YOLO(str(PT_PATH))

print(f"      Class count: {len(model.names)}")
LABELS_PATH.write_text(json.dumps(model.names, indent=2), encoding="utf-8")
print(f"      Labels saved: {LABELS_PATH.name}")

print(f"[2/3] Exporting to ONNX (opset=12, imgsz=640)...")
exported = model.export(format="onnx", opset=12, imgsz=640, dynamic=False, simplify=True)
exported_path = Path(exported)
if exported_path != ONNX_PATH:
    exported_path.replace(ONNX_PATH)
print(f"      ONNX FP32: {ONNX_PATH.name} ({ONNX_PATH.stat().st_size/1e6:.1f} MB)")

print(f"[3/3] Quantizing INT8 dynamic...")
from onnxruntime.quantization import quantize_dynamic, QuantType
quantize_dynamic(
    str(ONNX_PATH),
    str(INT8_PATH),
    weight_type=QuantType.QUInt8,
)
print(f"      ONNX INT8: {INT8_PATH.name} ({INT8_PATH.stat().st_size/1e6:.1f} MB)")
print("Done.")
