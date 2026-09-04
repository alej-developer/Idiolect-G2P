"""
Rutas de la API REST de Idiolect-G2P.
REST API routes for Idiolect-G2P.
"""

from __future__ import annotations
import base64
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status

from .schemas import (
    DialectInfoSchema,
    TranscribeRequest,
    TranscribeResponse,
    WordTranscriptionSchema,
    WordTimingSchema,
    SyllabifyRequest,
    SyllabifyResponse,
    WordSyllabificationSchema,
    SyllableInfoSchema,
    SynthesizeIPARequest,
    SynthesizeIPAResponse,
    AnalyzePoemRequest,
    AnalyzePoemResponse,
    StanzaAnalysisSchema,
    VerseAnalysisSchema,
    ProfileIdiolectRequest,
    ProfileIdiolectResponse,
    DialectProbabilitySchema,
    DiscriminantEvidenceSchema,
    GenerateReportRequest,
    GenerateReportResponse,
)
from ..dialects.registry import GLOBAL_DIALECT_REGISTRY
from ..core.transducer import G2PTransducer
from ..core.syllabifier import syllabify_text
from ..audio.synthesizer import IPAFormantSynthesizer, synthesize_ipa_to_wav
from ..meter.verse_analyzer import analyze_poem
from ..inference.bayesian_profiler import profile_idiolect_from_poem
from ..inference.forensic_explainer import generate_forensic_explanation
from ..reports.report_generator import ReportFormat, generate_report

router = APIRouter(prefix="/api/v1", tags=["Idiolect-G2P Services"])


@router.get("/health", summary="Estado del servicio")
def health_check() -> Dict[str, str]:
    """Comprueba el estado de disponibilidad del microservicio."""
    return {"status": "healthy", "service": "Idiolect-G2P", "version": "1.0.0"}


@router.get("/dialects", response_model=List[DialectInfoSchema], summary="Catalogo de variantes dialectales")
def list_dialects() -> List[DialectInfoSchema]:
    """Lista todos los dialectos panhispanicos y diacronicos soportados con sus vectores de isoglosas."""
    dialects = GLOBAL_DIALECT_REGISTRY.list_all()
    return [
        DialectInfoSchema(
            code=d.code,
            name=d.name,
            region=d.region.value,
            description=d.description,
            isogloss_vector=d.isogloss_vector.to_dict()
        )
        for d in dialects
    ]


@router.post("/transcribe", response_model=TranscribeResponse, summary="Transcripcion fonetica G2P multi-dialectal")
def transcribe_text(req: TranscribeRequest) -> TranscribeResponse:
    """Ejecuta la conversion grafema a fonema bajo una norma dialectal especificada."""
    dialect_code = req.dialect_code or "ES_PENINSULAR"
    dialect = GLOBAL_DIALECT_REGISTRY.get(dialect_code)
    if dialect is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dialecto con codigo '{dialect_code}' no encontrado en el catalogo."
        )

    transducer = G2PTransducer(default_dialect=dialect)
    word_results, connected_ipa, junctures = transducer.transcribe_connected_text(
        req.text,
        dialect=dialect,
        apply_sandhi=req.apply_sandhi
    )

    word_schemas: List[WordTranscriptionSchema] = []
    for r in word_results:
        word_schemas.append(WordTranscriptionSchema(
            original_text=r.prosodic_word.original_text,
            normalized_text=r.prosodic_word.normalized_text,
            phonetic_ipa=r.ipa_transcription,
            syllabified_ipa=r.syllabified_ipa,
            syllables=[s.raw_text for s in r.prosodic_word.syllables],
            stress_index=r.prosodic_word.stressed_syllable_index
        ))

    from .schemas import SandhiJunctureSchema
    sandhi_schemas: List[SandhiJunctureSchema] = [
        SandhiJunctureSchema(
            word_index_left=j.word_index_left,
            word_index_right=j.word_index_right,
            process_type=j.process_type.value,
            input_left_coda=j.input_left_coda,
            input_right_onset=j.input_right_onset,
            output_phoneme=j.output_phoneme,
            description=j.description,
            isogloss_condition=j.isogloss_condition
        )
        for j in junctures
    ]

    full_ipa_text = connected_ipa if req.apply_sandhi else " ".join(r.syllabified_ipa for r in word_results)

    audio_b64: Optional[str] = None
    timings_schemas: Optional[List[WordTimingSchema]] = None

    if req.generate_audio:
        synthesizer = IPAFormantSynthesizer()
        wav_bytes, word_timings = synthesizer.synthesize_text_with_timings(req.text, dialect=dialect)
        audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
        timings_schemas = [
            WordTimingSchema(
                word=wt["word"],
                normalized_word=wt.get("normalized_word"),
                ipa=wt["ipa"],
                start_time=wt["start_time"],
                end_time=wt["end_time"]
            )
            for wt in word_timings
        ]

    return TranscribeResponse(
        dialect_code=dialect.code,
        dialect_name=dialect.name,
        total_words=len(word_results),
        transcriptions=word_schemas,
        full_ipa_text=full_ipa_text,
        audio_base64=audio_b64,
        word_timings=timings_schemas,
        sandhi_applied=req.apply_sandhi,
        sandhi_junctures=sandhi_schemas
    )



