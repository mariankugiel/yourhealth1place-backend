# -*- coding: utf-8 -*-
import re, io, os, json, unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import subprocess
import logging

import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageOps, ImageFilter

from app.core.config import settings
from app.core.aws_service import aws_service

logger = logging.getLogger(__name__)

# ---------- text helpers ----------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))

def norm(s: str) -> str:
    return strip_accents((s or "")).lower()

def is_meaningful_text(t: str) -> bool:
    return bool(t) and sum(ch.isalnum() for ch in t) >= 40

def cleanup_lines(text: str) -> List[str]:
    return [ln.replace("\u00a0", " ").strip() for ln in (text or "").splitlines() if ln.strip()]

def fix_mojibake(s: str) -> str:
    if not s: return s
    if "Ã" in s:
        try:
            t = s.encode("latin-1", "ignore").decode("utf-8", "ignore")
            if t: return t
        except Exception:
            pass
    return s

# ---------- OCR helpers ----------
def _pixmap_to_pil(pix: "fitz.Pixmap") -> Image.Image:
    try: data = pix.tobytes("png")
    except TypeError: data = pix.getPNGData()
    return Image.open(io.BytesIO(data))

def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    g = ImageOps.grayscale(img)
    g = g.filter(ImageFilter.MedianFilter(size=3))
    g = ImageOps.autocontrast(g)
    return g

def _ocr_image(img: Image.Image, ocr_langs: str, psm: int) -> str:
    return pytesseract.image_to_string(img, lang=ocr_langs, config=f"--oem 1 --psm {psm}")

