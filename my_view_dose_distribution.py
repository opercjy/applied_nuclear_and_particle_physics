# view_dose_distribution.py

import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import os

# --- 1. 선량 파일 로드 ---
# OpenGATE 시뮬레이션 결과로 생성된 선량 파일 경로를 지정합니다.
# 파일 이름은 OpenGATE 버전에 따라 '_edep' 접미사가 붙을 수 있습니다.
dose_filename = 'output/total_dose.mhd' 

print(f"'{dose_filename}' 파일을 로딩합니다...")

# 파일 로딩 시 발생할 수 있는 오류를 처리하기 위해 try-except 구문을 사용합니다.
try:
    # SimpleITK를 사용하여 .mhd 이미지 파일을 읽습니다.
    dose_image = sitk.ReadImage(dose_filename)
    # 이미지 객체를 NumPy 배열로 변환하여 수치 분석 및 시각화를 준비합니다.
    dose_array = sitk.GetArrayFromImage(dose_image)
except Exception as e:
    print(f"오류: {e}")
    print(f"'{dose_filename}' 파일을 찾을 수 없거나 읽을 수 없습니다. 시뮬레이션이 성공적으로 완료되었는지, 파일 이름이 정확한지 확인해주세요.")
    exit() # 파일 로딩 실패 시 프로그램 종료

print("파일 로딩 완료.")

# --- 2. 전체 선량 통계 확인 ---
# NumPy를 사용하여 3D 선량 배열의 기본적인 통계를 계산합니다.
max_dose = np.max(dose_array)          # 최대 선량 (Hot spot)
mean_dose = np.mean(dose_array)        # 평균 선량
total_dose = np.sum(dose_array)        # 총 흡수 선량

print("\n--- 전체 볼륨 선량 분석 결과 ---")
print(f"최대 선량 (Max Dose): {max_dose:.5e}")  # 지수 표기법으로 출력
print(f"평균 선량 (Mean Dose): {mean_dose:.5e}")
print(f"총 선량 (Total Dose): {total_dose:.5e}")

# --- 3. 3개 단면(Axial, Coronal, Sagittal) 슬라이스 추출 ---
# 3D 배열의 각 축(Z, Y, X)에서 중앙에 위치한 2D 슬라이스의 인덱스를 계산합니다.
z_slice_index = dose_array.shape[0] // 2
y_slice_index = dose_array.shape[1] // 2
x_slice_index = dose_array.shape[2] // 2

# NumPy 슬라이싱을 사용하여 각 단면을 추출합니다.
axial_slice = dose_array[z_slice_index, :, :]    # 축상면 (Z축 고정)
coronal_slice = dose_array[:, y_slice_index, :]  # 관상면 (Y축 고정)
sagittal_slice = dose_array[:, :, x_slice_index] # 시상면 (X축 고정)

# --- 4. Matplotlib으로 시각화 및 파일 저장 ---
print("\nMatplotlib을 사용하여 3개 단면을 이미지 파일로 저장합니다...")

# 1행 3열의 서브플롯을 생성하여 세 단면을 나란히 표시합니다.
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
# 컬러맵을 'inferno'로 설정하여 선량의 세기를 시각적으로 표현합니다 (어두운색->밝은색).
cmap = 'inferno'

# 각 서브플롯에 단면 이미지를 그립니다.
# origin='lower'는 배열의 (0,0) 인덱스를 그림의 왼쪽 아래에 위치시킵니다.
# 축상면 (Axial View)
im1 = axes[0].imshow(axial_slice, cmap=cmap, origin='lower')
axes[0].set_title(f'Axial (Transverse) View\n(Z = {z_slice_index})')
axes[0].set_xlabel('X-axis')
axes[0].set_ylabel('Y-axis')

# 관상면 (Coronal View)
im2 = axes[1].imshow(coronal_slice, cmap=cmap, origin='lower')
axes[1].set_title(f'Coronal View\n(Y = {y_slice_index})')
axes[1].set_xlabel('X-axis')
axes[1].set_ylabel('Z-axis')

# 시상면 (Sagittal View)
im3 = axes[2].imshow(sagittal_slice, cmap=cmap, origin='lower')
axes[2].set_title(f'Sagittal View\n(X = {x_slice_index})')
axes[2].set_xlabel('Y-axis')
axes[2].set_ylabel('Z-axis')

# 전체 그림에 대한 컬러바를 추가합니다.
fig.colorbar(im1, ax=axes, orientation='vertical', fraction=0.046, pad=0.04, label='Dose (Arbitrary Units)')
# 그림의 전체 제목을 설정합니다.
fig.suptitle('전체 선량 분포 (Orthogonal Views)', fontsize=16)
# 레이아웃을 조절하여 제목과 그림이 겹치지 않게 합니다.
plt.tight_layout(rect=[0, 0, 1, 0.96])

# plt.show() 대신 plt.savefig()를 사용하여 시각화 결과를 파일로 저장합니다.
output_image_filename = 'dose_distribution.png'
plt.savefig(output_image_filename)

print(f"\n시각화 성공! ")
print(f"결과가 '{output_image_filename}' 파일로 저장되었습니다.")
