# ACE-Step 추론 API 문서

**Language / 语言 / 言語:** [English](../en/INFERENCE.md) | [中文](../zh/INFERENCE.md) | [日本語](../ja/INFERENCE.md) | [한국어](INFERENCE.md)

---

이 문서는 모든 지원되는 작업 유형에 대한 파라미터 사양을 포함하여 ACE-Step 추론 API에 대한 포괄적인 문서를 제공합니다.

## 목차

- [빠른 시작](#빠른-시작)
- [API 개요](#api-개요)
- [GenerationParams 파라미터](#generationparams-파라미터)
- [GenerationConfig 파라미터](#generationconfig-파라미터)
- [작업 유형](#작업-유형)
- [헬퍼 함수](#헬퍼-함수)
- [전체 예제](#전체-예제)
- [베스트 프랙티스](#베스트-프랙티스)

---

## 빠른 시작

### 기본 사용법

```python
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music

# 핸들러 초기화
dit_handler = AceStepHandler()
llm_handler = LLMHandler()

# 서비스 초기화
dit_handler.initialize_service(
    project_root="/path/to/project",
    config_path="acestep-v15-turbo",
    device="cuda"
)

llm_handler.initialize(
    checkpoint_dir="/path/to/checkpoints",
    lm_model_path="acestep-5Hz-lm-0.6B",
    backend="vllm",
    device="cuda"
)

# 생성 파라미터 구성
params = GenerationParams(
    caption="heavy bass가 있는 활기찬 일렉트로닉 댄스 음악",
    bpm=128,
    duration=30,
)

# 생성 설정 구성
config = GenerationConfig(
    batch_size=2,
    audio_format="flac",
)

# 음악 생성
result = generate_music(dit_handler, llm_handler, params, config, save_dir="/path/to/output")

# 결과 액세스
if result.success:
    for audio in result.audios:
        print(f"생성됨: {audio['path']}")
        print(f"Key: {audio['key']}")
        print(f"Seed: {audio['params']['seed']}")
else:
    print(f"오류: {result.error}")
```

---

## API 개요

### 주요 함수

#### generate_music

```python
def generate_music(
    dit_handler,
    llm_handler,
    params: GenerationParams,
    config: GenerationConfig,
    save_dir: Optional[str] = None,
    progress=None,
    lora_manager=None,
) -> GenerationResult
```

ACE-Step 모델을 사용하여 음악을 생성하는 메인 함수입니다.

#### understand_music

```python
def understand_music(
    llm_handler,
    audio_codes: str,
    temperature: float = 0.85,
    top_k: Optional[int] = None,
    top_p: Optional[float] = None,
    repetition_penalty: float = 1.0,
    use_constrained_decoding: bool = True,
    constrained_decoding_debug: bool = False,
) -> UnderstandResult
```

오디오 시맨틱 코드를 분석하고 메타데이터(caption, lyrics, BPM, 키 등)를 추출합니다.

#### create_sample

```python
def create_sample(
    llm_handler,
    query: str,
    instrumental: bool = False,
    vocal_language: Optional[str] = None,
    temperature: float = 0.85,
    top_k: Optional[int] = None,
    top_p: Optional[float] = None,
    repetition_penalty: float = 1.0,
    use_constrained_decoding: bool = True,
    constrained_decoding_debug: bool = False,
) -> CreateSampleResult
```

자연어 설명에서 완전한 음악 샘플(caption, lyrics, 메타데이터)을 생성합니다.

#### format_sample

```python
def format_sample(
    llm_handler,
    caption: str,
    lyrics: str,
    user_metadata: Optional[Dict[str, Any]] = None,
    temperature: float = 0.85,
    top_k: Optional[int] = None,
    top_p: Optional[float] = None,
    repetition_penalty: float = 1.0,
    use_constrained_decoding: bool = True,
    constrained_decoding_debug: bool = False,
) -> FormatSampleResult
```

사용자가 제공한 caption과 lyrics를 포맷하고 향상하며, 구조화된 메타데이터를 생성합니다.

---

## GenerationParams 파라미터

### 텍스트 입력

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `caption` | `str` | `""` | 원하는 음악의 텍스트 설명. "편안한 피아노 음악"과 같은 간단한 프롬프트 또는 장르, 분위기, 악기 등을 포함한 상세한 설명 가능. 최대 512자. |
| `lyrics` | `str` | `""` | 보컬 음악의 가사 텍스트. 연주곡의 경우 `"[Instrumental]"` 사용. 다국어 지원. 최대 4096자. |
| `instrumental` | `bool` | `False` | True인 경우 가사에 관계없이 연주곡 생성. |

### 음악 메타데이터

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `bpm` | `Optional[int]` | `None` | 분당 비트 수 (30-300). `None`은 LM을 통한 자동 감지 활성화. |
| `keyscale` | `str` | `""` | 음악 키 (예: "C Major", "Am", "F# minor"). 빈 문자열은 자동 감지 활성화. |
| `timesignature` | `str` | `""` | 박자 기호 (2는 '2/4', 3은 '3/4', 4는 '4/4', 6은 '6/8'). 빈 문자열은 자동 감지 활성화. |
| `vocal_language` | `str` | `"unknown"` | 보컬 언어 코드 (ISO 639-1). 지원 지원: `"en"`, `"zh"`, `"ja"`, `"es"`, `"fr"` 등. 자동 감지는 `"unknown"` 사용. |
| `duration` | `float` | `-1.0` | 목표 오디오 길이(초) (10-600). <= 0 또는 None인 경우 가사 길이에 따라 모델이 자동 선택. |

### 생성 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `inference_steps` | `int` | `8` | 디노이징 단계 수. Turbo 모델: 1-20 (권장 8). Base 모델: 1-200 (권장 32-64). 높을수록 품질은 좋지만 느려짐. |
| `guidance_scale` | `float` | `7.0` | Classifier-free guidance scale (1.0-15.0). 높은 값은 텍스트 프롬프트 준수 능력 향상. 비 turbo 모델만 지원. 일반적 범위: 5.0-9.0. |
| `seed` | `int` | `-1` | 재현성을 위한 랜덤 시드. 랜덤 시드는 `-1`, 고정 시드는 임의의 양의 정수 사용. |

### 고급 DiT 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `use_adg` | `bool` | `False` | Adaptive Dual Guidance 사용 (base 모델만 해당). 속도 대신 품질 향상. |
| `cfg_interval_start` | `float` | `0.0` | CFG 적용 시작 비율 (0.0-1.0). Classifier-free guidance 적용 시작 시점 제어. |
| `cfg_interval_end` | `float` | `1.0` | CFG 적용 종료 비율 (0.0-1.0). Classifier-free guidance 적용 종료 시점 제어. |
| `shift` | `float` | `1.0` | 타임스탭 시프트 계수 (범위 1.0-5.0, 기본 1.0). != 1.0인 경우 타임스탭에 `t = shift * t / (1 + (shift - 1) * t)` 적용. turbo 모델은 3.0 권장. |
| `infer_method` | `str` | `"ode"` | 확산 추론 방법. `"ode"`(Euler)는 더 빠르고 결정론적임. `"sde"`(Stochastic)는 분산이 있는 다른 결과를 생성할 수 있음. |
| `timesteps` | `Optional[List[float]]` | `None` | 사용자 정의 타임스탭, 1.0에서 0.0 사이의 부동 소수점 리스트 (예: `[0.97, 0.76, 0.615, 0.5, 0.395, 0.28, 0.18, 0.085, 0]`). 제공된 경우 `inference_steps`와 `shift`를 무시함. |

### 작업별 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `task_type` | `str` | `"text2music"` | 생성 작업 유형. [작업 유형](#작업-유형) 섹션을 참조하십시오. |
| `instruction` | `str` | `"Fill the audio semantic mask based on the given conditions:"` | 작업별 지침 프롬프트. |
| `reference_audio` | `Optional[str]` | `None` | 스타일 전송 또는 연속 생성 작업을 위한 참조 오디오 파일 경로. |
| `src_audio` | `Optional[str]` | `None` | 오디오-투-오디오 작업 (cover, repaint 등)을 위한 소스 오디오 파일 경로. |
| `audio_codes` | `str` | `""` | 사전 추출된 5Hz 오디오 시맨틱 코드 문자열. 고급 사용자용. |
| `repainting_start` | `float` | `0.0` | 리페인팅 시작 시간(초) (repaint/lego 작업용). |
| `repainting_end` | `float` | `-1` | 리페인팅 종료 시간(초). 오디오 끝까지는 `-1` 사용. |
| `audio_cover_strength` | `float` | `1.0` | 오디오 커버/코드 영향 강도 (0.0-1.0). 스타일 전송 작업에는 작은 값(0.2) 설정. |

### 5Hz 언어 모델 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `thinking` | `bool` | `True` | 시맨틱/음악 메타데이터 및 코드를 위한 5Hz 언어 모델 "Chain-of-Thought" 추론 활성화. |
| `lm_temperature` | `float` | `0.85` | LM 샘플링 온도 (0.0-2.0). 높을수록 더 창의적/다양함, 낮을수록 더 보수적임. |
| `lm_cfg_scale` | `float` | `2.0` | LM classifier-free guidance scale. 높을수록 프롬프트 준수 능력 향상. |
| `lm_top_k` | `int` | `0` | LM top-k 샘플링. `0`은 top-k 필터링 비활성화. 일반적인 값: 40-100. |
| `lm_top_p` | `float` | `0.9` | LM nucleus 샘플링 (0.0-1.0). `1.0`은 nucleus 샘플링 비활성화. 일반적인 값: 0.9-0.95. |
| `lm_negative_prompt` | `str` | `"NO USER INPUT"` | LM 가이드를 위한 부정 프롬프트. 원하지 않는 특징을 피하는 데 도움됨. |
| `use_cot_metas` | `bool` | `True` | LM CoT 추론을 사용하여 메타데이터 생성 (BPM, 키, 길이 등). |
| `use_cot_caption` | `bool` | `True` | LM CoT 추론을 사용하여 사용자 caption 향상. |
| `use_cot_language` | `bool` | `True` | LM CoT 추론을 사용하여 보컬 언어 감지. |
| `use_cot_lyrics` | `bool` | `False` | (향후 사용을 위해 예약됨) LM CoT를 사용하여 가사 생성/향상. |
| `use_constrained_decoding` | `bool` | `True` | 구조화된 LM 출력을 위한 제약된 디코딩 활성화. |

### LoRA 지원 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `lora_id` | `Optional[str]` | `None` | 사용할 업로드된 LoRA 어댑터의 ID. |
| `lora_scale` | `float` | `1.0` | LoRA 어댑터의 영향 스케일 (0.0-1.0). |

---

## GenerationConfig 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `batch_size` | `int` | `2` | 병렬로 생성할 샘플 수 (1-8). 높은 값은 더 많은 GPU 메모리 필요. |
| `allow_lm_batch` | `bool` | `False` | LM의 배치 처리 허용. `batch_size >= 2`이고 `thinking=True`인 경우 더 빠름. |
| `use_random_seed` | `bool` | `True` | 랜덤 시드 사용 여부. `True`는 매번 다른 결과, `False`는 재현 가능한 결과. |
| `seeds` | `Optional[List[int]]` | `None` | 배치 생성을 위한 시드 리스트. batch_size보다 적게 제공되면 랜덤 시드로 채움. 단일 정수도 가능. |
| `lm_batch_chunk_size` | `int` | `8` | LM 추론 청크당 최대 배치 크기 (GPU 메모리 제약). |
| `constrained_decoding_debug` | `bool` | `False` | 제약된 디코딩을 위한 디버그 로깅 활성화. |
| `audio_format` | `str` | `"flac"` | 출력 오디오 형식. 옵션: `"mp3"`, `"wav"`, `"flac"`. 빠른 저장을 위해 FLAC이 기본값임. |

---

## 작업 유형

ACE-Step은 각각 특정 사용 사례에 최적화된 6가지 생성 작업 유형을 지원합니다.

### 1. Text2Music (기본값)

**목적**: 텍스트 설명 및 선택적 메타데이터에서 음악을 생성합니다.

**사례**:
- 텍스트 설명에서 음악 생성
- 프롬프트에서 반주 트랙 제작
- 가사가 있는 노래 생성

### 2. Cover

**목적**: 기존 오디오를 변환하여 구조를 유지하면서 스타일/음색을 변경합니다.

**사례**:
- 다른 스타일의 커버 제작
- 멜로디를 유지하면서 악기 구성 변경
- 장르 변환

### 3. Repaint

**목적**: 오디오의 특정 시간 세그먼트를 재생성하고 나머지는 변경하지 않습니다.

**사례**:
- 생성된 음악의 특정 섹션 수정
- 노래의 일부 섹션에 변형 추가
- 부드러운 전환 효과 생성
- 문제가 있는 세그먼트 교체

### 4. Lego (Base 모델 전용)

**목적**: 기존 오디오의 컨텍스트에서 특정 악기 트랙을 생성합니다.

**사례**:
- 특정 악기 트랙 추가
- 반주 트랙 위에 추가 악기 레이어링
- 다중 트랙 작업을 반복적으로 제작

### 5. Extract (Base 모델 전용)

**목적**: 믹스 오디오에서 특정 악기 트랙을 추출/분리합니다.

**사례**:
- 스템 분리
- 특정 악기 격리
- 리믹스 제작
- 개별 트랙 분석

### 6. Complete (Base 모델 전용)

**목적**: 지정된 악기로 부분적인 트랙을 완성/확장합니다.

**사례**:
- 미완성 작업 편곡
- 반주 트랙 추가
- 음악 아이디어 자동 완성

---

## 헬퍼 함수

### understand_music

오디오 코드를 분석하여 음악에 대한 메타데이터를 추출합니다.

### create_sample

자연어 설명에서 완전한 음악 샘플을 생성합니다. 이것은 "Simple Mode" / "Inspiration Mode" 기능입니다.

### format_sample

사용자가 제공한 caption과 lyrics를 포맷하고 향상하며, 구조화된 메타데이터를 생성합니다.

---

## 베스트 프랙티스

### 1. Caption 작성법

**좋은 예**:
- `"heavy bass와 신시사이저 리드가 있는 활기찬 일렉트로닉 댄스 음악"` (구체적임)
- `"어쿠스틱 기타와 부드러운 보컬이 있는 우울한 인디 포크"` (분위기와 장르 포함)
- `"피아노, 업라이트 베이스, 브러시 드럼이 있는 재즈 트리오"` (악기 지정)

### 2. 파라미터 튜닝

- **최고 품질**: base 모델 사용, `inference_steps=64` 이상, `use_adg=True`, `shift=3.0` 권장.
- **빠른 속도**: turbo 모델 사용, `inference_steps=8`, ADG 비활성화, `"ode"` 추론 방법 사용.
- **일관성**: `use_random_seed=False`, 고정 `seed` 사용, 낮은 `lm_temperature` (0.7-0.85).
- **다양성**: `use_random_seed=True`, 높은 `lm_temperature` (0.9-1.1), `batch_size > 1` 사용.

---

상세 정보는 다음을 참조하십시오:
- 메인 README: [`../../README.md`](../../README.md)
- REST API 문서: [`API.md`](API.md)
- Gradio 데모 가이드: [`GRADIO_GUIDE.md`](GRADIO_GUIDE.md)