@router.post("/syllabify", response_model=SyllabifyResponse, summary="Silabificacion fonotactica y analisis prosodico")
def syllabify_input_text(req: SyllabifyRequest) -> SyllabifyResponse:
    """Silabifica texto aplicando restricciones fonotacticas, acentuacion prosodica y estructura O-N-C."""
    pwords = syllabify_text(req.text)
    word_schemas: List[WordSyllabificationSchema] = []

    for pw in pwords:
        syll_details = [
            SyllableInfoSchema(
                onset=s.onset,
                nucleus=s.nucleus,
                coda=s.coda,
                is_stressed=s.stressed,
                raw_text=s.raw_text
            )
            for s in pw.syllables
        ]
        word_schemas.append(WordSyllabificationSchema(
            word=pw.original_text,
            syllables=[s.raw_text for s in pw.syllables],
            stress_type=pw.stress_type.name,
            stressed_index=pw.stressed_syllable_index,
            syllable_details=syll_details
        ))

    return SyllabifyResponse(words=word_schemas)


@router.post("/synthesize-ipa", response_model=SynthesizeIPAResponse, summary="Sintesis acustica formántica de cadena AFI")
def synthesize_ipa(req: SynthesizeIPARequest) -> SynthesizeIPAResponse:
    """Genera audio WAV PCM lineal a partir de una secuencia en alfabeto fonetico internacional."""
    synthesizer = IPAFormantSynthesizer(sample_rate=req.sample_rate)
    samples = synthesizer.synthesize_ipa_string(req.ipa_sequence)
    wav_bytes = synthesizer.to_wav_bytes(samples)
    duration_sec = len(samples) / float(req.sample_rate)
    b64_audio = base64.b64encode(wav_bytes).decode("ascii")

    return SynthesizeIPAResponse(
        ipa_sequence=req.ipa_sequence,
        sample_rate=req.sample_rate,
        duration_seconds=round(duration_sec, 3),
        audio_base64_wav=b64_audio
    )


@router.post("/analyze-poem", response_model=AnalyzePoemResponse, summary="Escansion metrica y clasificacion estrofica")
def analyze_poetic_meter(req: AnalyzePoemRequest) -> AnalyzePoemResponse:
    """Ejecuta escansion de versos, computo de sinalefas, ley del acento final y clasificacion estrofica."""
    poem = analyze_poem(req.poem_text)
    stanza_schemas: List[StanzaAnalysisSchema] = []

    for s in poem.stanzas:
        v_schemas = [
            VerseAnalysisSchema(
                verse_number=v.verse_number,
                raw_text=v.raw_text,
                grammatical_syllables=v.grammatical_syllables_count,
                metrical_syllables=v.metrical_syllables_count,
                sinalefas_count=v.sinalefas_count,
                final_stress_compensation=v.final_stress_compensation,
                rhyme_segment=v.rhyme_segment_orthographic
            )
            for v in s.verses
        ]
        stanza_schemas.append(StanzaAnalysisSchema(
            stanza_number=s.stanza_number,
            stanza_type=s.stanza_type.value,
            rhyme_pattern=s.rhyme_pattern,
            verses=v_schemas
        ))

    return AnalyzePoemResponse(
        detected_stanza_type=poem.detected_stanza_type.value,
        global_rhyme_scheme=poem.global_rhyme_scheme,
        is_consonant_expected=poem.is_consonant_expected,
        total_verses=len(poem.all_verses),
        stanzas=stanza_schemas
    )


