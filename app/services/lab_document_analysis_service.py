import re
import json
import logging
import unicodedata
from typing import List, Dict, Optional, Any, Tuple, Iterable
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from app.crud.health_record import health_record_crud, health_record_doc_lab_crud, health_record_section_template_crud, health_record_metric_template_crud, health_record_section_crud, health_record_metric_crud
from app.models.health_record import (
    HealthRecord, HealthRecordDocLab, HealthRecordSection, 
    HealthRecordMetric, GeneralDocumentType, LabDocumentType
)
from app.schemas.health_record import HealthRecordCreate, HealthRecordDocLabCreate, HealthRecordSectionCreate, HealthRecordMetricCreate
from app.services.language_detection_service import detect_document_language

logger = logging.getLogger(__name__)

class LabDocumentAnalysisService:
    """Advanced service for analyzing lab report documents with multilingual support"""
    
    def __init__(self):
        self._init_patterns()
        self._detected_language: Optional[str] = None  # Store detected language for document
    
    def _init_patterns(self):
        """Initialize comprehensive regex patterns for lab report extraction"""
        
        # Superscript characters for unit normalization
        self.SUPERS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
        
        # Comprehensive unit patterns
        self.UNIT_ABS = (
            r"(?:"
            r"x\s*10(?:\^?\s*\d+|[" + self.SUPERS + r"]+)(?:/L)?|"
            r"g/dL|mg/dL|mmol/L|µmol/L|μmol/L|nmol/L|pmol/L|ng/mL|pg/mL|mIU/L|mUI/L|UI/L|U/L|/µL|/uL|/L|fL|pg|mEq/L|seg\."
            r")"
        )
        self.UNIT_ANY = rf"(?:{self.UNIT_ABS}|%)"
        
        # Date patterns
        self.MULTI_DATE_RE = re.compile(
            r"\b(?:(?P<d1>\d{2})[./-](?P<m1>\d{2})[./-](?P<y1>\d{2,4})|(?P<y2>\d{4})[./-](?P<m2>\d{2})[./-](?P<d2>\d{2}))\b"
        )
        
        # Comprehensive text value patterns for urine analysis (multilingual)
        self.TEXT_VALUE_PATTERNS = [
            # PT/ES/IT/RO
            r"Não\s+revelou(?:\s*\([^)]+\))?", r"Nao\s+revelou(?:\s*\([^)]+\))?",
            r"No\s+revel[oó]", r"No\s+detectado", r"No\s+se\s+detect[oó]", r"Ausente",
            r"Presente", r"Presencia", r"Presenza", r"Prezent",
            r"Raros(?:\s*\([^)]+\))?", r"Escasos", r"Pocos", r"Occasionali?",
            r"Vest[ií]gios", r"Vestigios", r"Tracce", r"Urme",
            r"Límpid[ao]", r"Limpid[eo]", r"Claro", r"Clara", r"Chiaro",
            r"Amarela(?:\s+clara)?", r"Amarill[oa]", r"Giallo", r"Galben[ăa]?",
            r"Negativo", r"Positivo",
            # EN/FR/DE/NL/DK/SE/NO/PL
            r"Not\s+detected", r"None\s+detected", r"Absent", r"Present",
            r"Rare", r"Few", r"Occasional",
            r"Trace(?:s)?", r"Traces?", r"Spur(?:e|en)?", r"Spor", r"Spår", r"Ślad(?:y)?",
            r"Clear", r"Limpid", r"Clair", r"Klar", r"Helder", r"Bistr[ăa]?",
            r"Yellow", r"Jaune", r"Gelb", r"Geel", r"Gul", r"Żółty",
            r"Negativ(?:e|o|t)?", r"Positiv(?:e|o|t)?",
            # EL / HR / SR / BG / TR
            r"Αρνητικ[όή]", r"Θετικ[όή]", r"Ίχνη", r"Διαυγές", r"Κίτρινο",
            r"Negativno", r"Pozitivno", r"Tragovi", r"Bistro", r"Žuto",
            r"Негативно", r"Позитивно", r"Трагови", r"Бистро", r"Жълт[о]?",
            r"Negatif", r"Pozitif", r"İz", r"Berrak", r"Sarı",
            # with /campo / field / HPF
            r"(?:Raros|Rare|Few|Occasional).*?\(\s*<?\s*\d+\s*/\s*(?:campo|field|HPF)\s*\)",
        ]
        self.TEXT_VALUE_RE = re.compile("|".join(self.TEXT_VALUE_PATTERNS), re.IGNORECASE)
        
        # Historical value pattern (numeric OR qualitative text)
        self.HIST_VALUE_RE = re.compile(
            r"(?:"
            + self.TEXT_VALUE_RE.pattern +
            r"|(?:[<>]=?\s*)?[\d.,]+(?:\s*/\s*(?:campo|field|HPF))?"
            r")",
            re.IGNORECASE
        )
        
        # Comprehensive meta/header patterns (multilingual)
        self.META_NAME_RE = re.compile(
            r"^(?:"
            # Hospital / Clinic / Lab
            r"hospital|clin(?:ic|iqu)e|cl[ií]nica|krankenhaus|klin(?:ik|ika)|"
            r"lab(?:or(?:atorio|atoire|oratorium)|or)|laborat[óo]rio|laboratuvar|"
            # Phone / Web
            r"tel(?:ephone|efo[oó]n|[eé]fono|efon|efonnummer)?|tlf\.?|telefon|téléphone|"
            r"www\.|http|https|e-?mail|correo|mail|email|"
            # Page
            r"p[áa]g\.?|page\b|seite|pagina|pagin[ăa]?|strona|stranica|sida|side|σελίδα|страница|sayfa|"
            r"pag\.|p[oó]lg\.?"
            r"|"
            # Date words
            r"data\b|fecha\b|date\b|datum\b|dato\b|ημερομηνία|дата|tarih\b"
            r"|"
            # Method / Methodology
            r"m[ée]t(?:odo|\.?)|met(?:hod|hode|odo|ode)?\b|méthode|methode|metode|"
            # Admin / identity
            r"impress|imprimi|druk|drucken|drukker|drukă|drukăre|drukati|print|"
            r"epis[óo]dio|episode|episod|akten|dossier|processo|proc[eé]s|"
            r"utente|pacient|patient|paciente|paziente|"
            r"n[º°#]\b|num(?:ero)?\b|refer[ée]ncia|ref\.:?|adres[se]?|end[eé]re[cç]o|morada|adresse|indirizzo|adres|adresa|adrese|adresi|adresă|адрес|"
            r"nif|nie|cif|dni|pesel|oib|egn|tc\s*kimlik|kimlik|"
            # Section/title-like
            r"ionogram(?:me|a|m)?|ionograma|hemograma|hemogramme|hemogramma|"
            r"urina\s*ii.*exame\s+sum[áa]rio"
            r"|"
            # Explicit prefixes to drop
            r"exma|exmo|hfe|phu\b"
            r")",
            re.IGNORECASE
        )
        
        # Additional patterns from the new version
        self.VALUE_WITH_UNIT_RE = re.compile(
            rf"(?:^|\s)(?P<val>[<>]=?\s*\d[\d.,]*)\s*(?P<u>{self.UNIT_ANY})\b"
        )
        self.RANGE_OR_CMP_RE = re.compile(r"(?:[\d.,]+\s*-\s*[\d.,]+|[<>]=?\s*[\d.,]+)")
        
        # Blocklist patterns for lines to skip
        self.START_BLOCKLIST = tuple(
            self._norm(s) for s in [
                "Referência", "Referência normal", "ReferÃªncia", "ReferÃªncia normal",
                "Insuficiência:", "InsuficiÃªncia:",
                "Recomendações", "Recomendações:", "RecomendaÃ§Ãµes", "RecomendaÃ§Ãµes:",
                "PHEV",
                "Deficiência", "Deficiência:", "DeficiÃªncia", "DeficiÃªncia:"  # block entire lines with this header
            ]
        )
        
        # Date labels (multilingual)
        self.DATE_LABELS = [
            # Portuguese
            r"data\s+colheita", r"data\s+da\s+colheita", r"data\s+do\s+relat[oó]rio", r"data\s+do\s+resultado",
            # Spanish
            r"fecha\s+de\s+extracci[oó]n", r"fecha\s+de\s+toma\s+de\s+muestra", r"fecha\s+del?\s+informe", r"fecha\s+del?\s+resultado",
            # English
            r"(collection|sample\s+collection|specimen\s+collection)\s+date", r"report\s+date", r"result\s+date",
            # French
            r"date\s+de\s+pr[ée]l[èe]vement", r"date\s+du\s+rapport", r"date\s+du\s+r[ée]sultat",
            # German
            r"entnahme(?:-|\s*)datum", r"berichtsdatum", r"ergebnisdatum",
            # Italian
            r"data\s+prelievo", r"data\s+del\s+referto", r"data\s+referto", r"data\s+del\s+rapporto", r"data\s+del\s+risultato",
            # Polish
            r"data\s+pobrania", r"data\s+raportu", r"data\s+wyniku",
            # Dutch
            r"afnamedatum", r"rapportdatum", r"resultaatdatum",
            # Danish / Swedish / Norwegian
            r"pr[øo]vetagningsdato|pr[øo]vetakingsdato", r"rapportdato", r"resultatdato", r"provtagningsdatum",
            # Greek
            r"ημερομηνία\s+λήψης", r"ημερομηνία\s+αναφοράς", r"ημερομηνία\s+αποτελέσματος",
            # Croatian / Serbian (Latin + Cyrillic)
            r"datum\s+uzorkovanj[ae]", r"datum\s+izv[je]s?ta[ja]", r"datum\s+rezultata",
            r"датум\s+узорковања", r"датум\s+извештаја", r"датум\s+резултата",
            # Romanian
            r"data\s+recolt[ăa]rii", r"data\s+raportului", r"data\s+rezultatului",
            # Bulgarian
            r"дата\s+на\s+вземане\s+на\s+пробата", r"дата\s+на\s+отчета", r"дата\s+на\s+резултата",
            # Turkish
            r"(?:[öo]rnek|numune)\s+al[ıi]m\s+tarihi", r"rapor\s+tarihi", r"sonu[cç]\s+tarihi",
        ]
    
    # Utility functions
    def _strip_accents(self, s: str) -> str:
        if not s:
            return s
        return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

    def _norm(self, s: str) -> str:
        return self._strip_accents(s or "").lower()

    def _normalize_units(self, s: str) -> str:
        """Coalesce spaces, fix common x10 variants, and normalize spacing."""
        if not s:
            return s
        s = s.replace("\u00a0", " ")
        for bad, good in [
            ("x109 / L", "x10^9/L"), ("x10 9 / L", "x10^9/L"), ("x109/ L", "x10^9/L"),
            ("x109 /L", "x10^9/L"), ("x 109 / L", "x10^9/L"), (" / ", "/"),
        ]:
            s = s.replace(bad, good)
        # Normalize common caret-less/spacey power-of-ten variants
        s = re.sub(r"x\s*10\s*\^?\s*9(?:\s*/\s*L)?", "x10^9/L", s, flags=re.IGNORECASE)
        s = re.sub(r"x\s*109(?:\s*/\s*L)?", "x10^9/L", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def _protect_x10_units(self, s: str) -> str:
        # prevent the "10" in x10^… units from being treated as historical tokens
        return re.sub(r"x\s*10[\^¹²³]?\s*\d*\s*/?\s*[A-Za-zµ/]+", "xTEN", s)
    
    def _is_blocklisted_line(self, raw: str) -> bool:
        """Check if a line should be blocked based on start patterns"""
        if not raw:
            return False
        r = self._norm(raw).strip()
        for prefix in self.START_BLOCKLIST:
            if r.startswith(prefix):
                return True
        return False
    
    def _is_blocklisted_metric_name(self, name: str) -> bool:
        """Check if a metric name should be blocked (handles exact 'Deficiência' as a name)"""
        # Normalize: remove accents and trailing punctuation like ":".
        n = self._norm(name)
        n = re.sub(r"[:\s]+$", "", n)
        # Accept both proper encoding and mojibake variants by normalization.
        # Only block if it's exactly the bare label "deficiencia"
        return n == "deficiencia"

    def _canonicalize_date(self, ds: Any) -> str:
        """Return dd-mm-yyyy if possible; accept either a string or a tuple from regex .findall()."""
        if isinstance(ds, tuple):
            s = next((x for x in ds if x), "")
        else:
            s = str(ds or "")
        if not s:
            return ""
        m = self.MULTI_DATE_RE.search(s)
        if not m:
            return s
        if m.group("y2"):  # yyyy-mm-dd
            y = int(m.group("y2"))
            mo = int(m.group("m2"))
            d = int(m.group("d2"))
        else:             # dd-mm-yyyy or dd-mm-yy
            d = int(m.group("d1"))
            mo = int(m.group("m1"))
            y = int(m.group("y1"))
            if y < 100:
                y += 2000 if y < 50 else 1900
        try:
            return f"{d:02d}-{mo:02d}-{y:04d}"
        except Exception:
            return s

    def _detect_section_type(self, line: str, current_type: str) -> str:
        """Detect section type with multilingual support"""
        t = self._norm(line)
        # Hematology keywords
        if any(k in t for k in [
            "hematolog", "hemograma", "hematologe", "hématolog", "hämatolog", "ematolog", "αιματολογ", "хематолог", "hematoloji"
        ]):
            return "HEMATOLOGIA"
        # Biochemistry keywords
        if any(k in t for k in [
            "bioquim", "biochim", "biochem", "biokem", "biokjem", "biochemie", "βιοχημ", "биохим", "biyokim"
        ]):
            return "BIOQUIMICA"
        # Urine / urinalysis keywords
        if any(k in t for k in [
            "urina", "urine", "urin ", "urin-", "urinalys", "urinaliz", "ουρ", "урин", "idrar", "mocz", "moczu"
        ]):
            return "URINA E DOSEAMENTOS URINÁRIOS"
        return current_type

    def _extract_report_date(self, first_page_text: str, full_text: str) -> str:
        """Extract report date with multilingual support"""
        # Look for labeled date on first page
        t = self._norm(first_page_text)
        for lbl in self.DATE_LABELS:
            for m in re.finditer(lbl, t, flags=re.IGNORECASE):
                start = max(0, m.end())
                window = first_page_text[start:start+160]
                md = self.MULTI_DATE_RE.search(window)
                if md:
                    return self._canonicalize_date(md.group(0))
        # fallback: any date on first page
        md = self.MULTI_DATE_RE.search(first_page_text)
        if md:
            return self._canonicalize_date(md.group(0))
        # last resort: any date anywhere
        md = self.MULTI_DATE_RE.search(full_text)
        return self._canonicalize_date(md.group(0)) if md else ""

    def _extract_lab_name(self, full_text: str, override: str = "") -> str:
        """Extract lab name with multilingual support"""
        if override:
            return override
        # High-priority specific name first (avoid "Certificado" footers)
        for line in (full_text.splitlines() if full_text else []):
            l = line.strip()
            ln = self._norm(l)
            if ("laboratorio de analises clinicas" in ln or "laboratório de análises clínicas" in ln) and "certific" not in ln:
                return l
        # Generic multilingual lab/clinic/hospital lines (avoid certificate lines)
        for line in (full_text.splitlines() if full_text else []):
            l = line.strip()
            ln = self._norm(l)
            if "certific" in ln:
                continue
            if re.search(r"\b(hospital|clin|clinic|clínic|klin|krankenhaus|ospedale|szpital|ziekenhuis|hospitalet|sjukhus|sykehus|spital|болниц|hastane)\b", ln):
                return l
            if re.search(r"\b(lab|laborat|laboratuv|laborator|laboratoire|laboratorium)\b", ln):
                return l
        return ""

    def _split_name_and_tail_safe(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Safe splitter:
        1) If we see a value+unit, split there.
        2) Else if we see a textual value, split there.
        3) Else try a last-resort numeric split ONLY if the remainder clearly contains a unit or a range/comparator.
           This prevents cutting names like 'CA 19-9', 'IGF-1', 'T4 Livre (FT4)', etc.
        """
        m_val = self.VALUE_WITH_UNIT_RE.search(line)
        if m_val:
            idx = m_val.start()
            return line[:idx].strip().lstrip("-:•·").strip(), line[idx:].strip()

        m_text = self.TEXT_VALUE_RE.search(line)
        if m_text:
            idx = m_text.start()
            return line[:idx].strip().lstrip("-:•·").strip(), line[idx:].strip()

        # Last resort: split at the first number ONLY if unit or range/comparator follows somewhere
        m_num = re.search(r"[<>]?\s*\d", line)
        if m_num:
            tail = line[m_num.start():]
            if self.VALUE_WITH_UNIT_RE.search(tail) or self.RANGE_OR_CMP_RE.search(tail):
                return line[:m_num.start()].strip().lstrip("-:•·").strip(), line[m_num.start():].strip()

        return None, None

    def _pick_central_from_left(self, left: str):
        """Prefer absolute units over % on the same line."""
        cand_re = re.compile(rf"(?P<val>[<>]?\s*[\d.,]+)\s*(?P<unit>{self.UNIT_ANY})?")
        cands = list(cand_re.finditer(left))
        if not cands:
            return None, None
        # Prefer absolute unit
        for m in cands:
            u = (m.group('unit') or "").strip()
            if u and re.fullmatch(self.UNIT_ABS, u):
                val = m.group('val').replace(" ", "").replace(",", ".")
                return val, self._normalize_units(u)
        # Fallback: first candidate
        m = cands[0]
        val = m.group('val').replace(" ", "").replace(",", ".")
        return val, self._normalize_units((m.group('unit') or "").strip())

    def _parse_numeric_metric_line(self, line: str, page_hist_dates: List[str], report_date: str):
        """Parse numeric metric line with historical data support"""
        line = self._normalize_units(line)
        if self._is_blocklisted_line(line):
            return None
        
        name, tail = self._split_name_and_tail_safe(line)
        if not name:
            return None
        
        if self._is_blocklisted_metric_name(name):
            return None
        
        nl = self._norm(name)
        # Drop meta names + explicit prefixes
        if self.META_NAME_RE.search(name) or nl.startswith("exmo") or nl.startswith("hfe"):
            return None

        tail_clean = self._protect_x10_units(tail)

        # Identify reference part (range or comparator) to the rightmost occurrence
        mref = None
        last_range = None
        for m in re.finditer(r"[\d.,]+\s*-\s*[\d.,]+", tail_clean):
            last_range = m
        if last_range:
            mref = last_range
        else:
            last_cmp = None
            for m in re.finditer(r"[<>]=?\s*[\d.,]+", tail_clean):
                last_cmp = m
            if last_cmp:
                mref = last_cmp

        if mref:
            left = tail_clean[:mref.start()].strip()
            reference = (mref.group(0) or "").strip()
            right = tail_clean[mref.end():].strip()
            left_original = (tail or "")[:mref.start()].strip()
        else:
            left = tail_clean
            right = ""
            reference = ""
            left_original = (tail or "")
        central_val, central_unit = self._pick_central_from_left(left_original)
        if not central_val:
            return None

        # historical values (numeric OR qualitative text)
        right_vals = [h.strip() for h in self.HIST_VALUE_RE.findall(right)]
        left_vals = []
        for m in self.HIST_VALUE_RE.finditer(left):
            tok = m.group(0).strip()
            # avoid echoing the central numeric token if same
            if tok.replace(" ", "").replace(",", ".") == central_val:
                continue
            # don't pick the reference range
            if reference and tok in reference:
                continue
            left_vals.append(tok)
        hist_vals = right_vals if right_vals else left_vals

        rows = []
        rows.append({
            "metric_name": name,
            "date_of_value": report_date,
            "value": central_val,
            "unit": central_unit or "",
            "reference": reference,
        })
        if hist_vals and page_hist_dates:
            for i, hv in enumerate(hist_vals[:2]):
                if i < len(page_hist_dates):
                    rows.append({
                        "metric_name": name,
                        "date_of_value": page_hist_dates[i],
                        "value": hv,
                        "unit": central_unit or "",
                        "reference": reference,
                    })
        return rows

    def _parse_urine_metric_line(self, line: str, report_date: str, page_hist_dates: List[str]):
        """Parse qualitative urine metrics with historical data support"""
        if self._is_blocklisted_line(line):
            return None
        
        name, tail = self._split_name_and_tail_safe(line)
        if not name or not tail:
            return None
        
        if self._is_blocklisted_metric_name(name):
            return None
        
        nl = self._norm(name)
        if self.META_NAME_RE.search(name) or nl.startswith("exmo") or nl.startswith("hfe"):
            return None

        # Find ALL qualitative tokens across the tail, in order
        all_texts = [m.group(0).strip() for m in self.TEXT_VALUE_RE.finditer(tail)]
        if not all_texts:
            return None

        central_val = all_texts[0]
        hist_vals = all_texts[1:]  # any further tokens are historical columns (left-to-right)

        rows = [{
            "metric_name": name,
            "date_of_value": report_date,
            "value": central_val,
            "unit": "",
            "reference": "",
        }]

        if hist_vals and page_hist_dates:
            for i, hv in enumerate(hist_vals[:2]):
                if i < len(page_hist_dates):
                    rows.append({
                        "metric_name": name,
                        "date_of_value": page_hist_dates[i],
                        "value": hv,
                        "unit": "",
                        "reference": "",
                    })
        return rows

    async def analyze_lab_document(
        self, 
        db: Session, 
        user_id: int, 
        file_data: bytes, 
        file_name: str, 
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze lab document with advanced multilingual extraction"""
        try:
            logger.info(f"Starting advanced lab document analysis for file: {file_name}")
            
            # Extract text from PDF
            text = self._extract_text_from_pdf(file_data)
            if not text:
                raise ValueError("No text could be extracted from the PDF")
            
            # Detect document language using OpenAI
            detected_language = detect_document_language(text, fallback='en')
            logger.info(f"Detected document language: {detected_language}")
            
            # Get user's preferred language
            from app.utils.user_language import get_user_language_from_cache
            user_language = await get_user_language_from_cache(user_id, db)
            logger.info(f"User preferred language: {user_language}")
            
            # Store detected language for use in section/metric creation
            self._detected_language = detected_language
            
            # Extract lab data using advanced parsing
            lab_data = self._extract_lab_data_advanced(text)
            logger.info(f"Extracted {len(lab_data)} lab records")
            
            # Translate lab data if detected language differs from user language
            translated_data = None
            translation_applied = False
            if detected_language != user_language and detected_language != 'en':
                logger.info(f"Languages differ (detected: {detected_language}, user: {user_language}). Batch translating lab data...")
                try:
                    from app.services.translation_service import TranslationService
                    translation_service = TranslationService()
                    
                    # Use batch translation for efficiency (single API call)
                    translated_data = translation_service.translate_lab_data_batch(
                        lab_data,
                        target_language=user_language,
                        source_language=detected_language
                    )
                    
                    translation_applied = True
                    logger.info(f"Successfully batch translated {len(translated_data)} lab records from {detected_language} to {user_language}")
                except Exception as e:
                    logger.error(f"Failed to translate lab data: {e}", exc_info=True)
                    # Continue without translation if it fails
            
            # If no records found, try OCR fallback
            ocr_used = False
            if len(lab_data) == 0:
                logger.warning("No records extracted with standard method, attempting OCR fallback")
                try:
                    from app.services.ocr_lab_extractor import extract_lab_data_with_ocr
                    lab_data = extract_lab_data_with_ocr(file_data, file_name)
                    ocr_used = True
                    logger.info(f"OCR extraction completed: {len(lab_data)} records found")
                except Exception as ocr_error:
                    logger.error(f"OCR fallback failed: {ocr_error}")
                    # Continue with empty lab_data
            
            # Upload to S3
            s3_url = await self._upload_to_s3(file_data, file_name, str(user_id))
            
            # Create medical document record
            medical_doc = await self._create_medical_document(
                db, user_id, file_name, s3_url, description
            )
            
            # Create health records from extracted data
            created_records = []
            for record_data in lab_data:
                try:
                    health_record = await self._create_health_record_from_lab_data(
                        db, user_id, record_data
                    )
                    if health_record:
                        created_records.append(health_record)
                except Exception as e:
                    logger.error(f"Failed to create health record for {record_data.get('metric_name', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Created {len(created_records)} health records")
            
            return {
                "success": True,
                "message": "Lab document analyzed successfully",
                "s3_url": s3_url,
                "lab_data": lab_data,  # Original data in detected language
                "translated_data": translated_data,  # Translated data (if translation applied)
                "detected_language": detected_language,
                "user_language": user_language,
                "translation_applied": translation_applied,
                "created_records_count": len(created_records),
                "ocr_used": ocr_used
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze lab document: {e}")
            raise

    async def _upload_to_s3(self, file_data: bytes, file_name: str, user_id: str) -> str:
        """Upload file to S3 and return S3 URL"""
        try:
            from app.core.aws_service import aws_service
            file_id = await aws_service.store_document(
                internal_user_id=user_id,
                file_data=file_data,
                file_name=file_name,
                content_type="application/pdf"
            )
            
            # Construct the S3 URL from the file_id
            # The S3 key format is: documents/{user_id}/{file_id}/{file_name}
            from app.core.config import settings
            s3_key = f"documents/{user_id}/{file_id}/{file_name}"
            s3_url = f"s3://{settings.AWS_S3_BUCKET}/{s3_key}"
            
            logger.info(f"Uploaded file to S3: {s3_url}")
            return s3_url
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise

    def _extract_text_from_pdf(self, file_data: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            import pdfplumber
            import io
            
            pdf_file = io.BytesIO(file_data)
            
            with pdfplumber.open(pdf_file) as pdf:
                pages_text = []
                for page in pdf.pages:
                    text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                    if text:
                        pages_text.append(text)
                
                return "\n".join(pages_text)
                
        except ImportError:
            raise ImportError("pdfplumber is required for PDF text extraction")
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

    def _extract_lab_data_advanced(self, text: str) -> List[Dict[str, Any]]:
        """Extract lab data using advanced multilingual parsing"""
        try:
            logger.info("Starting advanced lab data extraction from text")
            
            # Split into pages for page-level historical date extraction
            pages_text = text.split('\n\n')  # Simple page splitting - could be improved
            
            if not pages_text:
                pages_text = [text]
            
            first_page = pages_text[0] if pages_text else ""
            
            report_date = self._extract_report_date(first_page, text)
            lab_name = self._extract_lab_name(text)
            
            logger.info(f"Extracted report date: {report_date}, lab name: {lab_name}")
            
            records: List[Dict] = []
            current_type = ""
            
            # Iterate page-by-page to use page-level historical dates
            for page_text in pages_text:
                if not page_text:
                    continue
                
                # Historical dates present on this page (ignore report_date)
                page_dates = [self._canonicalize_date(m.group(0)) for m in self.MULTI_DATE_RE.finditer(page_text)]
                page_hist_dates = [d for d in page_dates if d and d != report_date][-2:]  # use the two rightmost dates if present
                
                # Process lines in this page
                raw_lines = [self._normalize_units(l) for l in page_text.splitlines() if l.strip()]
                last_metric_name = ""
                started_section = False
                
                for raw in raw_lines:
                    # Skip blocklisted lines early
                    if self._is_blocklisted_line(raw):
                        continue
                    
                    # Track section (mapped to PT canonical names)
                    current_type = self._detect_section_type(raw, current_type)
                    
                    # Skip obvious meta lines early
                    if self.META_NAME_RE.search(raw.strip(": ").strip()):
                        continue
                    
                    # Numeric lines (usual center + reference + historical numbers)
                    rowset = self._parse_numeric_metric_line(raw, page_hist_dates, report_date)
                    
                    # Urine qualitative fallback (only within urine section)
                    if not rowset and current_type == "URINA E DOSEAMENTOS URINÁRIOS":
                        rowset = self._parse_urine_metric_line(raw, report_date, page_hist_dates)
                    
                    if not rowset:
                        # try multi-line metric (previous line name + current numbers)
                        if last_metric_name and re.search(r"\d", raw):
                            combo = f"{last_metric_name} {raw}"
                            rowset = self._parse_numeric_metric_line(combo, page_hist_dates, report_date)
                        
                        # remember plausible metric-only header (require parentheses/colon/comma)
                        if not rowset and (re.search(r"[A-Za-zÁ-úÀ-ÿ]+", raw) and not re.search(r"\d", raw) and len(raw) < 100):
                            candidate = raw.strip(': ').strip()
                            cn = self._norm(candidate)
                            if not self.META_NAME_RE.search(candidate) and re.search(r"[(:,)]", candidate) and not (cn.startswith("exmo") or cn.startswith("hfe")):
                                last_metric_name = candidate
                            else:
                                last_metric_name = ""
                    else:
                        last_metric_name = ""
                    
                    if rowset:
                        started_section = True
                        for r in rowset:
                            out = {
                                "lab_name": lab_name,
                                "type_of_analysis": current_type,
                                **r
                            }
                            records.append(out)
                    elif not started_section:
                        continue
            
            # Deduplicate by (type_of_analysis, metric_name, date_of_value, value)
            seen = set()
            deduped = []
            for r in records:
                key = (r["type_of_analysis"], r["metric_name"], r["date_of_value"], r["value"])
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(r)
            
            logger.info(f"Extracted {len(deduped)} lab records from text")
            for i, record in enumerate(deduped):
                logger.info(f"Record {i+1}: {record.get('metric_name', 'Unknown')} = {record.get('value', 'N/A')} {record.get('unit', '')}")
            
            return deduped
            
        except Exception as e:
            logger.error(f"Failed to extract lab data: {e}")
            return []

    def _cleanup_s3_file(self, s3_url: str) -> None:
        """Clean up S3 file if it exists"""
        if s3_url:
            try:
                from app.core.aws_service import aws_service
                success = aws_service.delete_document(s3_url)
                if success:
                    logger.info(f"Successfully cleaned up S3 file: {s3_url}")
                else:
                    logger.warning(f"Failed to clean up S3 file: {s3_url}")
            except Exception as e:
                logger.error(f"Error cleaning up S3 file {s3_url}: {e}")

    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats to datetime object"""
        if not date_str:
            return None
        
        # First try ISO format (most common from HTML date inputs)
        try:
            # Handle ISO date format (YYYY-MM-DD)
            if len(date_str) == 10 and date_str.count('-') == 2:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            pass
            
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',  # 2024-09-27 (ISO format)
            '%d-%m-%Y',  # 27-09-2024
            '%d/%m/%Y',  # 27/09/2024
            '%Y/%m/%d',  # 2024/09/27
            '%d.%m.%Y',  # 27.09.2024
            '%Y.%m.%d',  # 2024.09.27
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, try to parse as ISO format with timezone
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Could not parse date string: {date_str}")
            return None

    async def _create_medical_document(
        self, 
        db: Session, 
        user_id: int, 
        file_name: str, 
        s3_url: str, 
        description: Optional[str],
        lab_test_date: Optional[str] = None,
        provider: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> HealthRecordDocLab:
        """Create a medical document record"""
        try:
            logger.info(f"Creating medical document with s3_url: {s3_url}")
            
            # Ensure health_record_type_id=1 exists (for lab results/analysis)
            health_record_type_id = self._ensure_health_record_type(db, type_id=1)
            
            # Parse the lab test date if provided
            parsed_lab_test_date = None
            if lab_test_date:
                from app.utils.date_utils import parse_date_string
                try:
                    parsed_lab_test_date = parse_date_string(lab_test_date)
                    logger.info(f"Parsed lab_test_date: {lab_test_date} -> {parsed_lab_test_date}")
                except Exception as date_error:
                    logger.warning(f"Could not parse lab_test_date '{lab_test_date}': {date_error}")
            
            doc_data = HealthRecordDocLabCreate(
                health_record_type_id=health_record_type_id,
                lab_doc_type=document_type or "Other",
                file_name=file_name,
                s3_url=s3_url,
                description=description,
                general_doc_type="lab_result",
                lab_test_date=parsed_lab_test_date,
                provider=provider
            )
            
            medical_doc = health_record_doc_lab_crud.create(db, doc_data, user_id)
            logger.info(f"Created medical document: {medical_doc.id} with s3_url: {medical_doc.s3_url}")
            return medical_doc
            
        except Exception as e:
            logger.error(f"Failed to create medical document: {e}")
            raise

    async def _create_health_record_from_lab_data(
        self, 
        db: Session, 
        user_id: int, 
        record_data: Dict[str, Any]
    ) -> Optional[HealthRecord]:
        """Create health record from extracted lab data"""
        try:
            # Get or create section
            section = await self._get_or_create_section(db, user_id, record_data["type_of_analysis"])
            
            # Get or create metric
            metric = await self._get_or_create_metric(db, user_id, section.id, record_data)
            
            # Create health record
            # Extract numeric value from the record data
            numeric_value = self._extract_numeric_value_from_record(record_data["value"])
            
            health_record_data = HealthRecordCreate(
                section_id=section.id,
                metric_id=metric.id,
                value=numeric_value,
                status=self._determine_status(record_data["value"], record_data.get("reference", "")),
                recorded_at=self._parse_date(record_data["date_of_value"]),
                source="lab_document_upload"
            )
            
            health_record, was_created = health_record_crud.create(db, health_record_data, user_id)
            logger.info(f"Created health record: {health_record.id} for metric: {metric.display_name}")
            return health_record
            
        except Exception as e:
            logger.error(f"Failed to create health record: {e}")
            return None

    def _ensure_health_record_type(self, db: Session, type_id: int = 1) -> int:
        """
        Ensure health record type exists, creating it if necessary.
        Returns the health_record_type_id to use.
        """
        from app.models.health_record import HealthRecordType
        
        health_record_type = db.query(HealthRecordType).filter(HealthRecordType.id == type_id).first()
        
        if not health_record_type:
            # Try to initialize health record types
            logger.warning(f"Health record type ID {type_id} not found. Attempting to initialize...")
            try:
                from app.core.init_db import init_health_record_types
                init_health_record_types(db, force=False)
                # Check again after initialization
                health_record_type = db.query(HealthRecordType).filter(HealthRecordType.id == type_id).first()
            except Exception as init_error:
                logger.error(f"Failed to initialize health record types: {init_error}")
            
            # If still not found, try to use an existing active type as fallback
            if not health_record_type:
                health_record_type = db.query(HealthRecordType).filter(
                    HealthRecordType.is_active == True
                ).first()
                if health_record_type:
                    logger.warning(f"Using health record type ID {health_record_type.id} as fallback (ID {type_id} not available)")
                else:
                    raise ValueError(
                        f"Health record type ID {type_id} is required but not found. "
                        "Please ensure database initialization has run. "
                        "The app should initialize this automatically on startup."
                    )
        
        return health_record_type.id

    async def _get_or_create_section(self, db: Session, user_id: int, section_type: str) -> HealthRecordSection:
        """Get or create health record section (main table only, no tmp table for user-created sections)"""
        try:
            if not section_type:
                raise ValueError("Section type is required but was None or empty")
            section_name = section_type.lower().replace(" ", "_")
            
            # Ensure health_record_type_id=1 exists
            health_record_type_id = self._ensure_health_record_type(db, type_id=1)
            
            # For user-created sections from lab documents, we don't create tmp table entries
            # Only create in main table for UI
            existing_section = db.query(HealthRecordSection).filter(
                HealthRecordSection.name == section_name,
                HealthRecordSection.health_record_type_id == health_record_type_id,
                HealthRecordSection.created_by == user_id
            ).first()
            
            if not existing_section:
                # Create in main table only (no tmp table entry for user-created sections)
                section_data = HealthRecordSectionCreate(
                    name=section_name,
                    display_name=section_type,
                    description="",
                    health_record_type_id=health_record_type_id,
                    is_default=False
                )
                # Use detected language if available, otherwise default to 'en'
                source_language = getattr(self, '_detected_language', None) or 'en'
                existing_section = health_record_section_crud.create(
                    db, section_data, user_id, source_language=source_language
                )
                logger.info(f"Created new user section (no tmp table): {existing_section.display_name} with source_language: {source_language}")
            
            return existing_section
            
        except Exception as e:
            logger.error(f"Failed to get or create section: {e}")
            raise

    async def _get_or_create_metric(
        self, 
        db: Session, 
        user_id: int, 
        section_id: int, 
        record_data: Dict[str, Any]
    ) -> HealthRecordMetric:
        """Get or create health record metric (main table only, no tmp table for user-created metrics)"""
        try:
            metric_name_raw = record_data.get("metric_name")
            if not metric_name_raw:
                raise ValueError("Metric name is required but was None or empty")
            metric_name = metric_name_raw.lower().replace(" ", "_")
            
            # Get the main section
            main_section = db.query(HealthRecordSection).filter(HealthRecordSection.id == section_id).first()
            if not main_section:
                raise ValueError(f"Section with ID {section_id} not found")
            
            # For user-created metrics from lab documents, we don't create tmp table entries
            # Only create in main table for UI
            existing_metric = db.query(HealthRecordMetric).filter(
                HealthRecordMetric.section_id == section_id,
                HealthRecordMetric.name == metric_name
            ).first()
            
            if not existing_metric:
                # Parse reference range using new format
                original_reference = record_data.get("reference_range", "") or record_data.get("reference", "")
                logger.info(f"Original reference string: '{original_reference}'")
                reference_data = self._parse_reference_range_new(original_reference)
                logger.info(f"Parsed reference data: {reference_data}")
                
                # Create threshold object for main table (backward compatibility)
                threshold = None
                if reference_data and reference_data.get("male"):
                    male_range = reference_data["male"]
                    if male_range.get("min") is not None or male_range.get("max") is not None:
                        threshold = {
                            "min": male_range.get("min"),
                            "max": male_range.get("max")
                        }
                
                # Create in main table only (no tmp table entry for user-created metrics)
                metric_data = HealthRecordMetricCreate(
                    section_id=section_id,
                    name=metric_name,
                    display_name=record_data["metric_name"],
                    description=f"Lab metric: {record_data['metric_name']}",
                    default_unit=record_data.get("unit", ""),
                    reference_data=reference_data,
                    data_type="number" if record_data["value"].replace(".", "").replace(",", "").isdigit() else "text",
                    threshold=threshold,
                    is_default=False
                )
                # Use detected language if available, otherwise default to 'en'
                source_language = getattr(self, '_detected_language', None) or 'en'
                existing_metric = health_record_metric_crud.create(
                    db, metric_data, user_id, source_language=source_language
                )
                logger.info(f"Created new user metric (no tmp table): {existing_metric.display_name} with source_language: {source_language} and threshold {threshold}")
            
            return existing_metric
            
        except Exception as e:
            logger.error(f"Failed to get or create metric: {e}")
            raise

    def _parse_reference_range(self, reference_str: str) -> tuple[Optional[float], Optional[float]]:
        """Parse reference range string like '3.90 - 5.10' into min and max values"""
        if not reference_str or not reference_str.strip():
            return None, None
        
        try:
            # Clean the reference string
            ref_clean = reference_str.strip()
            
            # Handle different formats
            if " - " in ref_clean:
                # Format: "3.90 - 5.10"
                parts = ref_clean.split(" - ")
                if len(parts) == 2:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())
                    return min_val, max_val
            elif "-" in ref_clean:
                # Format: "3.90-5.10"
                parts = ref_clean.split("-")
                if len(parts) == 2:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())
                    return min_val, max_val
            elif ref_clean.startswith("<"):
                # Format: "< 5.10"
                max_val = float(ref_clean[1:].strip())
                return None, max_val
            elif ref_clean.startswith(">"):
                # Format: "> 3.90"
                min_val = float(ref_clean[1:].strip())
                return min_val, None
            else:
                # Try to parse as a single number (might be a threshold)
                try:
                    single_val = float(ref_clean)
                    return single_val, single_val
                except ValueError:
                    pass
            
            logger.warning(f"Could not parse reference range: '{reference_str}'")
            return None, None
            
        except Exception as e:
            logger.error(f"Error parsing reference range '{reference_str}': {e}")
            return None, None

    def _parse_reference_range_new(self, reference_str: str) -> Dict[str, Any]:
        """
        Parse reference range string into structured data using new format.
        Returns format: {"male": {"min": value, "max": value}, "female": {"min": value, "max": value}}
        """
        if not reference_str or not reference_str.strip():
            logger.warning(f"Empty reference range string")
            return {"male": {"min": None, "max": None}, "female": {"min": None, "max": None}}
        
        try:
            ref_clean = reference_str.strip().lower()
            logger.info(f"Parsing reference range: '{reference_str}' -> '{ref_clean}'")
            
            # Handle gender-specific ranges
            if "men:" in ref_clean and "female:" in ref_clean:
                result = self._parse_gender_specific_range(ref_clean)
                logger.info(f"Parsed gender-specific range: {result}")
                return result
            
            # Parse simple range and apply to both genders
            parsed_range = self._parse_simple_range(ref_clean)
            result = {
                "male": parsed_range,
                "female": parsed_range
            }
            logger.info(f"Parsed simple range: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing reference range '{reference_str}': {e}")
            return {"male": {"min": None, "max": None}, "female": {"min": None, "max": None}}

    def _parse_gender_specific_range(self, ref_str: str) -> Dict[str, Any]:
        """Parse gender-specific reference ranges"""
        result = {"male": {"min": None, "max": None}, "female": {"min": None, "max": None}}
        
        # Extract male values
        male_match = re.search(r'men:\s*([^,]+)', ref_str)
        if male_match:
            male_ref = male_match.group(1).strip()
            result["male"] = self._parse_simple_range(male_ref)
        
        # Extract female values
        female_match = re.search(r'female:\s*([^,]+)', ref_str)
        if female_match:
            female_ref = female_match.group(1).strip()
            result["female"] = self._parse_simple_range(female_ref)
        
        return result

    def _parse_simple_range(self, ref_str: str) -> Dict[str, Any]:
        """Parse simple reference range without gender"""
        ref_clean = ref_str.strip()
        
        # Handle range format: "3.90 - 5.10" -> min: 3.90, max: 5.10
        if "-" in ref_clean and not ref_clean.startswith("<") and not ref_clean.startswith(">"):
            # Use regex to split on dash with optional spaces around it
            import re
            parts = re.split(r'\s*-\s*', ref_clean)
            if len(parts) == 2:
                try:
                    min_val = self._extract_numeric_value(parts[0].strip())
                    max_val = self._extract_numeric_value(parts[1].strip())
                    if min_val is not None and max_val is not None:
                        logger.info(f"Parsed range '{ref_str}' -> min: {min_val}, max: {max_val}")
                        return {"min": min_val, "max": max_val}
                    else:
                        logger.warning(f"Could not extract numeric values from range parts: '{parts[0]}', '{parts[1]}'")
                except ValueError as e:
                    logger.warning(f"Error parsing range parts: {e}")
        
        # Extract numeric value and operator, ignoring units
        numeric_value = self._extract_numeric_value(ref_clean)
        if numeric_value is None:
            logger.warning(f"Could not extract numeric value from: '{ref_str}'")
            return {"min": None, "max": None}
        
        # Handle >95% -> min: 95.01, max: null
        elif ref_clean.startswith(">"):
            return {"min": numeric_value + 0.01, "max": None}
        
        # Handle >=2 -> min: 2, max: null
        elif ref_clean.startswith(">="):
            return {"min": numeric_value, "max": None}
        
        # Handle <94 -> min: null, max: 93.99
        elif ref_clean.startswith("<") and not ref_clean.startswith("<="):
            return {"min": None, "max": numeric_value - 0.01}
        
        # Handle <=2 -> min: null, max: 2
        elif ref_clean.startswith("<="):
            return {"min": None, "max": numeric_value}
        
        # Try to parse as single number
        return {"min": numeric_value, "max": numeric_value}

    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract numeric value from text, ignoring units like %, cm, etc."""
        import re
        # Find the first number in the text (including decimals)
        match = re.search(r'-?\d+\.?\d*', text)
        if match:
            return float(match.group())
        return None

    def _extract_numeric_value_from_record(self, value: Any) -> float:
        """Extract numeric value from record data, handling both dict and direct values"""
        try:
            # If value is already a number
            if isinstance(value, (int, float)):
                return float(value)
            
            # If value is a string, try to extract numeric value
            if isinstance(value, str):
                # Clean the string and extract numeric value (handles operators like <, >, etc.)
                cleaned = value.replace(",", ".").strip()
                
                # Try to parse as float first (for simple numbers)
                try:
                    return float(cleaned)
                except ValueError:
                    # If that fails, extract numeric value using regex (handles operators)
                    numeric_value = self._extract_numeric_value(cleaned)
                    if numeric_value is not None:
                        return numeric_value
                    else:
                        # If still no numeric value found, try to parse the string differently
                        # Handle cases like "< 0.13" -> extract "0.13"
                        import re
                        match = re.search(r'-?\d+\.?\d*', cleaned)
                        if match:
                            return float(match.group())
                        else:
                            logger.warning(f"Could not extract numeric value from string: {value}")
                            return 0.0
            
            # If value is a dict with 'value' key (old format)
            if isinstance(value, dict) and 'value' in value:
                return self._extract_numeric_value_from_record(value['value'])
            
            # If value is a dict with other structure, try to find numeric values
            if isinstance(value, dict):
                for key, val in value.items():
                    if isinstance(val, (int, float)):
                        return float(val)
                    elif isinstance(val, str):
                        # Recursively try to extract from string values
                        try:
                            return self._extract_numeric_value_from_record(val)
                        except:
                            continue
            
            # Fallback: try to convert to string and extract numeric value
            str_value = str(value)
            numeric_value = self._extract_numeric_value(str_value)
            if numeric_value is not None:
                return numeric_value
            
            # If all else fails, return 0
            logger.warning(f"Could not extract numeric value from: {value}, using 0")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error extracting numeric value from {value}: {e}")
            return 0.0

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in multiple formats"""
        if not date_str:
            return datetime.utcnow()
        
        logger.info(f"Parsing date string: '{date_str}'")
        
        # List of possible date formats to try
        date_formats = [
            "%d-%m-%Y",      # 27-09-2024
            "%Y-%m-%d",      # 2024-09-27
            "%d/%m/%Y",      # 27/09/2024
            "%Y/%m/%d",      # 2024/09/27
            "%d.%m.%Y",      # 27.09.2024
            "%Y.%m.%d",      # 2024.09.27
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                logger.info(f"Successfully parsed date '{date_str}' with format '{date_format}' -> {parsed_date}")
                return parsed_date
            except ValueError:
                continue
        
        # If no format matches, try to parse as ISO format
        try:
            parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            logger.info(f"Successfully parsed date '{date_str}' with ISO format -> {parsed_date}")
            return parsed_date
        except ValueError:
            pass
        
        # If all else fails, return current time
        logger.warning(f"Could not parse date '{date_str}', using current time")
        return datetime.utcnow()

    def _determine_status(self, value: str, reference: str) -> str:
        """Determine status based on value and reference range"""
        if not reference or not value:
            return "normal"
        
        try:
            # Handle numeric values
            if value.replace(".", "").replace(",", "").isdigit():
                num_value = float(value.replace(",", "."))
                
                # Parse reference range (e.g., "3.90 - 5.10" or "74 - 106")
                range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", reference)
                if range_match:
                    min_value = float(range_match.group(1))
                    max_value = float(range_match.group(2))
                    
                    if num_value < min_value or num_value > max_value:
                        return "abnormal"
                    return "normal"
            
            # Handle text values
            if any(term in value.lower() for term in ["negativo", "negative", "ausente", "absent", "não revelou", "not detected"]):
                return "normal"
            if any(term in value.lower() for term in ["positivo", "positive", "presente", "present"]):
                return "abnormal"
            
            return "normal"
            
        except Exception:
            return "normal"
