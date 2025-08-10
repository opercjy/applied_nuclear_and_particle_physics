# 환자 맞춤형 3D 팬텀 기반 몬테카를로 선량계측 파이프라인
**A Monte Carlo Dosimetry Pipeline based on Patient-Specific 3D Phantoms**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. 프로젝트 개요 (Overview)

본 프로젝트는 환자의 CT DICOM 데이터를 기반으로 환자 맞춤형 3D 디지털 팬텀을 생성하고, **OpenGATE (v10.0 이상)** 및 **Geant4** 몬테카를로 시뮬레이션 툴킷을 활용하여 방사선 수송 및 에너지 흡착 과정을 정밀하게 모사하는 파이프라인입니다. 최종적으로 계산된 3차원 선량 분포를 분석하고 시각화하는 전체 과정을 파이썬 코드로 구현합니다.

이 프로젝트는 임상의학, 의학물리, 핵·입자물리학을 융합하는 다학제적 접근법의 구체적인 구현 사례로, 특히 방사성리간드 치료(RLT)와 같은 핵의학 분야의 정밀 선량 평가 연구에 기여하는 것을 목표로 합니다.

## 2. 배경 및 동기 (Background & Motivation)

[cite_start]최근 핵의학은 진단(Diagnosis)과 치료(Therapy)를 결합한 **테라노스틱스(Theranostics)**라는 새로운 패러다임으로 진입하고 있습니다[cite: 7]. [cite_start]특히 `177Lu-PSMA`와 같은 방사성리간드 치료제(RLT)가 성공적으로 도입되면서 [cite: 8][cite_start], `225Ac` 등 알파 핵종을 이용한 치료법까지 그 범위가 확장되고 있습니다[cite: 9].

[cite_start]RLT의 성공은 방사선이 인체 내에서 어떻게 에너지를 전달하는지에 대한 근본적인 이해에 달려있습니다[cite: 36]. [cite_start]본 프로젝트는 핵·입자물리학의 기본 원리에 기반한 정밀 전산 모사를 통해 선량 계측의 정확성을 획기적으로 높이고자 합니다[cite: 39].

## 3. 주요 기능 (Key Features)

-   **DICOM 처리**: 환자의 CT 데이터를 읽고 정렬하여 3D Hounsfield Unit(HU) 배열로 변환합니다.
-   [cite_start]**환자 맞춤형 팬텀 생성**: HU 값을 기반으로 각 복셀(Voxel)에 Geant4 물질 정보와 밀도를 할당하여 시뮬레이션을 위한 3D 디지털 팬텀을 구축합니다[cite: 49, 67].
-   [cite_start]**3D 해부학적 모델링**: `scikit-image` 및 `PyVista`를 사용하여 뼈와 같은 특정 조직의 표면을 3D 메쉬(Mesh)로 렌더링합니다[cite: 69].
-   [cite_start]**다차원 몬테카를로 시뮬레이션**: **OpenGATE v10.0**을 사용하여 Geant4 기반의 거시적(macroscopic) 선량 계산을 수행합니다[cite: 50, 81].
-   **미세선량계측 및 생물학적 효과 예측 확장**:
    -   [cite_start]**Geant4-DNA** 물리 모델을 적용하여 세포 및 아세포 수준의 미세선량(microscopic dose) 분포를 계산할 수 있도록 설계되었습니다[cite: 85].
    -   [cite_start]계산된 선량 분포를 **MIRDcell**과 같은 소프트웨어와 연계하여 세포 생존율 등 생물학적 효과를 예측하는 연구로 확장이 가능합니다[cite: 94].
-   **약동학(PK) 모델링 연계**:
    -   [cite_start]**PK-Sim**과 같은 약동학 툴킷과 연동하여 시계열 영상으로부터 도출된 시간-방사능 곡선(Time-Activity Curve, TAC)을 정밀하게 모델링하고, 이를 시뮬레이션 선원으로 활용할 수 있습니다[cite: 90].

## 4. 프로젝트 파이프라인 (Workflow)

본 프로젝트는 여러 스크립트가 유기적으로 연결된 파이프라인 구조를 가집니다. 각 스크립트는 순서대로 실행되어야 합니다.

1.  **`01_dicom_viewer.py`**: DICOM 파일 로딩 및 3D HU 데이터 변환 후 중앙 단면 CT 이미지를 출력하여 데이터 로딩을 검증합니다.
2.  **`02_surface_rendering.py`**: HU 데이터를 기반으로 뼈와 같은 특정 조직의 3D 표면을 렌더링하여 해부학적 구조를 시각적으로 확인합니다.
3.  **`03_scoring_simulation.py`**: OpenGATE를 사용하여 몬테카를로 선량 시뮬레이션을 실행하고, 3D 선량 분포 데이터 (`.mhd`)를 생성합니다.
4.  **`04_view_dose_distribution.py`**: 생성된 3D 선량 분포를 2D 직교 단면(Axial, Coronal, Sagittal)으로 시각화하여 결과를 개요적으로 파악합니다.
5.  **`05_analysis_and_visualization.py`**: 특정 조직의 선량을 정량 분석하고, PyVista를 이용해 그 결과를 3D로 시각화합니다.

## 5. 기술적 세부사항 및 시뮬레이션 환경

### 전산 모사 툴킷의 선택