@router.post("/profile-idiolect", response_model=ProfileIdiolectResponse, summary="Inferencia bayesiana del idiolecto y peritaje forense")
def profile_idiolect(req: ProfileIdiolectRequest) -> ProfileIdiolectResponse:
    """Infiere el dialecto optimo y el vector continuo de isoglosas a partir de las restricciones de rima."""
    result = profile_idiolect_from_poem(req.text, century_prior=req.century_prior)
    forensic = generate_forensic_explanation(result, case_id=req.case_identifier)

    ranking_schemas = [
        DialectProbabilitySchema(
            code=dp.dialect_code,
            name=dp.dialect_name,
            region=dp.region,
            posterior_probability=round(dp.posterior_probability, 6),
            phonetic_distance=round(dp.total_phonetic_distance, 4),
            perfect_rhymes=dp.perfect_rhymes_count
        )
        for dp in result.dialect_probabilities
    ]

    evidence_schemas = [
        DiscriminantEvidenceSchema(
            verse_1=ev.verse_1_num,
            verse_2=ev.verse_2_num,
            word_1=ev.word_1,
            word_2=ev.word_2,
            phenomenon=ev.phonetic_phenomenon,
            description=ev.impact_description
        )
        for ev in forensic.discriminant_evidences
    ]

    opt_trans_samples = [
        f"{t.prosodic_word.original_text} -> {t.syllabified_ipa}"
        for t in result.optimal_transcriptions[:12]
    ]

    from ..inference.maxent_grammar import MaxEntGrammar
    from .schemas import MaxEntConstraintSchema
    maxent_calc = MaxEntGrammar()
    weights_dict = maxent_calc.calibrate_weights_from_isoglosses(result.estimated_isogloss_vector)
    maxent_schemas = [
        MaxEntConstraintSchema(
            name=c.name,
            description=c.description,
            is_markedness=c.is_markedness,
            weight=round(weights_dict.get(c.name, 1.0), 3),
            violations=0
        )
        for c in maxent_calc.constraints
    ]

    return ProfileIdiolectResponse(
        case_identifier=req.case_identifier,
        predicted_dialect_code=result.predicted_dialect_code,
        predicted_dialect_name=result.predicted_dialect_name,
        confidence_score=round(result.confidence_score, 4),
        isogloss_vector=result.estimated_isogloss_vector,
        dialect_ranking=ranking_schemas,
        discriminant_evidences=evidence_schemas,
        sociolinguistic_conclusion=forensic.sociolinguistic_conclusion,
        optimal_transcription_sample=opt_trans_samples,
        maxent_constraints=maxent_schemas
    )



@router.post("/generate-report", response_model=GenerateReportResponse, summary="Generacion y exportacion de informe pericial multi-formato")
def generate_report_endpoint(req: GenerateReportRequest) -> GenerateReportResponse:
    """Genera dictamenes descargables en LaTeX, BibTeX, TEI-XML, CSV, HTML, Markdown, JSON o TXT."""
    fmt_str = req.format_type.lower()
    format_map = {
        "latex": (ReportFormat.LATEX, "application/x-latex", "report.tex"),
        "tex": (ReportFormat.LATEX, "application/x-latex", "report.tex"),
        "bibtex": (ReportFormat.BIBTEX, "application/x-bibtex", "citation.bib"),
        "bib": (ReportFormat.BIBTEX, "application/x-bibtex", "citation.bib"),
        "tei_xml": (ReportFormat.TEI_XML, "application/xml", "tei_verse.xml"),
        "xml": (ReportFormat.TEI_XML, "application/xml", "tei_verse.xml"),
        "csv": (ReportFormat.CSV, "text/csv", "dialect_probabilities.csv"),
        "html": (ReportFormat.HTML, "text/html", "report.html"),
        "markdown": (ReportFormat.MARKDOWN, "text/markdown", "report.md"),
        "md": (ReportFormat.MARKDOWN, "text/markdown", "report.md"),
        "json": (ReportFormat.JSON, "application/json", "report.json"),
        "txt": (ReportFormat.TXT, "text/plain", "report.txt"),
    }

    if fmt_str not in format_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato '{req.format_type}' no soportado. Elija entre: {list(format_map.keys())}"
        )

    r_format, mime, fname = format_map[fmt_str]
    result = profile_idiolect_from_poem(req.text, century_prior=req.century_prior)
    content = generate_report(result, format_type=r_format, case_id=req.case_identifier)

    return GenerateReportResponse(
        case_identifier=req.case_identifier,
        format_type=fmt_str,
        filename=f"{req.case_identifier}_{fname}",
        mime_type=mime,
        content=content
    )
