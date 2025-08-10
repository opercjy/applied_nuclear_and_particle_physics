# 1. 라이브러리 임포트
import pydicom
import numpy as np
import os
import glob
import SimpleITK as sitk
import pyvista as pv  # 고급 3D 시각화 및 메쉬 분석을 위한 라이브러리

# ===================================================================
# 2. DICOM 데이터 및 '뼈 마스크' 생성
# ===================================================================
print("1. DICOM 데이터 로딩 및 뼈 마스크 생성...")
data_path = 'Y90S1P26_Tc99m/Y90S1P26_Tc99m_CT'
dicom_files = glob.glob(os.path.join(data_path, '*.dcm'))
if not dicom_files:
    raise FileNotFoundError(f"'{data_path}' 디렉토리에서 DICOM 파일을 찾을 수 없습니다.")

slices = [pydicom.dcmread(f) for f in dicom_files]
slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
p = slices[0]

# --- 중요: PyVista의 축 순서(X, Y, Z)에 맞게 spacing 배열을 명확하게 정의 ---
# DICOM 태그 p.PixelSpacing 순서는 [Row Spacing(Y), Column Spacing(X)] 입니다.
spacing = np.array([
    float(p.PixelSpacing[1]),  # X 간격 (Column)
    float(p.PixelSpacing[0]),  # Y 간격 (Row)
    float(p.SliceThickness)    # Z 간격 (Slice)
])

# NumPy 배열의 축 순서는 (Z, Y, X)를 유지합니다.
ct_3d_hu = np.zeros((len(slices), int(p.Rows), int(p.Columns)), dtype=np.int16)
for i, s in enumerate(slices):
    ct_3d_hu[i, :, :] = (s.pixel_array * s.RescaleSlope) + s.RescaleIntercept

# --- 뼈 마스크 생성 ---
# 뼈 영역을 식별하기 위한 HU 임계값을 설정합니다.
bone_threshold = 200
# 원본 HU 배열과 동일한 크기의, 0으로 채워진 배열을 생성합니다.
bone_mask = np.zeros_like(ct_3d_hu, dtype=np.uint8)
# HU 값이 임계값 이상인 위치(뼈)의 마스크 값을 1로 설정합니다.
bone_mask[ct_3d_hu >= bone_threshold] = 1
print("   마스크 생성 완료.")

# ===================================================================
# 3. 선량 분석 (뼈 영역 한정)
# ===================================================================
print("2. 선량 분석 시작...")
try:
    dose_filename = "output/total_dose.mhd"
    total_dose_image = sitk.ReadImage(dose_filename)
    total_dose_array = sitk.GetArrayFromImage(total_dose_image)
    print(f"   '{dose_filename}' 파일 로딩 완료.")
    
    # --- 핵심 분석 단계 ---
    # 전체 선량 배열에 뼈 마스크를 곱하여, 뼈 영역에 해당하는 선량만 남깁니다.
    # 뼈가 아닌 영역의 선량 값은 모두 0이 됩니다.
    bone_dose_array = total_dose_array * bone_mask
    
    # 뼈 영역에 흡수된 총 선량을 계산합니다.
    total_dose_in_bone = np.sum(bone_dose_array)
    # 뼈 마스크가 1인 위치의 선량 값들만 추출합니다.
    bone_voxels_with_dose = bone_dose_array[bone_mask == 1]
    # 뼈 복셀들의 평균 선량을 계산합니다. (0으로 나누는 오류 방지)
    mean_dose_in_bone = np.mean(bone_voxels_with_dose) if len(bone_voxels_with_dose) > 0 else 0
    # 뼈 영역 내에서의 최대 선량을 계산합니다.
    max_dose_in_bone = np.max(bone_dose_array)
    
    print("\n--- 뼈 영역 선량 분석 결과 ---")
    print(f"뼈(HU > {bone_threshold})에 흡수된 총 선량: {total_dose_in_bone:.5e}")
    print(f"뼈 복셀의 평균 선량: {mean_dose_in_bone:.5e}")
    print(f"뼈 복셀의 최대 선량: {max_dose_in_bone:.5e}")

