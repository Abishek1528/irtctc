"""Generate IRCTC Part B wireframe PNGs for assets/wireframes/."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "assets" / "wireframes"
W, H = 1200, 900
BG = (252, 252, 252)
FRAME = (220, 220, 220)
TEXT = (40, 40, 40)
LABEL = (0, 102, 180)
ANNOT = (180, 80, 0)
CHANGED = (200, 40, 40)
GOOD = (0, 130, 60)
MUTED = (120, 120, 120)
PHONE_W, PHONE_H = 320, 560


def font(size: int, bold: bool = False):
    names = ["arialbd.ttf", "Arial Bold.ttf", "arial.ttf", "Arial.ttf", "segoeui.ttf"]
    if bold:
        names = ["arialbd.ttf", "Arial Bold.ttf", "arialbd.ttf"] + names
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def new_canvas(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((24, 16), title, fill=TEXT, font=font(22, True))
    d.line([(24, 48), (W - 24, 48)], fill=FRAME, width=2)
    return img, d


def phone_frame(d, x, y, label: str):
    d.rounded_rectangle([x, y, x + PHONE_W, y + PHONE_H], radius=12, outline=TEXT, width=2)
    d.text((x + 8, y + 8), label, fill=LABEL, font=font(11, True))


def box(d, x, y, w, h, text: str, fill=(255, 255, 255), outline=FRAME, fs=10):
    d.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=fill, outline=outline, width=1)
    if text:
        d.text((x + 8, y + h // 2 - fs // 2), text, fill=TEXT, font=font(fs))


def note(d, x, y, text: str, color=ANNOT, fs=9):
    d.text((x, y), f"→ {text}", fill=color, font=font(fs))


def badge(d, x, y, text: str, color=CHANGED):
    tw = len(text) * 6 + 16
    d.rounded_rectangle([x, y, x + tw, y + 20], radius=4, fill=color)
    d.text((x + 8, y + 3), text, fill=(255, 255, 255), font=font(9, True))


def legend_panel(d, x, y):
    d.text((x, y), "LEGEND", fill=TEXT, font=font(11, True))
    items = [
        (LABEL, "Component label"),
        (ANNOT, "Interaction annotation"),
        (CHANGED, "Changed from Part A"),
        (GOOD, "New / fixed state"),
    ]
    for i, (c, t) in enumerate(items):
        d.rectangle([x, y + 22 + i * 22, x + 14, y + 36 + i * 22], fill=c)
        d.text((x + 20, y + 22 + i * 22), t, fill=TEXT, font=font(9))


def save(img: Image.Image, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    img.save(path, "PNG", optimize=True)
    print(f"Wrote {path}")


def wireframe_tatkal():
    img, d = new_canvas("Spec 1 — Tatkal Virtual Queue (Proposed vs Part A)")
    legend_panel(d, 24, 60)

    # BEFORE (broken)
    bx, by = 24, 130
    phone_frame(d, bx, by, "BEFORE (Part A)")
    box(d, bx + 16, by + 40, PHONE_W - 32, 36, "Booking…", fill=(245, 245, 245))
    d.text((bx + 40, by + 90), "(spinner only)", fill=MUTED, font=font(10))
    d.text((bx + 24, by + 130), "No queue position", fill=CHANGED, font=font(9))
    d.text((bx + 24, by + 150), "Silent timeout / quota msg", fill=CHANGED, font=font(9))
    badge(d, bx + 16, by + PHONE_H - 36, "BROKEN")

    # AFTER (proposed)
    ax = 340
    phone_frame(d, ax, by, "AFTER (Proposed)")
    box(d, ax + 16, by + 40, PHONE_W - 32, 28, "Tatkal Queue", fill=(230, 245, 255), outline=LABEL)
    box(d, ax + 16, by + 76, PHONE_W - 32, 48, "Queue position: #847 / ~12,000", fill=(255, 255, 255))
    note(d, ax + PHONE_W + 8, by + 88, "Tap — refresh status", ANNOT)
    box(d, ax + 16, by + 132, PHONE_W - 32, 24, "Progress bar", fill=(200, 230, 200), outline=GOOD)
    box(d, ax + 16, by + 164, PHONE_W - 32, 32, "ETA: ~2 min 15 sec", fill=(255, 255, 255))
    box(d, ax + 16, by + 204, PHONE_W - 32, 28, "Countdown to 10:00 AM", fill=(255, 255, 255))
    box(d, ax + 16, by + 240, PHONE_W - 32, 36, "Cancel queue button", fill=(255, 240, 240), outline=CHANGED)
    box(d, ax + 16, by + 286, PHONE_W - 32, 28, "My Queue (nav)", fill=(255, 255, 255))
    note(d, ax + 16, by + 322, "Leave app → return via My Queue", ANNOT)
    badge(d, ax + 16, by + PHONE_H - 36, "NEW UI", GOOD)

    # States row
    sx, sy = 700, 130
    d.text((sx, sy), "STATES", fill=TEXT, font=font(12, True))
    states = [
        ("Loading", "Joining queue…", (240, 240, 255)),
        ("Processing", "Confirming berth…", (255, 248, 220)),
        ("Success", "Booked — PNR shown", (220, 255, 220)),
        ("Error", "Quota full — try alt train", (255, 230, 230)),
        ("Empty", "Queue closed — retry 10 AM", (245, 245, 245)),
    ]
    for i, (title, msg, col) in enumerate(states):
        yy = sy + 28 + i * 72
        box(d, sx, yy, 460, 60, f"{title}: {msg}", fill=col, fs=11)

    d.text((24, H - 28), "Caption: Tatkal queue replaces silent spinner with position, ETA, outcomes", fill=MUTED, font=font(10))
    save(img, "tatkal-queue-screen.png")


def wireframe_filters():
    img, d = new_canvas("Spec 2 — Search Filters & Filter Chips")
    legend_panel(d, 24, 60)
    px, py = 24, 120
    phone_frame(d, px, py, "PROPOSED — Search Results")
    box(d, px + 16, py + 36, PHONE_W - 32, 28, "Route header (DEL → BOM)", fill=(255, 255, 255))
    box(d, px + 16, py + 70, PHONE_W - 32, 24, "12 trains (filtered from 48)", fill=(230, 245, 255), outline=GOOD)
    d.text((px + 20, py + 100), "Filter chip row:", fill=LABEL, font=font(9, True))
    box(d, px + 16, py + 116, 90, 26, "Sleeper ×", fill=(220, 235, 255), outline=LABEL)
    box(d, px + 112, py + 116, 90, 26, "Morning ×", fill=(220, 235, 255), outline=LABEL)
    box(d, px + 208, py + 116, 70, 26, "Clear all", fill=(255, 255, 255))
    note(d, px + 16, py + 148, "Tap chip × → removes filter & refetches", ANNOT)
    box(d, px + 16, py + 168, PHONE_W - 32, 52, "Train card (tap → details)", fill=(255, 255, 255))
    note(d, px + PHONE_W + 8, py + 180, "Tap card → train details", ANNOT)
    box(d, px + 16, py + 228, PHONE_W - 32, 52, "Train card 2", fill=(255, 255, 255))
    box(d, px + 16, py + 288, PHONE_W - 32, 40, "Refine Results panel", fill=(255, 255, 255))
    note(d, px + 16, py + 336, "Check filter → list updates <1s", ANNOT)

    # Comparison
    cx = 380
    d.text((cx, 120), "CHANGED FROM PART A", fill=CHANGED, font=font(12, True))
    for i, t in enumerate([
        "✗ Filter checked but list unchanged",
        "✓ Server-side filter + instant refresh",
        "✗ Back nav loses filter state",
        "✓ URL/session restores chips",
        "✗ Per-train Refresh races filters",
        "✓ Refresh sequenced / scoped",
    ]):
        d.text((cx, 150 + i * 22), t, fill=GOOD if t.startswith("✓") else CHANGED, font=font(10))

    # States
    sx, sy = 700, 120
    d.text((sx, sy), "LOADING / EMPTY / ERROR", fill=TEXT, font=font(12, True))
    box(d, sx, sy + 30, 460, 55, "Loading: skeleton train cards", fill=(240, 240, 240))
    box(d, sx, sy + 95, 460, 55, "Empty: No trains match — Clear filters", fill=(255, 248, 220))
    box(d, sx, sy + 160, 460, 55, "Error: Filters unavailable — showing last results", fill=(255, 230, 230))
    save(img, "search-filters-results.png")


def wireframe_seat():
    img, d = new_canvas("Spec 3 — Seat Map with Berth Hold")
    px, py = 24, 80
    phone_frame(d, px, py, "Seat Map — Proposed")
    box(d, px + 16, py + 36, PHONE_W - 32, 32, "Held: Berth B2 until 10:42 AM", fill=(220, 255, 220), outline=GOOD)
    note(d, px + 16, py + 74, "Tap berth → hold API + highlight", ANNOT)
    for row in range(4):
        for col in range(4):
            x = px + 24 + col * 68
            y = py + 100 + row * 44
            sel = row == 1 and col == 1
            box(d, x, y, 60, 36, "B2" if sel else "—", fill=(180, 220, 255) if sel else (255, 255, 255), outline=GOOD if sel else FRAME, fs=9)
    box(d, px + 16, py + 290, PHONE_W - 32, 40, "Continue button", fill=(0, 102, 180), outline=(0, 80, 140))
    d.text((px + 100, py + 302), "Continue", fill=(255, 255, 255), font=font(11, True))
    note(d, px + 16, py + 338, "Disabled until hold succeeds", ANNOT)

    px2 = 380
    phone_frame(d, px2, py, "Passenger Details — Proposed")
    box(d, px2 + 16, py + 50, PHONE_W - 32, 40, "Selected berth: B2 (Lower)", fill=(220, 255, 220), outline=GOOD)
    box(d, px2 + 16, py + 98, 120, 28, "Change seat link", fill=(255, 255, 255))
    note(d, px2 + 140, py + 102, "Tap → back to map", ANNOT)
    box(d, px2 + 16, py + 140, PHONE_W - 32, 120, "Passenger name fields", fill=(255, 255, 255))

    d.text((720, 100), "BEFORE: berth blank on this screen", fill=CHANGED, font=font(11))
    d.text((720, 130), "AFTER: same berth from hold_id", fill=GOOD, font=font(11))

    sy = 520
    d.text((24, sy), "STATES", fill=TEXT, font=font(12, True))
    box(d, 24, sy + 28, 360, 50, "Loading: Reserving berth…", fill=(240, 240, 255))
    box(d, 400, sy + 28, 360, 50, "Error: Berth just taken", fill=(255, 230, 230))
    box(d, 776, sy + 28, 400, 50, "Expired: Hold expired — reselect", fill=(255, 248, 220))
    save(img, "seat-map-berth-hold.png")


def wireframe_guest():
    img, d = new_canvas("Spec 4 — Guest Browse (No Login Modal on Type)")
    px, py = 24, 80
    phone_frame(d, px, py, "BEFORE — Part A")
    box(d, px + 16, py + 50, PHONE_W - 32, 36, "From: Del…", fill=(255, 255, 255))
    d.rounded_rectangle([px + 30, py + 100, px + PHONE_W - 30, py + 320], radius=8, fill=(80, 80, 80, 180), outline=CHANGED, width=2)
    d.text((px + 70, py + 180), "LOGIN MODAL", fill=(255, 255, 255), font=font(12, True))
    d.text((px + 50, py + 210), "(blocks form)", fill=(255, 200, 200), font=font(10))
    badge(d, px + 16, py + PHONE_H - 40, "BLOCKS SEARCH")

    ax = 380
    phone_frame(d, ax, py, "AFTER — Proposed Homepage")
    box(d, ax + 16, py + 44, PHONE_W - 32, 32, "From station autocomplete", fill=(255, 255, 255))
    note(d, ax + 16, py + 82, "Type → station list (no modal)", GOOD)
    box(d, ax + 16, py + 100, PHONE_W - 32, 32, "To station field", fill=(255, 255, 255))
    box(d, ax + 16, py + 140, PHONE_W - 32, 32, "Date picker", fill=(255, 255, 255))
    box(d, ax + 16, py + 180, PHONE_W - 32, 32, "Travel class dropdown", fill=(255, 255, 255))
    box(d, ax + 16, py + 220, PHONE_W - 32, 40, "Search button", fill=(0, 102, 180))
    d.text((ax + 110, py + 232), "Search", fill=(255, 255, 255), font=font(11))

    rx = 720
    phone_frame(d, rx, py, "Results — Guest")
    box(d, rx + 16, py + 44, PHONE_W - 32, 28, "Banner: Login to book — browse free", fill=(230, 245, 255), outline=GOOD)
    box(d, rx + 16, py + 80, PHONE_W - 32, 50, "Train list (read-only)", fill=(255, 255, 255))
    box(d, rx + 16, py + 140, PHONE_W - 32, 36, "Book button", fill=(0, 102, 180))
    note(d, rx + 16, py + 184, "Tap Book → LoginRequiredDialog", ANNOT)

    sy = 560
    box(d, 24, sy, 550, 45, "Loading: Searching trains…", fill=(240, 240, 240))
    box(d, 590, sy, 550, 45, "Error: Sign in to search (policy fallback only)", fill=(255, 230, 230))
    save(img, "guest-search-no-modal.png")


def wireframe_charts():
    img, d = new_canvas("Spec 5 — Reservation Charts Train Autocomplete")
    px, py = 24, 80
    phone_frame(d, px, py, "BEFORE — Part A")
    box(d, px + 16, py + 60, PHONE_W - 32, 40, "Train Name/Number", fill=(255, 255, 255))
    box(d, px + 16, py + 108, PHONE_W - 32, 50, '"0 results available"', fill=(255, 230, 230), outline=CHANGED)
    d.text((px + 20, py + 170), "User thinks field is broken", fill=CHANGED, font=font(9))

    ax = 380
    phone_frame(d, ax, py, "AFTER — Initial load")
    box(d, ax + 16, py + 60, PHONE_W - 32, 40, "Placeholder: Enter train no/name", fill=(255, 255, 255), outline=GOOD)
    d.text((ax + 20, py + 110), "(dropdown closed)", fill=MUTED, font=font(9))
    box(d, ax + 16, py + 130, PHONE_W - 32, 28, "Helper: Type 2+ characters", fill=(230, 245, 255))

    bx = 720
    phone_frame(d, bx, py, "AFTER — Typing")
    box(d, bx + 16, py + 60, PHONE_W - 32, 36, "12951 | Rajdhani", fill=(255, 255, 255))
    box(d, bx + 16, py + 102, PHONE_W - 32, 80, "Dropdown matches", fill=(240, 248, 255))
    note(d, bx + 16, py + 190, "Tap row → select train", ANNOT)

    sy = 480
    d.text((24, sy), "STATES", fill=TEXT, font=font(12, True))
    box(d, 24, sy + 28, 360, 48, "Loading: Searching…", fill=(240, 240, 255))
    box(d, 400, sy + 28, 360, 48, "Empty: No trains found — check number", fill=(255, 248, 220))
    box(d, 776, sy + 28, 400, 48, "Error: Autocomplete unavailable — enter number manually", fill=(255, 230, 230))
    save(img, "charts-train-autocomplete.png")


def wireframe_class():
    img, d = new_canvas("Spec 6 — Single Travel Class Selector")
    px, py = 24, 80
    phone_frame(d, px, py, "BEFORE — Part A")
    box(d, px + 16, py + 70, PHONE_W - 32, 36, "All Classes ▼", fill=(255, 255, 255))
    box(d, px + 16, py + 116, PHONE_W - 32, 36, "GENERAL ▼  (redundant)", fill=(255, 230, 230), outline=CHANGED)
    d.text((px + 20, py + 160), "Which to use? ", fill=CHANGED, font=font(10))
    badge(d, px + 16, py + 200, "CONFUSING")

    ax = 380
    phone_frame(d, ax, py, "AFTER — Proposed")
    d.text((ax + 16, py + 50), "Travel class", fill=LABEL, font=font(10, True))
    box(d, ax + 16, py + 68, PHONE_W - 32, 40, "All Classes ▼", fill=(220, 255, 230), outline=GOOD)
    d.text((ax + 20, py + 116), "Helper: Narrow results or see all", fill=MUTED, font=font(9))
    box(d, ax + 16, py + 140, PHONE_W - 32, 120, "Expanded options:\n1A, 2A, 3A, SL, GN", fill=(255, 255, 255))
    note(d, ax + 16, py + 270, "Tap option → single class param", ANNOT)
    box(d, ax + 16, py + 300, PHONE_W - 32, 40, "Search button", fill=(0, 102, 180))

    d.text((720, 100), "Removed: second GENERAL dropdown", fill=CHANGED, font=font(11))
    d.text((720, 130), "Added: helper + canonical labels", fill=GOOD, font=font(11))

    sy = 520
    box(d, 24, sy, 550, 50, "Default: All Classes — no empty state needed", fill=(245, 245, 245))
    box(d, 590, sy, 580, 50, "Error: Class unavailable for route — pick another", fill=(255, 230, 230))
    save(img, "travel-class-single-dropdown.png")


def main():
    wireframe_tatkal()
    wireframe_filters()
    wireframe_seat()
    wireframe_guest()
    wireframe_charts()
    wireframe_class()
    print("Done — 6 wireframes")


if __name__ == "__main__":
    main()