물리학 및 공학 분야에서는 다양한 목적에 따라 여러 몬테카를로 시뮬레이션 툴킷이 사용됩니다. 각 분야에서 선호되는 툴킷은 다음과 같습니다.

-   **고에너지물리**: **GEANT4**, Delphes
-   **핵공학 (원자력)**: MCNP
-   **핵물리 응용**: PHITS
-   **방사선 치료**: openTOPAS
-   **영상의학/핵의학**: **OpenGATE**

본 프로젝트는 핵의학 분야의 선량 계측을 목표로 하므로, 해당 분야의 최종 사용자(End-user)들이 가장 선호하고 관련 기능이 특화된 **OpenGATE**를 채택했습니다.

### 임상 장비 및 팬텀 기하학 구현

본 시뮬레이션 플랫폼은 실제 임상 환경과의 연계를 목표로 합니다. [cite_start] 표준 핵의학과에서 운용 중인 **GE Discovery NM/CT 670** (하이브리드 SPECT/CT 시스템) 장비 및 **NEMA IEC 표준 팬텀**과 같이 물리적 특성을 정확히 아는 팬텀에 대한 기하학적 구현이 OpenGATE 환경 내에서 구현 되어 있습니다. 표준 라이브러리보다 정밀 구현 중에 있습니다[cite: 75, 99].

### 플랫폼 검증 및 비교

[cite_start]개발된 플랫폼의 계산 정확도는 물리적 팬텀을 이용한 측정값과 비교하여 검증됩니다[cite: 99]. [cite_start]또한, 임상 표준 선량평가 소프트웨어인 **OLINDA/EXM (MIRD소프트웨어)**의 계산 결과와 상호 비교하여 신뢰도를 확보하는 과정을 포함합니다[cite: 83].

### HU-물질 변환 (HU-to-Material Conversion)

[cite_start]시뮬레이션의 정확도를 위해 CT의 HU 값을 실제 조직의 물질 정보와 밀도로 변환하는 과정이 필수적입니다[cite: 68]. `03_scoring_simulation.py` 스크립트에서는 다음과 같은 룩업 테이블(LUT)을 사용합니다.

```python
# HU-물질 변환 룩업 테이블(LUT)
voxel_materials_lut = [
    [-1024, -900, "G4_AIR"],
    [-900,  -200, "G4_LUNG_ICRP"],
    [-200,   200, "G4_TISSUE_SOFT_ICRP"],
    [200,   3000, "G4_BONE_CORTICAL_ICRP"],
]
```

## 6. 설치 및 사용법 (Setup & Usage)

### 사전 요구사항 (Prerequisites)

-   Python 3.8 이상
-   Rocky Linux 9.6
-   OpenGATE 10.0 이상 (Geant4 포함)
-   필요한 Python 라이브러리: `pydicom`, `numpy`, `matplotlib`, `scikit-image`, `simpleitk`, `pyvista`

### 설치 (Installation)

1.  저장소를 클론하고 해당 디렉토리로 이동합니다.
2.  필요한 Python 패키지를 설치합니다 (`requirements.txt` 파일 생성 후 `pip install -r requirements.txt` 권장).

### 실행 (Execution)

1.  **데이터 준비**: 프로젝트 루트에 환자 DICOM CT 데이터 폴더(예: `Y90S1P26_Tc99m/Y90S1P26_Tc99m_CT`)를 위치시킵니다.
2.  **스크립트 실행**: 파이프라인 순서(`01`~`05`)에 따라 스크립트를 실행합니다.

## 7. 결과 (Results)

| `01_dicom_viewer` | `02_surface_rendering` |
| :---: | :---: |
|  |  |
| **그림 1.** 중앙 축상면 CT 이미지 | **그림 2.** HU>300 임계값으로 재구성한 뼈의 3D 표면 |

| `04_view_dose_distribution` | `05_analysis_and_visualization` |
| :---: | :---: |
| [Image showing three views of a central dose hot spot] |  |
| **그림 3.** 시뮬레이션 선량 분포 (직교 단면) | **그림 4.** PyVista를 이용한 뼈 선량 분포 3D 시각화 |


## 8. 참고문헌 및 주요 인용 (References & Citations)

본 프로젝트는 다음의 연구 및 소프트웨어에 깊이 의존하고 있습니다.

-   **연구 기반**:
    -   [cite_start]전남대학교/전남대학교병원 [cite: 2]
-   **핵심 툴킷**:
    -   **Geant4**: Agostinelli, S., et al. "Geant4—a simulation toolkit." *Nuclear instruments and methods in physics research section A* 506.3 (2003): 250-303.
    -   **OpenGATE**: Jan, S., et al. "GATE: a simulation toolkit for PET and SPECT." *Physics in Medicine & Biology* 49.19 (2004): 4543.
-   **선량계측 방법론**:
    -   **MIRD Pamphlet No. 26**: Siegel, J. A., et al. "MIRD pamphlet no. 26: joint EANM/MIRD guidelines for quantitative 177Lu SPECT/CT for radiopharmaceutical therapy." [cite_start]*Journal of Nuclear Medicine* 61.5 (2020): 754-761. [cite: 136]

## 9. 라이선스 (License)

본 프로젝트는 [MIT 라이선스](https://opensource.org/licenses/MIT)를 따릅니다.
