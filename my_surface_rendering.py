# 1. 라이브러리 임포트
import pydicom
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
from skimage import measure  # 이미지 처리 라이브러리, Marching Cubes 알고리즘을 사용하기 위해 임포트
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # Matplotlib에서 3D 모델을 렌더링하기 위한 클래스

# ===================================================================
# 2. DICOM 데이터 로딩 및 3D 변환 (이전 코드 통합)
# 이 부분은 01_dicom_viewer.py와 동일한 과정으로, 3D HU 배열을 생성합니다.
# ===================================================================

# DICOM 파일이 있는 디렉토리 경로 설정
data_path = 'Y90S1P26_Tc99m/Y90S1P26_Tc99m_CT'
dicom_files = glob.glob(os.path.join(data_path, '*.dcm'))

if not dicom_files:
    raise FileNotFoundError(f"'{data_path}' 디렉토리에서 DICOM 파일을 찾을 수 없습니다. 경로를 확인해주세요.")

# 모든 DICOM 파일을 읽고 z축 위치를 기준으로 정렬
slices = [pydicom.dcmread(f) for f in dicom_files]
slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))

# 메타데이터 추출 및 3D 배열 생성
p = slices[0]
pixel_spacing = p.PixelSpacing
slice_thickness = p.SliceThickness
image_size = [int(p.Rows), int(p.Columns), len(slices)]
# 복셀의 물리적 크기를 [x, y, z] 순서로 저장
spacing = np.array([float(pixel_spacing[0]), float(pixel_spacing[1]), float(slice_thickness)])

ct_3d_hu = np.zeros(image_size, dtype=np.int16)
# 각 슬라이스의 픽셀 데이터를 HU로 변환하여 3D 배열에 저장
for i, s in enumerate(slices):
    ct_3d_hu[:, :, i] = (s.pixel_array * s.RescaleSlope) + s.RescaleIntercept

print("DICOM 데이터 로딩 및 3D 변환 완료.")
print(f"이미지 크기: {image_size}, 복셀 크기: {spacing}")


# ===================================================================
# 3. 3D 표면 렌더링
# ===================================================================

# --- 뼈 영역 분할 (Segmentation) ---
# 뼈를 분할하기 위한 HU 임계값을 300으로 설정합니다. (뼈는 보통 +200 HU 이상)
threshold_hu = 300
# HU 배열에서 임계값보다 큰 영역은 1, 아닌 영역은 0으로 이진(binary) 이미지를 생성합니다.
# 이 이미지는 뼈의 위치를 나타내는 3D 마스크 역할을 합니다.
binary_image = ct_3d_hu > threshold_hu

# --- Marching Cubes 알고리즘을 사용하여 표면 메쉬 생성 ---
# 이 알고리즘은 3D 복셀 데이터에서 등고면(isosurface)을 찾아 삼각형 메쉬로 근사합니다.
# 즉, 0과 1의 경계를 찾아 3D 모델의 표면을 생성합니다.
# verts: 메쉬를 구성하는 정점(vertex)들의 3D 좌표 배열
# faces: 어떤 정점 3개가 모여 하나의 삼각형 면(face)을 이루는지 정의하는 배열
# normals: 각 정점에서의 법선 벡터 (조명 계산 등에 사용)
# values: 각 정점에서의 스칼라 값
verts, faces, normals, values = measure.marching_cubes(
    binary_image,       # 입력 3D 데이터
    level=0,            # 표면을 찾을 값의 경계. 이진 이미지이므로 0과 1의 경계인 0 또는 0.5를 사용.
    spacing=spacing     # 복셀의 물리적 크기를 전달하여 실제 비율에 맞는 모델을 생성.
)

# --- 3D 시각화 ---
fig = plt.figure(figsize=(12, 12))  # 12x12 인치 크기의 시각화 창 생성
ax = fig.add_subplot(111, projection='3d')  # 3D 플롯을 위한 서브플롯 추가

# Poly3DCollection을 사용하여 정점과 면 정보로부터 3D 메쉬 객체를 생성합니다.
# verts[faces]는 각 면을 구성하는 정점들의 좌표를 묶어줍니다.
mesh = Poly3DCollection(verts[faces], alpha=0.70)  # alpha는 투명도를 의미

# 메쉬의 색상을 설정합니다 (회색 계열).
face_color = [0.9, 0.9, 0.9]
mesh.set_facecolor(face_color)

# 생성된 메쉬를 3D 플롯에 추가합니다.
ax.add_collection3d(mesh)

# 플롯의 각 축 범위를 물리적 크기(mm)에 맞게 설정합니다.
ax.set_xlim(0, image_size[1] * spacing[1])
ax.set_ylim(0, image_size[0] * spacing[0])
ax.set_zlim(0, image_size[2] * spacing[2])

# 축 레이블과 제목을 설정합니다.
ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_zlabel("Z (mm)")
ax.set_title(f"3D Surface Rendering of Bone (HU > {threshold_hu})")

# 3D 모델을 보기 좋은 각도로 카메라 시점을 조절합니다.
# elev: 고도각(올려다보는 각도), azim: 방위각(수평 회전 각도)
ax.view_init(elev=30, azim=45)

plt.tight_layout()  # 플롯 요소들이 겹치지 않게 조절
plt.show()          # 최종 3D 렌더링 결과를 화면에 표시