except FileNotFoundError:
    print(f"\n오류: '{dose_filename}' 파일을 찾을 수 없습니다. 먼저 시뮬레이션 스크립트를 실행하세요.")
    exit()

# ===================================================================
# 4. PyVista를 사용한 3D 시각화
# ===================================================================
print("\n3. PyVista 3D 시각화 시작...")
# PyVista가 사용하는 3D 격자 데이터 구조(ImageData)를 생성합니다.
grid = pv.ImageData()

# --- PyVista 데이터 구조에 정보 할당 ---
# NumPy 배열의 shape은 (Z, Y, X) 순서이지만, PyVista의 dimensions는 (X, Y, Z) 순서를 따릅니다.
grid.dimensions = (ct_3d_hu.shape[2], ct_3d_hu.shape[1], ct_3d_hu.shape[0])
# spacing 배열은 이미 (X, Y, Z) 순서로 만들었으므로 그대로 사용합니다.
grid.spacing = spacing

# --- 스칼라 데이터 추가 ---
# 3D 배열을 PyVista가 사용하는 1D 배열로 변환(flatten)하여 'point_data'에 추가합니다.
# order="C"는 C 스타일(행 우선) 순서로 배열을 펼치라는 의미로, NumPy와 PyVista 간의 호환성을 위해 중요합니다.
grid.point_data["Hounsfield Unit"] = ct_3d_hu.flatten(order="C")
grid.point_data["Bone Dose"] = bone_dose_array.flatten(order="C")

# --- 표면 추출 (Contouring) ---
# HU 스칼라 데이터를 기반으로 200 HU 값을 갖는 등고면을 찾아 뼈 표면 메쉬를 생성합니다.
bone_surface = grid.contour([200], scalars="Hounsfield Unit")
# HU 값이 -200에서 200 사이인 등고면을 찾아 연조직 표면 메쉬를 생성합니다.
soft_tissue_surface = grid.contour([-200, 200], scalars="Hounsfield Unit")

# --- 선량 데이터 매핑 (Interpolation) ---
# 뼈 표면 메쉬(bone_surface)에 원본 grid의 "Bone Dose" 데이터를 보간(interpolate)하여 덧씌웁니다.
# 이 과정을 통해 뼈의 형태와 그 표면의 선량 분포를 하나의 메쉬에서 동시에 표현할 수 있게 됩니다.
bone_surface_with_dose = bone_surface.interpolate(grid, radius=5.0)

# --- PyVista Plotter를 사용하여 시각화 ---
plotter = pv.Plotter(window_size=[1000, 1000]) # 3D 뷰어 창 생성

# 연조직 메쉬를 반투명한 붉은색으로 추가합니다.
plotter.add_mesh(soft_tissue_surface, color="red", opacity=0.1, smooth_shading=True)

# 뼈 메쉬를 추가하되, 표면 색상을 "Bone Dose" 스칼라 값에 따라 표현합니다.
# opacity='linear'는 스칼라 값(선량)이 낮으면 투명하게, 높으면 불투명하게 만들어 선량 집중도를 시각적으로 강조합니다.
plotter.add_mesh(bone_surface_with_dose, scalars="Bone Dose",
                 cmap='nipy_spectral',  # 컬러맵 지정
                 opacity='linear',
                 smooth_shading=True,
                 scalar_bar_args={'title': 'Bone Dose (a.u.)'}) # 컬러바 제목 설정

# --- 뷰어 추가 설정 ---
plotter.camera_position = 'iso'  # 등각 투영 카메라 위치로 설정
plotter.show_grid()              # 그리드 표시
plotter.add_axes()               # X, Y, Z 축 표시
plotter.add_text("Bone Dose Distribution within Soft Tissue", position="upper_edge", font_size=18)

# 3D 뷰어 창을 화면에 표시합니다.
plotter.show()

print("\nPyVista 뷰어 창을 닫으면 프로그램이 종료됩니다.")
