from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from haunted_blender.dream_cutout_compiler import KIT_SCHEMA, render_sixup
from haunted_blender.dreambreeder import create_ecology


def main() -> int:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required.")

    root = Path("output/dream-cutout-004-demo").resolve()
    root.mkdir(parents=True, exist_ok=True)
    assets = root / "assets"
    assets.mkdir(exist_ok=True)

    width, height = 320, 180

    bg = Image.new("RGBA", (width, height), (28, 34, 48, 255))
    draw = ImageDraw.Draw(bg)
    draw.rectangle((0, 126, width, height), fill=(90, 64, 42, 255))
    draw.polygon([(0, 128), (86, 88), (150, 126)], fill=(66, 55, 47, 255))
    draw.polygon([(116, 126), (232, 70), (320, 120), (320, 150)], fill=(78, 61, 45, 255))
    bg.save(assets / "background.png")

    actor = Image.new("RGBA", (60, 98), (0, 0, 0, 0))
    d = ImageDraw.Draw(actor)
    d.ellipse((18, 2, 42, 26), fill=(225, 186, 125, 255))
    d.rectangle((15, 25, 45, 72), fill=(174, 111, 62, 255))
    d.polygon([(15, 70), (29, 96), (8, 96)], fill=(54, 61, 70, 255))
    d.polygon([(45, 70), (52, 96), (31, 96)], fill=(54, 61, 70, 255))
    actor.save(assets / "actor.png")

    arm = Image.new("RGBA", (52, 18), (0, 0, 0, 0))
    ImageDraw.Draw(arm).rounded_rectangle((0, 4, 50, 14), radius=4, fill=(214, 164, 105, 255))
    arm.save(assets / "arm.png")

    prop = Image.new("RGBA", (48, 64), (0, 0, 0, 0))
    pd = ImageDraw.Draw(prop)
    pd.rectangle((4, 6, 44, 60), fill=(118, 78, 45, 255))
    pd.rectangle((10, 12, 38, 54), outline=(216, 178, 105, 255), width=3)
    prop.save(assets / "door.png")

    light = Image.new("RGBA", (92, 92), (255, 220, 125, 0))
    ld = ImageDraw.Draw(light)
    for r in range(44, 4, -4):
        alpha = max(8, int(110 * (1 - r / 48)))
        ld.ellipse((46-r, 46-r, 46+r, 46+r), fill=(255, 225, 135, alpha))
    light.save(assets / "light.png")

    foreground = Image.new("RGBA", (140, 60), (0, 0, 0, 0))
    fd = ImageDraw.Draw(foreground)
    for x in range(0, 140, 12):
        fd.line((x, 60, x + 8, 18 + (x % 24)), fill=(165, 123, 69, 220), width=3)
    foreground.save(assets / "grass.png")

    donor_ids = [f"flow-video:demo-{i}" for i in range(1, 7)]
    donor_map = {}
    for i, donor_id in enumerate(donor_ids, start=1):
        video = assets / f"donor-{i}.mp4"
        color = ["#553322", "#335566", "#665533", "#224455", "#665544", "#334433"][i - 1]
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi",
                "-i", f"color=c={color}:s=160x90:d=2:r=12",
                "-vf", f"drawbox=x='mod(t*35\\,120)':y={8+i*4}:w=32:h=32:color=white@0.55:t=fill",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video),
            ],
            check=True,
        )
        donor_map[donor_id] = str(video)

    ecology = create_ecology(
        relation_id="demo-relation-004",
        common_checkpoint_id="demo-checkpoint-004",
        source_receipt_ids=["demo-receipt-left", "demo-receipt-right"],
        donor_ids=donor_ids,
    )
    kit = {
        "schema": KIT_SCHEMA,
        "canvas": {"width": width, "height": height},
        "donorScale": 0.38,
        "layers": [
            {"id": "background", "role": "background", "source": str(assets / "background.png"), "z": 0, "x": 0, "y": 0},
            {"id": "light", "role": "light", "source": str(assets / "light.png"), "z": 1, "x": 214, "y": 4, "opacity": 0.25},
            {"id": "door", "role": "prop", "source": str(assets / "door.png"), "z": 2, "x": 246, "y": 93},
            {"id": "actor", "role": "actor", "source": str(assets / "actor.png"), "z": 3, "x": 72, "y": 66},
            {"id": "arm", "role": "arm-right", "source": str(assets / "arm.png"), "z": 4, "x": 108, "y": 103, "rotation": -8},
            {"id": "grass", "role": "foreground", "source": str(assets / "grass.png"), "z": 60, "x": 0, "y": 124, "opacity": 0.9},
        ],
    }

    (root / "ecology.json").write_text(json.dumps(ecology, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "kit.json").write_text(json.dumps(kit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "donor-map.json").write_text(json.dumps(donor_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = render_sixup(
        ecology,
        kit,
        root / "previews",
        duration=2.0,
        fps=12,
        donor_video_by_id=donor_map,
    )
    print(result["contactSheetVideo"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