def _ocr_page(doc, page_index: int, dpi: int, ocr_langs: str, psm: int) -> str:
    page = doc.load_page(page_index)
    mat = fitz.Matrix(dpi/72.0, dpi/72.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return _ocr_image(_preprocess_for_ocr(_pixmap_to_pil(pix)), ocr_langs, psm)

# ---------- PDF text extraction ----------
def extract_pages_text(pdf_data: bytes, ocr_langs: str, dpi: int, force_ocr: bool, allow_ocr: bool, psm: int) -> List[str]:
    pages_text: List[str] = []
    with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
        try: doc = fitz.open(stream=pdf_data, filetype="pdf")
        except Exception: doc = None
        for i, p in enumerate(pdf.pages):
            embedded = p.extract_text(x_tolerance=2, y_tolerance=2) or p.extract_text() or ""
            need_ocr = force_ocr or not is_meaningful_text(embedded)
            if not allow_ocr: need_ocr = False
            if need_ocr and doc is not None:
                try: pages_text.append(_ocr_page(doc, i, dpi, ocr_langs, psm) or ""); continue
                except Exception: pass
            pages_text.append(embedded or "")
    return pages_text

# ---------- patterns ----------
DATE_PATTERNS = [
    r"\b(?P<d>\d{2})[./-](?P<m>\d{2})[./-](?P<y>\d{2,4})\b",
    r"\b(?P<y2>\d{4})[./-](?P<m2>\d{2})[./-](?P<d2>\d{2})\b",
    r"\b(?P<d3>\d{1,2})\s+de\s+(?P<mo_pt>[A-Za-zçãéíóúâêôÇÃÉÍÓÚÂÊÔ]+)\s+de\s+(?P<y3>\d{4})\b",
    r"\b(?P<en_mo>January|February|March|April|May|June|July|August|September|October|November|December)\s+(?P<d4>\d{1,2}),\s+(?P<y4>\d{4})\b",
]
MONTHS_PT = {"janeiro":1,"fevereiro":2,"marco":3,"março":3,"abril":4,"maio":5,"junho":6,"julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
DATE_LABELS = [r"data\s+do\s+exame", r"data\s+exame", r"relat[óo]rio\s+data\s+exame", r"fecha\s+del?\s+examen", r"fecha\s+de\s+estudio",
               r"(?:exam|study)\s+date", r"date\s+of\s+exam", r"date\s+de\s+l'?examen", r"untersuchungsdatum", r"data\s+dell'?esame", r"onderzoeksdatum"]

# Exam type synonyms -> normalized label
ECG_PATTERNS = [r"\becg\b", r"\bekg\b", r"electrocardiogram[aao]?\b", r"electro[- ]?cardiogr"]
US_PATTERNS  = [r"\becografia\b", r"ultra(son|ss)on", r"\bultrasound\b", r"\bechografia\b", r"\bsonograf"]
XR_PATTERNS  = [r"\braio[-\s]?x\b", r"\brx\b", r"\bradiograf", r"\bx[-\s]?ray\b", r"\bradiol[óo]gic"]

INTERP_LABELS = [r"interpreta[cç][aá]o", r"interpretaci[óo]n", r"interpretation",
                 r"relat[óo]rio\s+de\s+exame|relatorio\s+de\s+exame|report\s+of\s+exam",
                 r"descri[cç][aã]o|description|findings|descrizione|beschreibung"]
CONCL_LABELS  = [r"conclus[aã]o(?:es)?", r"conclus[íi][oó]n(?:es)?", r"conclusion(?:s)?", r"impress[aã]o", r"\bimpression\b", r"diagn[óo]stico\s+final"]
CONCL_INLINE_KEYS = [r"conclus[aã]o", r"conclus[íi][oó]n", r"conclusion", r"impress[aã]o", r"impression", r"diagn[óo]stico\s+final"]
CONCL_HARD_STOPS = [
    r"^dr[.\s]", r"^dra[.\s]", r"especialista", r"assinatura|signature|carimbo|stamp",
    r"^hospital\b", r"\bunidade\b", r"\bendere[cç]o|\baddress\b", r"^ddn\b|data\s+de\s+nasc",
    r"\bmasculino\b|\bfeminino\b|\bmale\b|\bfemale\b", r"\banos?\b|\bage\b",
    r"\b\d{2}:\d{2}(:\d{2})?\b", r"\b\d{2}[-/]\d{2}[-/]\d{2,4}\b", r"\bprotocol|protocolo|ref\b",
    r"^freq\b|^fc\b|^hr\b|^pr\b|^qrsd?\b|^qt\b|^qtc\b|^--\s*eixo\s*--", r"\bderiv", r"\bveloc", r"\bmm/s\b|\bmm/mv\b|\bhz\b",
]

# ECG body (strict — only explicit mentions)
ECG_BODY_STRICT = [r"precord", r"deriva[cç][oõ]es", r"\bleads\b"]

# Doctor patterns
DOCTOR_NAME_RE = re.compile(
    r"\b(?:dr\.?\s*(?:\(\s*a\s*\))?\.?|dra\.?|doctor|doctora)\s*"
    r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\.'-]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\.'-]+)+)",
    re.IGNORECASE
)
DOCTOR_ID_STRONG_RE = re.compile(r"\b([A-Z]{1,3}\s?\d{4,7})\b")            # e.g., M30569, CRM 123456
DOCTOR_ID_WEAK_CTX_RE = re.compile(                                       # digits with context words
    r"(?:om|crm|gmc|big|rpps|ced(?:\.?|ula)|c[ée]dula|c\.?\s*prof\.?|ordem(?:\s+dos\s+m[ée]dicos)?|inscri[cç][aã]o|licen[cs]e|n[º°o]\.?)\s*[:\.#-]?\s*(\d{4,10})",
    re.IGNORECASE
)
DOCTOR_ID_PURE_NUM_TOKEN_RE = re.compile(r"\b(\d{4,6})\b")                 # plain 4–6 digits (e.g., 31184)

def _looks_like_datetime(s: str) -> bool:
    return bool(re.search(r"\b\d{2}:\d{2}(:\d{2})?\b", s) or re.search(r"\b\d{2}[-/]\d{2}[-/]\d{2,4}\b", s))

def _looks_like_postal(s: str) -> bool:
    return bool(re.search(r"\b\d{4}-\d{3}\b", s))

