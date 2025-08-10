# In[1]: 필요한 라이브러리 임포트
import pydicom  # DICOM 파일을 읽고 파싱하기 위한 라이브러리
import numpy as np  # 다차원 배열 및 수치 연산을 위한 라이브러리
import matplotlib.pyplot as plt  # 데이터 시각화를 위한 라이브러리
import os  # 운영체제와 상호작용하기 위한 라이브러리 (파일 경로 등)
import glob  # 특정 패턴에 맞는 파일 목록을 가져오기 위한 라이브러리

# In[2]: DICOM 파일이 있는 디렉토리 경로 설정
# --- 사용자가 수정해야 할 부분 ---
# 실제 DICOM 파일들이 저장된 폴더 경로를 지정합니다.
data_path = 'Y90S1P26_Tc99m/Y90S1P26_Tc99m_CT'

# glob.glob을 사용하여 해당 디렉토리 내의 모든 .dcm 파일을 찾습니다.
dicom_files = glob.glob(os.path.join(data_path, '*.dcm'))

# 파일이 없는 경우, 오류를 발생시켜 사용자에게 경로 확인을 요청합니다.
if not dicom_files:
    raise FileNotFoundError(f"'{data_path}' 디렉토리에서 DICOM 파일을 찾을 수 없습니다. 경로를 확인해주세요.")

# In[3]: 모든 DICOM 파일을 읽고 z축 위치를 기준으로 정렬
# pydicom.dcmread()를 사용하여 리스트의 각 파일 경로에 해당하는 DICOM 파일을 읽어들입니다.
slices = [pydicom.dcmread(f) for f in dicom_files]

# CT 슬라이스는 파일 이름 순서가 아닌, 실제 촬영된 z축 위치에 따라 정렬되어야 합니다.
# DICOM 태그 (0020,0032) ImagePositionPatient의 세 번째 값(z 좌표)을 기준으로 슬라이스들을 정렬합니다.
# 이 방법은 (0020,1041) SliceLocation 태그보다 더 정확하고 보편적입니다.
slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))

# In[4]: 정렬된 슬라이스에서 3D 이미지 배열 및 정보 추출
# 첫 번째 슬라이스에서 후속 계산에 필요한 메타데이터를 추출합니다.
p = slices[0]
pixel_spacing = p.PixelSpacing  # 픽셀 간격 (x, y 간격) (mm)
slice_thickness = p.SliceThickness  # 슬라이스 두께 (z 간격) (mm)
image_size = [int(p.Rows), int(p.Columns), len(slices)]  # 최종 3D 이미지의 크기 (행, 열, 슬라이스 개수)

# 복셀(Voxel, 3D 픽셀)의 물리적 크기를 [x, y, z] 순서로 저장합니다.
spacing = np.array([float(pixel_spacing[0]), float(pixel_spacing[1]), float(slice_thickness)])

# 3D 이미지 데이터를 담을 빈 NumPy 배열을 생성합니다. 데이터 타입은 int16으로 설정합니다.
ct_3d = np.zeros(image_size, dtype=np.int16)

# 정렬된 슬라이스 리스트를 순회하며 각 2D 슬라이스의 픽셀 데이터를 3D 배열의 해당 위치에 채워 넣습니다.
for i, s in enumerate(slices):
    ct_3d[:, :, i] = s.pixel_array

# Hounsfield Unit (HU) 변환: CT 장비에서 얻은 픽셀 값은 상대적인 값이므로,
# 표준화된 HU 단위로 변환해야 조직의 밀도를 정확히 나타낼 수 있습니다.
# HU = pixel_value * RescaleSlope + RescaleIntercept
slope = p.RescaleSlope  # (0028,1053) Rescale Slope
intercept = p.RescaleIntercept  # (0028,1052) Rescale Intercept

# float64로 변환하여 정밀한 계산을 수행한 뒤, 다시 int16으로 변환하여 메모리를 효율적으로 사용합니다.
ct_3d_hu = ct_3d.astype(np.float64) * slope + intercept
ct_3d_hu = ct_3d_hu.astype(np.int16)

# In[5]: 결과 확인 - 3D 이미지 정보 출력 및 중앙 슬라이스 시각화
print("3D 이미지 생성 완료!")
print(f"이미지 크기 (보셀 수): {image_size[0]} x {image_size[1]} x {image_size[2]}")
print(f"복셀 크기 (mm): {spacing[0]:.2f} x {spacing[1]:.2f} x {spacing[2]:.2f}")
print(f"Hounsfield Unit (HU) 범위: {ct_3d_hu.min()} ~ {ct_3d_hu.max()}")

# 3D 볼륨의 가장 중앙에 위치한 슬라이스를 시각화하여 데이터가 잘 로드되었는지 확인합니다.
central_slice_index = len(slices) // 2
plt.figure(figsize=(8, 8))  # 시각화 창의 크기를 설정합니다.
# imshow 함수를 사용하여 2D 배열을 이미지로 표시합니다. cmap=plt.cm.gray는 흑백 명암으로 표시하라는 의미입니다.
plt.imshow(ct_3d_hu[:, :, central_slice_index], cmap=plt.cm.gray)
plt.title(f'Central Slice (Index: {central_slice_index})')  # 제목 설정
plt.xlabel('X (pixels)')  # x축 레이블 설정
plt.ylabel('Y (pixels)')  # y축 레이블 설정
plt.colorbar(label='Hounsfield Unit (HU)')  # HU 값을 나타내는 컬러바 추가
plt.show()  # 최종 이미지를 화면에 표시합니다.
