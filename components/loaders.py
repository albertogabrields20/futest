import json
import zipfile
import io
import math
from collections import defaultdict
from PIL import Image


def load_zip(uploaded):
    frames = None
    frame_images = {}
    metricas = None
    with zipfile.ZipFile(io.BytesIO(uploaded.read())) as z:
        for name in z.namelist():
            if name.endswith("metricas.json"):
                with z.open(name) as f:
                    metricas = json.load(f)
            elif name.endswith(".json"):
                with z.open(name) as f:
                    raw = json.load(f)
                if isinstance(raw, dict) and "frames" in raw:
                    frames = raw["frames"]
                elif isinstance(raw, list):
                    frames = raw
                else:
                    frames = []
            elif name.lower().endswith((".jpg", ".jpeg", ".png")):
                stem = name.split("/")[-1].rsplit(".", 1)[0]
                digits = "".join(c for c in stem if c.isdigit())
                if digits:
                    idx = int(digits)
                    with z.open(name) as f:
                        frame_images[idx] = Image.open(
                            io.BytesIO(f.read())
                        ).convert("RGB")
    return frames, frame_images, metricas


def get_jugadores(frame):
    if isinstance(frame, dict):
        return frame.get("jugadores", [])
    elif isinstance(frame, list):
        return [d for d in frame if isinstance(d, dict)]
    return []


def get_pos(det):
    pos = det.get("pos_2d_smooth", det.get("pos_2d", None))
    if pos is not None:
        return float(pos[0]), float(pos[1])
    return det.get("x", 0.0), det.get("y", 0.0)


def get_pid(det):
    return det.get("track_id", det.get("id", -1))


def get_team(det):
    return det.get("equipo", det.get("team", -1))
