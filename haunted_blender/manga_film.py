"""FRANKEN BLENDER 008o — Page Five Manga Film.

Consumes an admitted 008n particular-performance plan and renders a deterministic
limited-animation manga short with deterministic source-specific sound.

This renderer does not invent source facts. It visualizes admitted staging while
retaining each performed beat's source-particular hash in the render receipt.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import shutil
import struct
import subprocess
import tempfile
import textwrap
import wave
from pathlib import Path

from . import narrative_performance

RECEIPT_SCHEMA = "haunted-blender/manga-film-render-receipt/v1"
AUDIO_SCHEMA = "haunted-blender/manga-film-audio-plan/v1"


def _stable(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _font(size: int):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _probe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    raw = json.loads(proc.stdout)
    video = next(
        (s for s in (raw.get("streams") or []) if s.get("codec_type") == "video"),
        None,
    )
    audio = next(
        (s for s in (raw.get("streams") or []) if s.get("codec_type") == "audio"),
        None,
    )
    if not video:
        raise ValueError("008o render has no video stream")
    return {
        "durationSeconds": round(float((raw.get("format") or {}).get("duration") or 0), 6),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "frameRate": str(video.get("r_frame_rate") or ""),
        "videoCodec": video.get("codec_name"),
        "hasAudio": audio is not None,
        "audioCodec": audio.get("codec_name") if audio else None,
    }


def _beat_for_time(plan: dict, t: float) -> tuple[int, dict]:
    beats = plan.get("beats") or []
    if not beats:
        raise ValueError("008o requires at least one admitted performance beat")
    for index, beat in enumerate(beats):
        if float(beat["start"]) <= t < float(beat["end"]):
            return index, beat
    return len(beats) - 1, beats[-1]


def _local_progress(beat: dict, t: float) -> float:
    start = float(beat["start"])
    end = float(beat["end"])
    if end <= start:
        return 1.0
    return min(1.0, max(0.0, (t - start) / (end - start)))


def _ink(seed: str, salt: int) -> int:
    digest = hashlib.sha256(f"{seed}:{salt}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _draw_caption(draw, beat: dict, width: int, height: int) -> None:
    margin = max(10, width // 45)
    band_h = max(62, height // 5)
    top = height - band_h
    draw.rectangle((0, top, width, height), fill=(249, 247, 240, 244))
    draw.line((0, top, width, top), fill=(28, 28, 26, 255), width=max(1, width // 320))
    title = str(beat.get("sourceText") or beat.get("sourceParticularId") or "")
    staging = str(beat.get("staging") or "")
    hash_short = str(beat.get("sourceParticularHash") or "")[:12]
    draw.text(
        (margin, top + 8),
        title,
        fill=(15, 15, 14, 255),
        font=_font(max(14, width // 34)),
    )
    wrapped = textwrap.wrap(staging, width=max(28, width // 10))[:2]
    if wrapped:
        draw.multiline_text(
            (margin, top + 30),
            "\n".join(wrapped),
            fill=(75, 73, 68, 255),
            font=_font(max(10, width // 55)),
            spacing=2,
        )
    draw.text(
        (width - max(120, width // 4), top + 9),
        f"SRC {hash_short}",
        fill=(110, 108, 103, 255),
        font=_font(max(9, width // 62)),
    )


def _draw_panel_frame(draw, width: int, height: int, seed: str, t: float) -> None:
    inset = max(8, width // 80)
    wobble = ((_ink(seed, int(t * 12) + 1) % 5) - 2)
    draw.rectangle(
        (inset + wobble, inset, width - inset, height - inset),
        outline=(20, 20, 19, 255),
        width=max(2, width // 220),
    )
    # sparse deterministic paper marks
    for i in range(12):
        x = 12 + (_ink(seed, 100 + i) % max(1, width - 24))
        y = 12 + (_ink(seed, 200 + i) % max(1, height - 90))
        r = 1 + (_ink(seed, 300 + i) % 2)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(188, 184, 172, 120))


def _draw_guitar(draw, width: int, height: int, u: float) -> None:
    cy = int(height * 0.39)
    amp = max(2, int(width * 0.012 * (1.0 - u)))
    for lane in range(5):
        y0 = cy + (lane - 2) * max(7, height // 38)
        points = []
        for x in range(int(width * 0.10), int(width * 0.90), 5):
            phase = (x / max(1, width)) * math.pi * 12 + u * math.pi * 7
            y = y0 + math.sin(phase) * amp
            points.append((x, int(y)))
        draw.line(points, fill=(18, 18, 18, 255), width=2)
    draw.ellipse(
        (int(width*.70), int(height*.27), int(width*.84), int(height*.51)),
        outline=(25,25,25,255), width=3,
    )


def _draw_mug_lid(draw, width: int, height: int, u: float) -> None:
    jitter = int(math.sin(u * math.pi * 18) * max(2, width * 0.008) * (1-u))
    cx, cy = int(width*.5)+jitter, int(height*.38)
    rw, rh = int(width*.22), int(height*.075)
    draw.ellipse((cx-rw, cy-rh, cx+rw, cy+rh), fill=(230,228,219,255),
                 outline=(18,18,18,255), width=4)
    draw.line((cx-rw, cy+rh+10, cx+rw, cy+rh+10), fill=(80,78,73,255), width=3)


def _draw_breath(draw, width: int, height: int, u: float) -> None:
    # abstract profile + three visible breath arcs, not identity reconstruction
    cx, cy = int(width*.35), int(height*.35)
    draw.ellipse((cx-50, cy-80, cx+45, cy+70), outline=(24,24,23,255), width=4)
    draw.line((cx+40, cy-8, cx+72, cy+2), fill=(24,24,23,255), width=3)
    fade = max(0.15, 1.0 - u)
    for i in range(3):
        x = cx + 80 + i * 52 + int(u * 25)
        y = cy - 18 + i * 10
        tone = int(125 + 70 * (1-fade))
        draw.arc((x, y-22, x+62, y+26), 205, 335, fill=(tone,tone,tone,255), width=3)


def _draw_spring(draw, width: int, height: int, u: float) -> None:
    x0 = int(width*.20)
    x1 = int(width*.80)
    cy = int(height*.38)
    coils = 10
    compression = 0.72 + 0.28 * min(1.0, u*1.6)
    span = (x1-x0) * compression
    start = (width-span)/2
    pts=[]
    for i in range(coils*12+1):
        f=i/(coils*12)
        x=start+span*f
        y=cy+math.sin(f*coils*2*math.pi)*max(12,height*.055)
        pts.append((int(x),int(y)))
    draw.line(pts, fill=(20,20,19,255), width=4)
    draw.rectangle((x0-20,cy-65,x0,cy+65), fill=(70,68,64,255))
    draw.rectangle((x1,cy-65,x1+20,cy+65), fill=(70,68,64,255))


def _draw_fingers_rail(draw, width: int, height: int, u: float) -> None:
    rail_y=int(height*.47)
    draw.line((int(width*.12),rail_y,int(width*.88),rail_y),fill=(25,25,24,255),width=8)
    base_x=int(width*.42)
    tap=int(abs(math.sin(u*math.pi*3))*18)
    for i in range(4):
        x=base_x+i*22
        top=int(height*.24)+i*3
        bottom=rail_y-tap if i==1 else rail_y
        draw.rounded_rectangle((x,top,x+15,bottom),radius=7,fill=(183,177,163,255),
                               outline=(28,28,27,255),width=2)


def _draw_window(draw, width: int, height: int, u: float) -> None:
    shake=int(math.sin(u*math.pi*20)*max(1,width*.006)*(1-u*.5))
    x1,x2=int(width*.27)+shake,int(width*.73)+shake
    y1,y2=int(height*.18),int(height*.55)
    draw.rectangle((x1,y1,x2,y2),outline=(20,20,20,255),width=7)
    draw.line(((x1+x2)//2,y1,(x1+x2)//2,y2),fill=(55,55,53,255),width=3)
    draw.line((x1,(y1+y2)//2,x2,(y1+y2)//2),fill=(55,55,53,255),width=3)
    for i in range(7):
        yy=y1+20+i*22
        draw.line((x2+12,yy,x2+36,yy+shake),fill=(110,108,102,255),width=2)


def _draw_blinker(draw, width: int, height: int, u: float) -> None:
    # watcher at left, blinking dashboard particular at right
    cx,cy=int(width*.30),int(height*.36)
    draw.ellipse((cx-54,cy-65,cx+54,cy+65),outline=(24,24,23,255),width=4)
    draw.arc((cx-22,cy-15,cx+28,cy+18),190,350,fill=(24,24,23,255),width=3)
    on = int(u*4) % 2 == 0
    bx,by=int(width*.73),int(height*.38)
    draw.rounded_rectangle((bx-50,by-28,bx+50,by+28),radius=10,
                           fill=((45,45,42,255) if on else (220,218,210,255)),
                           outline=(18,18,18,255),width=3)
    # negative-space beat marks
    for i in range(3):
        x=bx-130+i*36
        draw.line((x,by+62,x+18,by+62),fill=(130,127,120,255),width=2)


def _draw_wide_bus(draw, width: int, height: int, u: float) -> None:
    x1,y1,x2,y2=int(width*.08),int(height*.12),int(width*.92),int(height*.60)
    draw.rounded_rectangle((x1,y1,x2,y2),radius=24,outline=(18,18,18,255),width=6)
    # windows
    for i in range(4):
        wx1=x1+32+i*int((x2-x1-64)/4)
        wx2=wx1+int((x2-x1-88)/4)
        draw.rectangle((wx1,y1+30,wx2,y1+125),outline=(70,68,65,255),width=3)
    # seat rails
    draw.line((x1+45,y2-95,x2-45,y2-95),fill=(35,35,34,255),width=6)
    # recurring particulars, reduced to stable glyphs
    draw.line((x1+80,y2-150,x1+190,y2-150),fill=(25,25,24,255),width=2)
    draw.ellipse((x1+215,y2-175,x1+285,y2-145),outline=(25,25,24,255),width=2)
    # blinker keeps ordinary timing
    on=int(u*5)%2==0
    bx=x2-95
    by=y2-65
    draw.rectangle((bx-18,by-12,bx+18,by+12),
                   fill=((35,35,33,255) if on else (220,218,210,255)),
                   outline=(20,20,20,255),width=2)


def _draw_frame(plan: dict, frame_index: int, fps: int, width: int, height: int):
    from PIL import Image, ImageDraw

    t = frame_index / fps
    beat_index, beat = _beat_for_time(plan, t)
    u = _local_progress(beat, t)
    image = Image.new("RGBA", (width, height), (242, 239, 229, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    seed = str(beat.get("sourceParticularHash") or beat["id"])
    _draw_panel_frame(draw, width, height, seed, t)

    pid = beat["sourceParticularId"]
    if pid == "p-guitar-string":
        _draw_guitar(draw, width, height, u)
    elif pid == "p-mug-lid":
        _draw_mug_lid(draw, width, height, u)
    elif pid == "p-grace-breath":
        _draw_breath(draw, width, height, u)
    elif pid == "p-seat-spring":
        _draw_spring(draw, width, height, u)
    elif pid == "p-fingers-rail":
        _draw_fingers_rail(draw, width, height, u)
    elif pid == "p-window-edge":
        _draw_window(draw, width, height, u)
    elif pid == "p-lumi-blinker":
        _draw_blinker(draw, width, height, u)
    else:
        _draw_wide_bus(draw, width, height, u)

    draw.text(
        (max(12,width//45), max(12,height//40)),
        f"{beat_index+1:02d} / {len(plan['beats']):02d}   {beat['type']}",
        fill=(80,78,73,255),
        font=_font(max(11,width//52)),
    )
    _draw_caption(draw, beat, width, height)
    return image.convert("RGB")


def _tone(samples: list[float], sample_rate: int, start: float, duration: float,
          freq: float, amp: float, *, decay: float = 4.0) -> None:
    first=max(0,int(start*sample_rate))
    count=max(1,int(duration*sample_rate))
    for i in range(count):
        idx=first+i
        if idx>=len(samples):
            break
        t=i/sample_rate
        env=math.exp(-decay*t/max(duration,1e-6))
        samples[idx]+=math.sin(2*math.pi*freq*t)*amp*env


def _noise(samples: list[float], sample_rate: int, start: float, duration: float,
           amp: float, seed: int, *, decay: float = 1.5) -> None:
    rng=random.Random(seed)
    first=max(0,int(start*sample_rate))
    count=max(1,int(duration*sample_rate))
    for i in range(count):
        idx=first+i
        if idx>=len(samples):
            break
        t=i/sample_rate
        env=math.exp(-decay*t/max(duration,1e-6))
        samples[idx]+=(rng.random()*2-1)*amp*env


def audio_plan(plan: dict, *, sample_rate: int = 16000) -> dict:
    narrative_performance._require_schema(plan, narrative_performance.PLAN_SCHEMA)
    events=[]
    for beat in plan["beats"]:
        pid=beat["sourceParticularId"]
        start=float(beat["start"])
        duration=float(beat["durationSeconds"])
        if pid=="p-guitar-string":
            event={"kind":"pluck","frequencyHz":220.0,"start":start,"duration":duration}
        elif pid=="p-mug-lid":
            event={"kind":"clink","frequencyHz":1320.0,"start":start,"duration":min(.22,duration)}
        elif pid=="p-grace-breath":
            event={"kind":"breath-noise","start":start,"duration":duration}
        elif pid=="p-seat-spring":
            event={"kind":"spring-pair","frequencyHz":155.0,"start":start,"duration":duration}
        elif pid=="p-fingers-rail":
            event={"kind":"tap","frequencyHz":720.0,"start":start,"duration":min(.28,duration)}
        elif pid=="p-window-edge":
            event={"kind":"rattle-noise","start":start,"duration":duration}
        elif pid=="p-lumi-blinker":
            event={"kind":"blinker-ticks","frequencyHz":980.0,"start":start,"duration":duration}
        else:
            event={"kind":"room-tone","frequencyHz":82.0,"start":start,"duration":duration}
        events.append({
            **event,
            "beatId":beat["id"],
            "sourceParticularId":pid,
            "sourceParticularHash":beat["sourceParticularHash"],
        })
    body={
        "schema":AUDIO_SCHEMA,
        "planId":plan["id"],
        "sampleRate":int(sample_rate),
        "durationSeconds":float(plan["durationSeconds"]),
        "events":events,
        "authority":"derived-performance-sound-only",
        "laws":[
            "SYNTHESIZED SOUND != SOURCE RECORDING",
            "AUDIBLE RHYME != CAUSAL PROOF",
            "AUDIO EVENT RETAINS SOURCE PARTICULAR HASH",
        ],
    }
    return {**body,"id":"manga-film-audio:"+_hash(body)[:24]}


def render_audio(audio: dict, output_path: str | Path) -> dict:
    if audio.get("schema")!=AUDIO_SCHEMA:
        raise ValueError("Expected 008o audio plan")
    out=Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("008o audio renderer never overwrites")
    out.parent.mkdir(parents=True,exist_ok=True)
    sr=int(audio["sampleRate"])
    duration=float(audio["durationSeconds"])
    samples=[0.0]*max(1,int(math.ceil(duration*sr)))

    for event in audio["events"]:
        kind=event["kind"]
        start=float(event["start"])
        dur=float(event["duration"])
        seed=int(event["sourceParticularHash"][:16],16)
        if kind=="pluck":
            _tone(samples,sr,start,dur,220,.26,decay=7)
            _tone(samples,sr,start,dur,440,.10,decay=9)
        elif kind=="clink":
            _tone(samples,sr,start,dur,1320,.24,decay=12)
            _tone(samples,sr,start,dur,1760,.11,decay=15)
        elif kind=="breath-noise":
            _noise(samples,sr,start,dur,.055,seed,decay=.25)
        elif kind=="spring-pair":
            _tone(samples,sr,start,dur,155,.19,decay=4)
            _tone(samples,sr,start+.08,max(.08,dur-.08),93,.13,decay=5)
        elif kind=="tap":
            _tone(samples,sr,start,.11,720,.22,decay=14)
            if dur>.16:
                _tone(samples,sr,start+.16,.09,560,.12,decay=14)
        elif kind=="rattle-noise":
            pulses=max(2,int(dur/.08))
            for i in range(pulses):
                _noise(samples,sr,start+i*.075,min(.045,dur),.045,seed+i,decay=6)
        elif kind=="blinker-ticks":
            tick=0.0
            while tick<dur-1e-6:
                _tone(samples,sr,start+tick,.055,980,.20,decay=18)
                tick+=.48
        else:
            _tone(samples,sr,start,dur,82,.018,decay=.02)

    peak=max(1e-9,max(abs(x) for x in samples))
    scale=min(1.0,.82/peak)
    with wave.open(str(out),"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        for value in samples:
            clipped=max(-1.0,min(1.0,value*scale))
            wav.writeframesraw(struct.pack("<h",int(clipped*32767)))
        wav.writeframes(b"")

    return {
        "audioPlanId":audio["id"],
        "path":str(out),
        "sha256":_file_sha(out),
        "byteLength":out.stat().st_size,
        "sampleRate":sr,
        "durationSeconds":duration,
    }


def render_plan(
    plan: dict,
    output_path: str | Path,
    *,
    width: int = 640,
    height: int = 360,
    fps: int = 12,
) -> dict:
    narrative_performance._require_schema(plan, narrative_performance.PLAN_SCHEMA)
    if width<160 or height<120 or fps<1:
        raise ValueError("invalid 008o render geometry")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and FFprobe are required")

    out=Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("008o renderer never overwrites")
    out.parent.mkdir(parents=True,exist_ok=True)
    duration=float(plan["durationSeconds"])
    frame_count=max(1,int(math.ceil(duration*fps)))
    audio=audio_plan(plan)

    with tempfile.TemporaryDirectory(prefix="haunted-blender-008o-") as td:
        root=Path(td)
        for frame_index in range(frame_count):
            image=_draw_frame(plan,frame_index,fps,width,height)
            image.save(root/f"frame-{frame_index:06d}.png")
        audio_receipt=render_audio(audio,root/"page-five.wav")
        subprocess.run(
            [
                "ffmpeg","-nostdin","-v","error","-y",
                "-framerate",str(fps),
                "-i",str(root/"frame-%06d.png"),
                "-i",str(root/"page-five.wav"),
                "-t",f"{duration:.6f}",
                "-c:v","libx264","-pix_fmt","yuv420p",
                "-c:a","aac","-b:a","128k",
                "-movflags","+faststart",
                str(out),
            ],
            check=True,
        )

    probe=_probe(out)
    beat_receipts=[]
    for beat in plan["beats"]:
        start=float(beat["start"])
        end=float(beat["end"])
        beat_receipts.append({
            "beatId":beat["id"],
            "sourceParticularId":beat["sourceParticularId"],
            "sourceParticularHash":beat["sourceParticularHash"],
            "shotType":beat["type"],
            "start":start,
            "end":end,
            "firstFrame":int(math.floor(start*fps)),
            "lastFrame":max(0,min(frame_count-1,int(math.ceil(end*fps))-1)),
        })

    body={
        "schema":RECEIPT_SCHEMA,
        "planId":plan["id"],
        "sourceId":plan["sourceId"],
        "proposalId":plan["proposalId"],
        "admissionId":plan["admissionId"],
        "adapter":"pillow-manga-film+stdlib-audio+ffmpeg/v1",
        "outputSha256":_file_sha(out),
        "outputByteLength":out.stat().st_size,
        "width":probe["width"],
        "height":probe["height"],
        "fps":fps,
        "frameCount":frame_count,
        "durationSeconds":probe["durationSeconds"],
        "hasAudio":probe["hasAudio"],
        "audioPlanId":audio["id"],
        "audioRenderSha256":audio_receipt["sha256"],
        "beats":beat_receipts,
        "beatCount":len(beat_receipts),
        "externalGenerations":0,
        "providerCredits":0,
        "usdMicros":0,
        "receiptAuthority":"none",
        "laws":[
            "VISIBLE PERFORMANCE != RETROACTIVE CANON",
            "SYNTHESIZED SOUND != SOURCE RECORDING",
            "AUDIBLE RHYME != CAUSAL PROOF",
            "EVERY RENDERED BEAT RETAINS SOURCE PARTICULAR HASH",
            "RENDER RECEIPT != SOURCE AUTHORITY",
        ],
    }
    return {**body,"id":"manga-film-render:"+_hash(body)[:24]}


def render_spec(
    spec: dict,
    output_dir: str | Path,
    *,
    width: int = 640,
    height: int = 360,
    fps: int = 12,
) -> dict:
    bundle=narrative_performance.compile_spec(spec)
    out=Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True,exist_ok=True)
    movie=out/"page-five-manga-film.mp4"
    receipt=render_plan(bundle["plan"],movie,width=width,height=height,fps=fps)
    receipt_path=out/"page-five-manga-film.receipt.json"
    if receipt_path.exists():
        raise FileExistsError("008o receipt already exists")
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return {
        "bundle":bundle,
        "movie":str(movie),
        "receipt":receipt,
        "receiptPath":str(receipt_path),
    }