# ---------- dates ----------
def canonical_date(raw: str) -> Optional[str]:
    for pat in DATE_PATTERNS:
        m = re.search(pat, raw or "", flags=re.IGNORECASE)
        if not m: continue
        gd = m.groupdict()
        try:
            if gd.get("y2"): y, mo, d = int(gd["y2"]), int(gd["m2"]), int(gd["d2"])
            elif gd.get("en_mo"):
                months = {m:i+1 for i,m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"])}
                mo = months[gd["en_mo"]]; d = int(gd["d4"]); y = int(gd["y4"])
            elif gd.get("mo_pt"):
                mo = MONTHS_PT.get(norm(gd["mo_pt"]), 0); d = int(gd["d3"]); y = int(gd["y3"])
            else:
                d, mo, y = int(gd["d"]), int(gd["m"]), int(gd["y"])
                if y < 1900: y = y + (2000 if y < 100 else 0)
            return f"{d:02d}-{mo:02d}-{y:04d}"
        except Exception:
            continue
    return None

def find_first(lines: List[str], patterns: List[str]) -> Optional[Tuple[int, re.Match]]:
    for i, ln in enumerate(lines):
        for pat in patterns:
            m = re.search(pat, norm(ln), flags=re.IGNORECASE)
            if m: return i, m
    return None

# ---------- conclusions (page-aware) ----------
def _inline_after_label(original_line: str) -> str:
    n = norm(original_line)
    if any(re.search(p, n) for p in CONCL_INLINE_KEYS):
        m = re.search(r"[:\-]\s*(.+)$", original_line)
        if m: return m.group(1).strip()
    return ""

def _take_next_line_as_conclusion(lines: List[str], idx: int) -> str:
    if idx+1 < len(lines):
        nxt = lines[idx+1].strip()
        if any(re.search(p, norm(nxt)) for p in CONCL_HARD_STOPS): return ""
        return nxt
    return ""

def parse_conclusions_and_page(pages_text: List[str]) -> Tuple[str, int]:
    for pi, page_text in enumerate(pages_text):
        lines = cleanup_lines(page_text)
        fc = find_first(lines, CONCL_LABELS)
        if not fc: continue
        inline = _inline_after_label(lines[fc[0]])
        if inline: return inline.strip(), pi
        nxt = _take_next_line_as_conclusion(lines, fc[0])
        return nxt.strip(), pi
    return "", -1

def parse_interpretation(lines: List[str]) -> str:
    fp = find_first(lines, INTERP_LABELS)
    if not fp: return ""
    out = []
    for ln in lines[fp[0]+1:fp[0]+1+120]:
        if any(re.search(p, norm(ln)) for p in CONCL_LABELS + INTERP_LABELS + CONCL_HARD_STOPS): break
        out.append(ln)
    return "\n".join(out).strip()

# ---------- exam type / body ----------
def normalize_exam_type(lines: List[str]) -> str:
    head = "\n".join(lines[:60]); blob = "\n".join(lines)
    if any(re.search(p, norm(head)) or re.search(p, norm(blob)) for p in ECG_PATTERNS): return "ECG"
    if any(re.search(p, norm(head)) or re.search(p, norm(blob)) for p in US_PATTERNS):  return "Ultrasound"
    if any(re.search(p, norm(head)) or re.search(p, norm(blob)) for p in XR_PATTERNS):  return "X-Ray"
    return ""

def detect_body_area_for_ecg(lines: List[str]) -> str:
    window = "\n".join(lines[:120] + lines[-120:])
    if any(re.search(p, norm(window)) for p in ECG_BODY_STRICT): return "Precordial leads"
    return ""  # keep empty unless explicit mention

# ---------- doctor (focus on AFTER-the-name ID) ----------
def _find_id_in_text(text: str) -> str:
    # Prefer letter+digits
    sid = DOCTOR_ID_STRONG_RE.search(text)
    if sid:
        return sid.group(1).replace(" ", "").strip()
    # Then digits with context labels
    wid = DOCTOR_ID_WEAK_CTX_RE.search(text)
    if wid:
        return wid.group(1).strip()
    # Finally, plain 4–6 digits if the line looks like a signature line (not a date/time/postal)
    if not _looks_like_datetime(text) and not _looks_like_postal(text):
        m = DOCTOR_ID_PURE_NUM_TOKEN_RE.search(text)
        if m:
            return m.group(1).strip()
    return ""

def _doctor_from_lines_forward(lines: List[str]) -> Tuple[str, str]:
    """
    Scan in natural order so we can capture IDs that appear AFTER the doctor's name:
      - Same-line: take tail after the name and look for ID.
      - Next 1–3 lines: prefer short lines / lines with specialty words.
    """
    n = len(lines)
    for i in range(n):
        line = lines[i]
        nm = DOCTOR_NAME_RE.search(line)
        if not nm:
            continue
        name = nm.group(1).strip()

        # 1) Same line tail (AFTER the name)
        tail = line[nm.end():]
        doc_id = _find_id_in_text(tail)
        if doc_id:
            return name, doc_id

        # 2) Next 1–3 lines (look forward)
        for j in range(1, 4):
            if i + j >= n: break
            l2 = lines[i + j].strip()
            # Prefer typical signature lines: short, or contain specialty cue
            if len(l2) <= 60 or re.search(r"especialista|cardio|radiolog|ultra|imagem|imaging|ecografia|raio[-\s]?x|x[-\s]?ray", norm(l2)):
                doc_id = _find_id_in_text(l2)
                if doc_id:
                    return name, doc_id

        # 3) Previous 1–2 lines (sometimes ID is above)
        for j in range(1, 3):
            if i - j < 0: break
            l0 = lines[i - j].strip()
            if len(l0) <= 60 or re.search(r"especialista|cardio|radiolog|ultra|imagem|imaging|ecografia|raio[-\s]?x|x[-\s]?ray", norm(l0)):
                doc_id = _find_id_in_text(l0)
                if doc_id:
                    return name, doc_id

        # If we found the name but no ID nearby, keep the name and continue (maybe a later name has an ID)
        fallback_name = name

    # No pair found; try to return a lone name if present
    for line in reversed(lines):
        nm = DOCTOR_NAME_RE.search(line)
        if nm:
            return nm.group(1).strip(), ""
    return "", ""

def _page_bottom_lines(pdf_data: bytes, page_index: int, ocr_langs: str, dpi: int, psm: int, frac: float = 0.35) -> List[str]:
    """Bottom strip of a page (pdf text + OCR), cleaned to lines."""
    out = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            p = pdf.pages[page_index]
            H = p.height
            words = p.extract_words(use_text_flow=True, keep_blank_chars=False) or []
            words = [w for w in words if w.get("top", 9e9) >= H*(1-frac)]
            # group by row
            rows = {}
            for w in words:
                y = int(w.get("top", 0)//8)
                rows.setdefault(y, []).append((w.get("x0", 0), w.get("text", "")))
            for _, items in sorted(rows.items()):
                out.append(" ".join(t for _, t in sorted(items)))
    except Exception:
        pass
    # OCR bottom crop
    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        page = doc.load_page(page_index)
        mat = fitz.Matrix(dpi/72.0, dpi/72.0)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = _pixmap_to_pil(pix)
        h, w = img.size[1], img.size[0]
        crop = img.crop((0, int(h*(1-frac)), w, h))
        txt = _ocr_image(_preprocess_for_ocr(crop), ocr_langs, psm)
        out += cleanup_lines(txt)
    except Exception:
        pass
    return cleanup_lines("\n".join(out))

def detect_doctor_from_pages(pdf_data: bytes, pages_text: List[str], preferred_idx: int, ocr_langs: str, dpi: int, psm: int) -> Tuple[str, str]:
    # Search conclusions page first, then last, then others
    order = []
    if preferred_idx >= 0: order.append(preferred_idx)
    if (len(pages_text)-1) not in order: order.append(len(pages_text)-1)
    order += [i for i in range(len(pages_text)) if i not in order]
    for idx in order:
        lines = _page_bottom_lines(pdf_data, idx, ocr_langs, dpi, psm)
        name, num = _doctor_from_lines_forward(lines)
        if name or num:
            # Prefer letter+digits formats if both encountered
            if num and re.match(r"^[A-Z]{1,3}\d{4,7}$", num, flags=re.IGNORECASE):
                return name, num
            return name, num
    return "", ""

class MedicalImageAnalysisService:
    def __init__(self):
        self.aws_service = aws_service
        
    def extract_exam_info(self, pdf_data: bytes,
                          ocr_langs: str = "eng+por+spa+deu+ita+fra+ell+pol+rus+nld",
                          dpi: int = 300, force_ocr: bool = False, allow_ocr: bool = True, psm: int = 6,
                          tesseract_cmd: str = "", tessdata_dir: str = "") -> Dict:
        """Extract structured information from medical exam PDFs"""
        try:
            # Configure Tesseract
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            else:
                for p in [r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]:
                    if Path(p).is_file(): 
                        pytesseract.pytesseract.tesseract_cmd = p
                        break
            if tessdata_dir: 
                os.environ["TESSDATA_PREFIX"] = str(Path(tessdata_dir).resolve())

            pages_text = extract_pages_text(pdf_data, ocr_langs, dpi, force_ocr, allow_ocr, psm)
            full_text = "\n".join(pages_text)
            lines = cleanup_lines(full_text)

            # Date
            lf = find_first(lines, DATE_LABELS)
            date = canonical_date(" ".join(lines[lf[0]:lf[0]+2])) if lf else canonical_date(full_text) or ""

            # Exam type & body rules
            head = "\n".join(lines[:60])
            blob = "\n".join(lines)
            if any(re.search(p, norm(head)) or re.search(p, norm(blob)) for p in ECG_PATTERNS):
                exam_type = "ECG"
                body = ""
                # allow only explicit precordial/leads
                window = "\n".join(lines[:120] + lines[-120:])
                if any(re.search(p, norm(window)) for p in ECG_BODY_STRICT): 
                    body = "Precordial leads"
            elif any(re.search(p, norm(head)) or re.search(p, norm(blob)) for p in US_PATTERNS):
                exam_type = "Ultrasound"
                body = "Upper abdomen"
            elif any(re.search(p, norm(head)) or re.search(p, norm(blob)) for p in XR_PATTERNS):
                exam_type = "X-Ray"
                body = "Chest"
            else:
                exam_type = ""
                body = ""

            # Sections (page-aware conclusions)
            conclusions_raw, concl_page = parse_conclusions_and_page(pages_text)
            conclusions = fix_mojibake(conclusions_raw)
            interpretation = fix_mojibake(parse_interpretation(lines))

            # Doctor (prefer conclusions page; capture IDs AFTER the name)
            doctor_name, doctor_number = detect_doctor_from_pages(pdf_data, pages_text, concl_page, ocr_langs, dpi, psm)

            return {
                "file": "uploaded_pdf",
                "date_of_exam": date,
                "exam_type": exam_type,
                "body_area": body,
                "interpretation": interpretation,
                "conclusions": conclusions,
                "doctor_name": (doctor_name or "").strip(),
                "doctor_number": (doctor_number or "").strip()
            }
        except Exception as e:
            logger.error(f"Error extracting exam info from uploaded PDF: {e}")
            return {
                "file": "uploaded_pdf",
                "date_of_exam": "",
                "exam_type": "",
                "body_area": "",
                "interpretation": "",
                "conclusions": "",
                "doctor_name": "",
                "doctor_number": ""
            }

    def categorize_findings(self, body_part: str, interpretation: str, conclusion: str) -> str:
        """Categorize findings using AI based on interpretation and conclusion"""
        try:
            from app.core.config import settings
            import openai
            
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API key not configured, using default categorization")
                return "No Findings"
            
            prompt = f"""Categorize an exam for {body_part} with the following instructions ({interpretation}) and conclusion ({conclusion}) in one of the following categories using the instruction and conclusions that are on the report:
- No Findings: the exam was considered as normal or it mentions that it has no findings or changes
- Low Risk Findings: the exam has detected something that can pose a risk in the future, but at the moment it poses no serious risk for the patient.
- Relevant Findings: the exam has detected something that can pose a risk in the near future and has the potential to pose a serious risk for the patient in the next 12/48 months.

Respond with only one of these exact categories: "No Findings", "Low Risk Findings", or "Relevant Findings"."""

            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Latest cost-effective model with better performance
                messages=[
                    {"role": "system", "content": "You are a medical AI assistant that categorizes medical exam findings."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            # Validate the response
            valid_categories = ["No Findings", "Low Risk Findings", "Relevant Findings"]
            if result in valid_categories:
                return result
            else:
                logger.warning(f"AI returned invalid category: {result}, defaulting to 'No Findings'")
                return "No Findings"
                
        except Exception as e:
            logger.error(f"Error categorizing findings: {e}")
            return "No Findings"

    async def process_medical_image(self, file_content: bytes, filename: str, user_id: int) -> Dict:
        """Process uploaded medical image document and extract information"""
        try:
            # Extract information using the analysis script (now works with bytes directly)
            extracted_info = self.extract_exam_info(file_content)
            
            # Categorize findings using AI
            findings = self.categorize_findings(
                body_part=extracted_info.get('body_area', ''),
                interpretation=extracted_info.get('interpretation', ''),
                conclusion=extracted_info.get('conclusions', '')
            )
            
            # Add findings to extracted info
            extracted_info['findings'] = findings
            
            # Upload to S3 using the existing AWS service
            file_id = await self.aws_service.store_document(str(user_id), file_content, filename, "application/pdf")
            s3_key = f"documents/{user_id}/{file_id}/{filename}"
            
            return {
                "success": True,
                "extracted_info": extracted_info,
                "s3_key": s3_key,
                "filename": filename
            }
                    
        except Exception as e:
            logger.error(f"Error processing medical image {filename}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
