"""Renders a single Thai government letter to a high-res PNG using Playwright."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

GENERATOR_DIR = Path(__file__).parent
PROJECT_DIR = GENERATOR_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "mock_data" / "positive"

# A4 at 96 dpi = 794 × 1123 px. Scale factor 2 → ~150 dpi equivalent.
_A4_WIDTH_PX = 794
_A4_HEIGHT_PX = 1123
_DEVICE_SCALE = 2


def render_letter(data: dict, output_path: Path) -> None:
    """Render one letter data dict to a PNG at output_path."""
    env = Environment(loader=FileSystemLoader(str(GENERATOR_DIR)))
    template = env.get_template("template.html")

    data.setdefault("garuda_path", "../assets/images/garuda_emblem.png")
    html = template.render(**data)

    # Write inside generator/ so relative CSS and font paths in styles.css resolve correctly.
    temp_html = GENERATOR_DIR / "_render_temp.html"
    temp_html.write_text(html, encoding="utf-8")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": _A4_WIDTH_PX, "height": _A4_HEIGHT_PX},
                device_scale_factor=_DEVICE_SCALE,
            )
            page.goto(temp_html.as_uri(), wait_until="networkidle")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output_path), full_page=True)
            browser.close()
    finally:
        temp_html.unlink(missing_ok=True)

    print(f"Rendered → {output_path}")


if __name__ == "__main__":
    sample: dict = {
        "ref_id": "กห 1467.1.1.2/300",
        "agency": "กรมพัฒนาฝีมือแรงงาน กระทรวงแรงงาน",
        "date": "1 กรกฎาคม 2569",
        "subject": "ขอรับรองรายได้ของพนักงานเพื่อประกอบการพิจารณาสินเชื่อ",
        "recipient": "ผู้จัดการธนาคารกรุงไทย จำกัด (มหาชน) สาขาสีลม",
        "attachments": None,
        "body_paragraphs": [
            "ด้วย นายสมชาย ใจดี ตำแหน่ง เจ้าหน้าที่บริหารงานทั่วไป ระดับ 4 สังกัดกองพัฒนาทักษะฝีมือ "
            "กรมพัฒนาฝีมือแรงงาน ได้ยื่นความประสงค์ขอกู้เงินจากสถาบันการเงินของท่าน "
            "กรมฯ จึงขอรับรองว่าบุคคลดังกล่าวเป็นข้าราชการพลเรือนสามัญสังกัดหน่วยงานนี้จริง",
            "ปัจจุบัน นายสมชาย ใจดี ได้รับเงินเดือนในอัตรา 28,500 บาทต่อเดือน "
            "และมีสถานะการปฏิบัติราชการปกติ ไม่อยู่ระหว่างถูกสอบสวนทางวินัยหรือถูกพักราชการแต่อย่างใด",
            "จึงเรียนมาเพื่อโปรดทราบและใช้ประกอบการพิจารณาตามที่เห็นสมควร",
        ],
        "signature_name": "สมศักดิ์ วีระพงษ์",
        "printed_name": "สมศักดิ์ วีระพงษ์",
        "title": "อธิบดีกรมพัฒนาฝีมือแรงงาน",
        "responsible_dept": "กองพัฒนาทักษะฝีมือ",
        "phone": "0 2245 1707",
        "fax": "0 2245 6956",
        "email": "dsd@dsd.go.th",
    }

    render_letter(sample, OUTPUT_DIR / "letter_001.png")
