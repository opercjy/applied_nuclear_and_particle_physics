# 1. 라이브러리 임포트
import opengate as gate          # OpenGATE 시뮬레이션 라이브러리
import pydicom
import numpy as np
import os
import glob
import SimpleITK as sitk         # 의료 영상 처리 및 분석을 위한 라이브러리 (팬텀 파일 생성에 사용)

# ===================================================================
# 2. DICOM 데이터 로딩
# 이 부분은 이전 스크립트들과 동일하게 3D CT HU 데이터를 준비합니다.
# 단, OpenGATE/SimpleITK의 축 순서(Z, Y, X)에 맞게 배열을 생성합니다.
# ===================================================================
print("1. DICOM 데이터 로딩 시작...")
data_path = 'Y90S1P26_Tc99m/Y90S1P26_Tc99m_CT'
dicom_files = glob.glob(os.path.join(data_path, '*.dcm'))
if not dicom_files:
    raise FileNotFoundError(f"'{data_path}' 디렉토리에서 DICOM 파일을 찾을 수 없습니다.")

slices = [pydicom.dcmread(f) for f in dicom_files]
slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
p = slices[0]

# 이미지 크기와 복셀 간격을 정의합니다.
image_size = [int(p.Columns), int(p.Rows), len(slices)]
spacing = np.array([float(p.PixelSpacing[0]), float(p.PixelSpacing[1]), float(p.SliceThickness)])

# (Z, Y, X) 순서의 NumPy 배열을 생성하고 HU 값으로 채웁니다.
ct_3d_hu = np.zeros((len(slices), int(p.Rows), int(p.Columns)), dtype=np.int16)
for i, s in enumerate(slices):
    ct_3d_hu[i, :, :] = (s.pixel_array * s.RescaleSlope) + s.RescaleIntercept
print("   DICOM 데이터 로딩 및 3D 변환 완료.")

# ===================================================================
# 3. OpenGATE 시뮬레이션 설정
# ===================================================================
print("2. OpenGATE 시뮬레이션 설정 시작...")
# 시뮬레이션 객체를 생성합니다.
sim = gate.Simulation()

# --- 시뮬레이션 기본 설정 ---
sim.progress_bar = True              # 시뮬레이션 진행 상황을 프로그래스바로 표시
sim.number_of_threads = 8            # 시뮬레이션에 사용할 CPU 스레드 수
sim.output_dir = 'output'            # 결과 파일이 저장될 디렉토리

# --- 단위 설정 ---
# Geant4의 단위 시스템을 가져와 변수로 사용하면 코드가 명확해집니다.
mm = gate.g4_units.mm
keV = gate.g4_units.keV

# --- 월드(World) 설정 ---
# 시뮬레이션이 일어날 가상 공간을 정의합니다. 팬텀보다 약간 크게 설정합니다.
sim.world.size = (np.array(image_size) * spacing + 20) * mm
# 월드 공간을 채울 기본 물질을 공기로 설정합니다.
sim.world.material = "G4_AIR"

# --- 물리(Physics) 설정 ---
# 시뮬레이션에 적용할 물리 법칙 목록을 지정합니다. (QGSP_BIC_HP는 표준 중 하나)
sim.physics_manager.physics_list_name = 'QGSP_BIC_HP'
# 방사성 동위원소의 붕괴 현상을 시뮬레이션에 포함할지 여부 (이 예제에서는 직접 감마선을 쏘므로 필수 아님)
sim.user_info.radioactive_decay = True

# --- CT 팬텀(Phantom) 설정 ---
# 'Image' 타입의 볼륨을 추가하여 CT 데이터를 팬텀으로 사용합니다.
phantom = sim.add_volume('Image', 'ct_phantom')
# NumPy 배열을 SimpleITK 이미지 객체로 변환합니다.
sitk_image = sitk.GetImageFromArray(ct_3d_hu)
# 이미지의 복셀 간격과 원점 정보를 설정합니다. 원점을 중앙으로 맞춰 좌표계를 다루기 쉽게 합니다.
sitk_image.SetSpacing(spacing)
sitk_image.SetOrigin(-(np.array(image_size) * spacing / 2.0))
# OpenGATE가 읽을 수 있도록 팬텀을 .mhd 파일 포맷으로 저장합니다.
image_filename = os.path.join(sim.output_dir, "phantom_hu.mhd")
sitk.WriteImage(sitk_image, image_filename)
phantom.image = image_filename # 팬텀에 사용할 이미지 파일 지정

# HU-물질 변환 룩업 테이블(LUT)을 정의합니다.
# [HU 최소값, HU 최대값, Geant4 물질 이름] 형식입니다.
voxel_materials_lut = [
    [-1024, -900, "G4_AIR"],
    [-900,  -200, "G4_LUNG_ICRP"],
    [-200,   200, "G4_TISSUE_SOFT_ICRP"],
    [200,   3000, "G4_BONE_CORTICAL_ICRP"],
]
phantom.voxel_materials = voxel_materials_lut

# --- 방사선원(Source) 설정 ---
source = sim.add_source('GenericSource', 'gamma_gun')
source.particle = 'gamma'         # 방출할 입자 종류
source.n = 1e6                    # 방출할 입자 개수 (통계량)
source.energy.mono = 364 * keV    # 입자의 에너지 (단일 에너지)
source.position.type = 'box'      # 선원의 모양 (작은 상자)
source.position.size = np.array([10, 10, 10]) * mm # 선원의 크기
source.position.center = np.array([0, 0, 0]) * mm # 선원의 중심 위치
source.direction.type = 'iso'     # 방출 방향 (모든 방향으로 균일하게)

# --- 액터(Actor) 설정: 결과 수집기 ---
# 'DoseActor'를 추가하여 특정 볼륨 내의 흡수 선량을 계산합니다.
dose_actor = sim.add_actor('DoseActor', 'total_dose')
dose_actor.attached_to = 'ct_phantom'  # 선량을 측정할 대상 볼륨을 팬텀으로 지정
dose_actor.output_filename = 'total_dose.mhd' # 선량 분포 결과 파일 이름
# 선량 그리드의 크기, 간격, 위치를 팬텀과 동일하게 설정하여 1:1 매칭
dose_actor.size = image_size
dose_actor.spacing = spacing
dose_actor.translation = phantom.translation
# 에너지 흡수량(Dose)을 기록하도록 설정
dose_actor.SetDoseFlag(True)

# 시뮬레이션 통계(실행 시간, 이벤트 수 등)를 기록할 액터를 추가합니다.
stats = sim.add_actor('SimulationStatisticsActor', 'stats')
print("   시뮬레이션 설정 완료.")

# ===================================================================
# 4. 시뮬레이션 실행
# ===================================================================
print("3. 시뮬레이션 실행 시작...")
# 설정된 내용으로 시뮬레이션을 실행합니다.
sim.run()

# 시뮬레이션 완료 후 결과 정보를 출력합니다.
print("\n-------------------------------------------------")
print(f"시뮬레이션 완료")
print(f"결과 파일: {sim.output_dir}/{dose_actor.output_filename}")
print("-------------------------------------------------")
print(stats) # 통계 액터의 결과 출력
