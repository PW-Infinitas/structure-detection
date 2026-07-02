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
        "header_title": "หนังสือรับรองเรื่องการหักเงินเดือน",
        "agency": [
            "กองพันทหารราบที่ 1 กรมทหารราบที่ 3",
            "ค่ายมหาจักรีสิรินธร ตำบลท่าเหนือ",
            "อำเภอเมือง จังหวัดสตูล",
        ],
        "date": "พฤษภาคม 2569",
        "subject": "ขอส่งรายชื่อผู้ขอกู้เงินโครงการสินเชื่อสวัสดิการเพื่อข้าราชการ กองทัพบก",
        "recipient": "ผู้จัดการ บมจ.ธนาคารกรุงไทย สาขานาทวี",
        "reference": None,
        "body_blocks": [
            {
                "type": "paragraph",
                "text": "กองพันทหารราบที่ 1 กรมทหารราบที่ 3 ได้พิจารณาแล้วเห็นว่า ผู้มีรายชื่อดังต่อไปนี้ "
                "มีคุณสมบัติเหมาะสมที่จะเป็นผู้กู้โครงการสินเชื่อสวัสดิการเพื่อข้าราชการในสังกัดสำนักงานเลขานุการรัฐมนตรี "
                "กระทรวงกลาโหม ตามหลักเกณฑ์ที่ธนาคารกำหนด และมีเงินเดือนเหลือเพียงพอที่จะชำระหนี้",
            },
            {
                "type": "table",
                "columns": ["ชื่อ - นามสกุล", "จำนวนเงินที่ขอกู้(บาท)"],
                "rows": [["สิบโท พงศกร โยธินภัทรอนุธนารักษ์", "1,250,000.- บาท"]],
            },
            {
                "type": "paragraph",
                "text": "จึงเรียนมาเพื่อโปรดพิจารณาดำเนินการทั้งนี้ กองพันทหารราบที่ 1 กรมทหารราบที่ 3 "
                "ยินดีให้ความร่วมมือหักเงินเดือน และ/หรือค่าจ้างหรือเงินได้อื่นๆ ของผู้กู้ส่งชำระหนี้ให้ธนาคารทุกเดือน "
                "จนกว่าจะชำระหนี้เสร็จสิ้น",
            },
        ],
        "signer_rank": "พันเอก",
        "signature_name": "วิเศษ เทพยักษ์คำราม",
        "printed_name": "วิเศษ เทพยักษ์คำราม",
        "title": "ผู้บังคับกองพันทหารราบที่ 1 กรมทหารราบที่ 3",
        "responsible_dept": None,
        "phone": None,
        "fax": None,
        "email": None,
    }

    render_letter(sample, OUTPUT_DIR / "letter_001.png")
