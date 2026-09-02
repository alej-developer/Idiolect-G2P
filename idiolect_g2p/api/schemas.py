"""
Esquemas de datos Pydantic para la API REST de Idiolect-G2P.
Pydantic data schemas for Idiolect-G2P REST API.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class DialectInfoSchema(BaseModel):
    """Informacion descriptiva de una variante dialectal."""
    code: str
    name: str
    region: str
    description: str
    isogloss_vector: Dict[str, float]


class SandhiJunctureSchema(BaseModel):
    """Información de un evento fonotáctico de frontera de palabra (sandhi externo)."""
    word_index_left: int
    word_index_right: int
    process_type: str
    input_left_coda: str
    input_right_onset: str
    output_phoneme: str
    description: str
    isogloss_condition: Optional[str] = None


class MaxEntConstraintSchema(BaseModel):
    """Detalle formal de una restricción fonológica evaluada por gramática MaxEnt."""
    name: str
    description: str
    is_markedness: bool
    weight: float
    violations: int


class TranscribeRequest(BaseModel):
    """Solicitud de transcripcion fonetica G2P."""
    text: str = Field(..., min_length=1, max_length=10000, description="Texto en espanol a transcribir.")
    dialect_code: Optional[str] = Field("ES_PENINSULAR", description="Codigo del dialecto objetivo.")
    generate_audio: bool = Field(False, description="Indica si debe sintetizarse audio WAV.")
    apply_sandhi: bool = Field(True, description="Indica si se aplican procesos post-léxicos de sandhi.")


class WordTranscriptionSchema(BaseModel):
    """Transcripcion fonetica de una palabra individual."""
    original_text: str
    normalized_text: str
    phonetic_ipa: str
    syllabified_ipa: str
    syllables: List[str]
    stress_index: int


class WordTimingSchema(BaseModel):
    """Marca temporal de una palabra para sincronización de audio en tiempo real."""
    word: str
    normalized_word: Optional[str] = None
    ipa: str
    start_time: float
    end_time: float


class TranscribeResponse(BaseModel):
    """Respuesta de transcripcion fonetica G2P."""
    dialect_code: str
    dialect_name: str
    total_words: int
    transcriptions: List[WordTranscriptionSchema]
    full_ipa_text: str
    audio_base64: Optional[str] = None
    word_timings: Optional[List[WordTimingSchema]] = None
    sandhi_applied: bool = False
    sandhi_junctures: List[SandhiJunctureSchema] = Field(default_factory=list)



class SyllabifyRequest(BaseModel):
    """Solicitud de silabificacion ortografica y prosodica."""
    text: str = Field(..., min_length=1, max_length=10000)


class SyllableInfoSchema(BaseModel):
    """Detalle estructural de una silaba individual."""
    onset: str
    nucleus: str
    coda: str
    is_stressed: bool
    raw_text: str


class WordSyllabificationSchema(BaseModel):
    """Estructura prosodica de una palabra."""
    word: str
    syllables: List[str]
    stress_type: str
    stressed_index: int
    syllable_details: List[SyllableInfoSchema]


class SyllabifyResponse(BaseModel):
    """Respuesta de silabificacion."""
    words: List[WordSyllabificationSchema]


class SynthesizeIPARequest(BaseModel):
    """Solicitud de sintesis acustica a partir de simbolos AFI."""
    ipa_sequence: str = Field(..., min_length=1, max_length=2000, description="Cadena en notacion AFI.")
    sample_rate: int = Field(22050, description="Frecuencia de muestreo (Hz).")


class SynthesizeIPAResponse(BaseModel):
    """Respuesta de sintesis acustica."""
    ipa_sequence: str
    sample_rate: int
    duration_seconds: float
    audio_base64_wav: str


class VerseAnalysisSchema(BaseModel):
    """Analisis metrico de un verso individual."""
    verse_number: int
    raw_text: str
    grammatical_syllables: int
    metrical_syllables: int
    sinalefas_count: int
    final_stress_compensation: int
    rhyme_segment: str


class StanzaAnalysisSchema(BaseModel):
    """Analisis metrico de una estrofa."""
    stanza_number: int
    stanza_type: str
    rhyme_pattern: str
    verses: List[VerseAnalysisSchema]


class AnalyzePoemRequest(BaseModel):
    """Solicitud de analisis metrico versal."""
    poem_text: str = Field(..., min_length=1, max_length=25000, description="Texto completo del poema.")


class AnalyzePoemResponse(BaseModel):
    """Respuesta del analizador metrico versal."""
    detected_stanza_type: str
    global_rhyme_scheme: str
    is_consonant_expected: bool
    total_verses: int
    stanzas: List[StanzaAnalysisSchema]


class ProfileIdiolectRequest(BaseModel):
    """Solicitud de perfilacion forense e inferencia dialectal bayesiana."""
    text: str = Field(..., min_length=5, max_length=25000, description="Texto o poema a perfilar.")
    century_prior: Optional[int] = Field(None, description="Siglo estimado para prior diacronico (12 a 21).")
    case_identifier: str = Field("CASE-G2P-001", description="Identificador pericial del expediente.")


class DialectProbabilitySchema(BaseModel):
    """Probabilidad asignada a una variante dialectal."""
    code: str
    name: str
    region: str
    posterior_probability: float
    phonetic_distance: float
    perfect_rhymes: int


class DiscriminantEvidenceSchema(BaseModel):
    """Evidencia fonologica clave."""
    verse_1: int
    verse_2: int
    word_1: str
    word_2: str
    phenomenon: str
    description: str


class ProfileIdiolectResponse(BaseModel):
    """Respuesta completa del perfilador forense bayesiano."""
    case_identifier: str
    predicted_dialect_code: str
    predicted_dialect_name: str
    confidence_score: float
    isogloss_vector: Dict[str, float]
    dialect_ranking: List[DialectProbabilitySchema]
    discriminant_evidences: List[DiscriminantEvidenceSchema]
    sociolinguistic_conclusion: str
    optimal_transcription_sample: List[str]
    maxent_constraints: List[MaxEntConstraintSchema] = Field(default_factory=list)



class GenerateReportRequest(BaseModel):
    """Solicitud de generacion de informe multi-formato."""
    text: str = Field(..., min_length=5, max_length=25000)
    format_type: str = Field("markdown", description="Formato: latex, bibtex, tei_xml, csv, html, markdown, json, txt")
    case_identifier: str = Field("CASE-G2P-001")
    century_prior: Optional[int] = None


class GenerateReportResponse(BaseModel):
    """Respuesta de generacion de informe."""
    case_identifier: str
    format_type: str
    filename: str
    mime_type: str
    content: str
