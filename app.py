import streamlit as st
import pandas as pd
import subprocess
import tempfile
import shutil
from pathlib import Path
import zipfile
import io
import os

# 检查并安装R包
@st.cache_resource
def install_r_packages():
    """首次运行时安装R包"""
    try:
        # 检查MALDIquant和MALDIquantForeign是否都已安装
        result = subprocess.run(
            ['Rscript', '-e', 'library(MALDIquant); library(MALDIquantForeign); library(readxl)'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            # 需要安装R包
            st.info("⏳ 检测到R包未完全安装，正在安装（约需3-5分钟）...")
            st.text("正在安装: MALDIquant, MALDIquantForeign, readxl")
            
            install_script = Path('install_r_packages.R')
            if install_script.exists():
                # 显示安装进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📦 正在下载和安装R包...")
                progress_bar.progress(30)
                
                result = subprocess.run(
                    ['Rscript', str(install_script)],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                progress_bar.progress(90)
                
                if result.returncode == 0:
                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()
                    st.success("✅ R包安装完成！")
                    
                    # 显示安装日志
                    with st.expander("查看安装日志"):
                        st.code(result.stdout, language='text')
                    
                    return True
                else:
                    st.error(f"❌ R包安装失败")
                    st.code(result.stdout, language='text')
                    st.code(result.stderr, language='text')
                    return False
            else:
                st.error("❌ 找不到 install_r_packages.R 文件")
                return False
        
        return True
        
    except Exception as e:
        st.warning(f"⚠️ 无法自动安装R包: {str(e)}")
        return False

# 页面配置
st.set_page_config(
    page_title="MALDI-TOF MS 模版化处理平台",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 启动时安装R包
if 'r_packages_checked' not in st.session_state:
    st.session_state.r_packages_checked = install_r_packages()

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
        text-align: center;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 2rem;
        text-align: center;
    }
    .phase-header {
        background: linear-gradient(90deg, #1f77b4 0%, #4a9eff 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'template_created' not in st.session_state:
    st.session_state.template_created = False
if 'template_data' not in st.session_state:
    st.session_state.template_data = None

def extract_files_from_zip(zip_file):
    """从ZIP文件中提取TXT和Excel文件"""
    txt_files = []
    excel_file = None
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            if file_name.lower().endswith('.txt') and not file_name.startswith('__MACOSX'):
                content = zip_ref.read(file_name)
                base_name = Path(file_name).name
                txt_files.append((content, base_name))  # (content, name)
            elif file_name.lower().endswith(('.xlsx', '.xls')) and not file_name.startswith('__MACOSX'):
                if excel_file is None:
                    content = zip_ref.read(file_name)
                    base_name = Path(file_name).name
                    excel_file = (content, base_name)  # (content, name)
    
    return txt_files, excel_file

def check_r_installation():
    """检查R是否安装"""
    try:
        result = subprocess.run(['Rscript', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.returncode == 0
    except:
        return False

def run_r_script(script_content, work_dir):
    """执行R脚本"""
    script_path = Path(work_dir) / "process.R"
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    try:
        result = subprocess.run(
            ['Rscript', str(script_path)],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=600
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "处理超时（超过10分钟）", 1
    except Exception as e:
        return "", f"执行R脚本出错: {str(e)}", 1

# 主界面
st.markdown('<div class="main-header">🔬 MALDI-TOF MS 模版化处理平台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">基于训练集建立特征模版，批量处理验证集</div>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("📋 处理策略")
    st.info("""
    **模版化处理流程：**
    
    1️⃣ **阶段1**：处理训练集
       - 上传训练集ZIP
       - 建立特征模版
       - 保存参数配置
    
    2️⃣ **阶段2**：处理验证集
       - 使用训练集模版
       - 批量处理多批次
       - 特征完全一致
    """)
    
    st.divider()
    
    st.header("⚙️ 处理参数")
    
    with st.expander("高级参数设置", expanded=False):
        halfWindowSize = st.slider("半峰宽", 10, 200, 90, 10)
        SNR = st.slider("信噪比阈值", 1.0, 10.0, 2.0, 0.5)
        tolerance = st.slider("对齐容差", 0.001, 0.02, 0.008, 0.001, format="%.4f")
        iterations = st.slider("基线去除迭代次数", 50, 200, 100, 10)
    
    processing_params = {
        'halfWindowSize': halfWindowSize,
        'SNR': SNR,
        'tolerance': tolerance,
        'iterations': iterations
    }
    
    st.divider()
    
    # 检查R环境
    st.header("🔧 环境检查")
    if check_r_installation():
        st.success("✅ R环境已安装")
    else:
        st.error("❌ 未检测到R环境")

# 主内容区
tab1, tab2 = st.tabs(["🎯 阶段1: 建立训练集模版", "🔄 阶段2: 处理验证集"])

# 阶段1: 建立训练集模版
with tab1:
    st.markdown('<div class="phase-header">📊 阶段1: 建立训练集特征模版</div>', unsafe_allow_html=True)
    
    st.info("💡 处理训练集并建立特征模版（只需做一次！）")
    
    train_zip = st.file_uploader("上传训练集ZIP文件", type=['zip'], key='train_zip')
    
    if train_zip:
        txt_files, excel_file = extract_files_from_zip(train_zip)
        
        if txt_files and excel_file:
            st.success(f"✅ {len(txt_files)}个TXT文件 + 1个Excel文件")
            
            if st.button("🎯 建立训练集模版", type="primary", use_container_width=True):
                
                if not check_r_installation():
                    st.error("❌ R环境未安装，无法处理数据！")
                    st.stop()
                
                # 创建进度条和状态文本
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                temp_dir = tempfile.mkdtemp()
                train_dir = Path(temp_dir) / "train"
                train_dir.mkdir()
                
                try:
                    # 步骤1: 保存文件
                    status_text.text("📁 步骤1/6: 保存上传的文件...")
                    progress_bar.progress(10)
                    
                    txt_files, excel_file = extract_files_from_zip(train_zip)
                    
                    for content, name in txt_files:
                        with open(train_dir / name, 'wb') as f:
                            f.write(content)
                    
                    excel_path = train_dir / excel_file[1]
                    with open(excel_path, 'wb') as f:
                        f.write(excel_file[0])
                    
                    progress_bar.progress(15)
                    
                    # 步骤2: 生成R脚本
                    status_text.text("📝 步骤2/6: 生成处理脚本...")
                    progress_bar.progress(20)
                    
                    params = processing_params
                    
                    r_script = f"""
# 设置用户库路径
user_lib <- Sys.getenv("R_LIBS_USER")
if (user_lib == "") {{
    user_lib <- "~/R/library"
}}
if (!dir.exists(user_lib)) {{
    dir.create(user_lib, recursive = TRUE)
}}
.libPaths(c(user_lib, .libPaths()))

library('MALDIquant')
library('MALDIquantForeign')
library('readxl')

cat("开始处理训练集...\\n")

# 读取训练集
cat("读取Excel和TXT文件...\\n")
samples <- read_excel('{excel_path.as_posix()}')
training_spectra <- importTxt('{train_dir.as_posix()}')
cat(sprintf("导入训练集: %d 个光谱\\n", length(training_spectra)))

# 预处理
cat("执行预处理（1/5）: 强度转换...\\n")
training_spectra <- transformIntensity(training_spectra, method = "sqrt")

cat("执行预处理（2/5）: 平滑处理...\\n")
training_spectra <- smoothIntensity(training_spectra, method = "SavitzkyGolay", 
                                     halfWindowSize = {params['halfWindowSize']})

cat("执行预处理（3/5）: 基线去除...\\n")
training_spectra <- removeBaseline(training_spectra, method = "SNIP", 
                                   iterations = {params['iterations']})

cat("执行预处理（4/5）: 强度校准...\\n")
training_spectra <- calibrateIntensity(training_spectra, method = "TIC")

# 分配标签
cat("执行预处理（5/5）: 分配标签...\\n")
train_labels <- samples$group[match(
  sapply(training_spectra, function(s) basename(s@metaData$file)),
  samples$file
)]

# 计算平均谱
cat("计算平均谱...\\n")
avgSpectra <- averageMassSpectra(training_spectra, labels = train_labels)
cat(sprintf("计算平均谱: %d 个分组\\n", length(avgSpectra)))

# 对齐
cat("对齐平均谱...\\n")
avgSpectra <- alignSpectra(avgSpectra,
                           halfWindowSize = {params['halfWindowSize']},
                           SNR = {params['SNR']},
                           tolerance = {params['tolerance']},
                           warpingMethod = "lowess")

# 检测峰
cat("检测峰，建立特征模版...\\n")
train_peaks <- detectPeaks(avgSpectra,
                           method = "MAD",
                           halfWindowSize = {params['halfWindowSize']},
                           SNR = {params['SNR']})

# Binning
cat("峰分箱处理...\\n")
train_binned <- binPeaks(train_peaks, tolerance = 2)

# 提取特征m/z
cat("提取特征m/z...\\n")
feature_mz <- as.numeric(unique(unlist(lapply(train_binned, function(p) p@mass))))
feature_mz <- sort(feature_mz)

cat(sprintf("训练集特征数: %d 个峰\\n", length(feature_mz)))
cat(sprintf("m/z范围: %.0f - %.0f\\n", min(feature_mz), max(feature_mz)))

# 保存特征模版
cat("保存特征模版...\\n")
feature_template <- data.frame(
  feature_id = paste0("mz_", round(feature_mz)),
  mz = feature_mz
)
write.csv(feature_template, 
          file = '{temp_dir}/feature_template.csv',
          row.names = FALSE)

# 生成训练集强度矩阵
cat("生成训练集强度矩阵...\\n")
train_intensity_matrix <- intensityMatrix(train_binned, avgSpectra)
bin_centers <- as.numeric(colnames(train_intensity_matrix))
bin_centers_integer <- round(bin_centers)
colnames(train_intensity_matrix) <- paste0("mz_", bin_centers_integer)
rownames(train_intensity_matrix) <- unique(train_labels)

train_df <- as.data.frame(train_intensity_matrix)
train_df <- cbind(group = rownames(train_df), train_df)
write.csv(train_df, 
          file = '{temp_dir}/peak_intensity_train.csv',
          row.names = FALSE)

# 保存处理参数
cat("保存处理参数...\\n")
params_df <- data.frame(
  parameter = c('halfWindowSize', 'SNR', 'tolerance', 'iterations'),
  value = c({params['halfWindowSize']}, 
            {params['SNR']}, 
            {params['tolerance']},
            {params['iterations']})
)
write.csv(params_df, '{temp_dir}/processing_params.csv', row.names = FALSE)

cat("训练集处理完成!\\n")
cat(sprintf("  分组数: %d\\n", nrow(train_df)))
cat(sprintf("  特征数: %d\\n", ncol(train_df) - 1))
"""
                    
                    progress_bar.progress(25)
                    
                    # 步骤3: 执行R脚本
                    status_text.text("🔬 步骤3/6: 读取和预处理数据（这可能需要几分钟）...")
                    progress_bar.progress(30)
                    
                    stdout, stderr, returncode = run_r_script(r_script, temp_dir)
                    
                    if returncode == 0:
                        # 步骤4: 读取结果
                        status_text.text("📊 步骤4/6: 读取处理结果...")
                        progress_bar.progress(70)
                        
                        template_df = pd.read_csv(Path(temp_dir) / 'feature_template.csv')
                        train_df = pd.read_csv(Path(temp_dir) / 'peak_intensity_train.csv')
                        params_df = pd.read_csv(Path(temp_dir) / 'processing_params.csv')
                        
                        progress_bar.progress(85)
                        
                        # 步骤5: 保存到session state
                        status_text.text("💾 步骤5/6: 保存结果...")
                        progress_bar.progress(90)
                        
                        st.session_state.template_created = True
                        st.session_state.template_data = template_df
                        st.session_state.processing_params = processing_params
                        st.session_state.train_result = train_df
                        
                        # 步骤6: 完成
                        status_text.text("✅ 步骤6/6: 处理完成！")
                        progress_bar.progress(100)
                        
                        import time
                        time.sleep(0.5)
                        
                        status_text.empty()
                        progress_bar.empty()
                        
                        st.success("✅ 训练集处理完成！特征模版已建立！")
                        
                        # 显示摘要
                        st.subheader("📊 处理摘要")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("训练集分组数", len(train_df))
                        with col2:
                            st.metric("特征数量", len(template_df))
                        with col3:
                            st.metric("m/z范围", f"{template_df['mz'].min():.0f} - {template_df['mz'].max():.0f}")
                        
                        # 显示参数
                        with st.expander("查看处理参数"):
                            st.dataframe(params_df, use_container_width=True)
                        
                        # 显示日志
                        with st.expander("查看处理日志"):
                            st.code(stdout, language='text')
                        
                        # 下载区域
                        st.divider()
                        st.subheader("📥 下载结果")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.download_button(
                                "📊 训练集结果",
                                data=train_df.to_csv(index=False),
                                file_name="peak_intensity_train.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        with col2:
                            st.download_button(
                                "🎯 特征模版",
                                data=template_df.to_csv(index=False),
                                file_name="feature_template.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        with col3:
                            st.download_button(
                                "⚙️ 处理参数",
                                data=params_df.to_csv(index=False),
                                file_name="processing_params.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ 处理失败！\n\n{stderr}")
                        with st.expander("查看详细日志"):
                            st.code(stdout, language='text')
                
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ 发生错误: {str(e)}")
                
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)

# 阶段2: 处理验证集
with tab2:
    st.markdown('<div class="phase-header">🔄 阶段2: 使用模版处理验证集</div>', unsafe_allow_html=True)
    
    if not st.session_state.template_created:
        st.warning("⚠️ 请先完成阶段1！")
    else:
        st.success("✅ 特征模版已就绪！")
        
        valid_zip = st.file_uploader("上传验证集ZIP文件", type=['zip'], key='valid_zip')
        
        if valid_zip:
            if st.button("🔄 处理验证集", type="primary", use_container_width=True):
                
                if not check_r_installation():
                    st.error("❌ R环境未安装，无法处理数据！")
                    st.stop()
                
                # 创建进度条和状态文本
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                temp_dir = tempfile.mkdtemp()
                valid_dir = Path(temp_dir) / "validation"
                valid_dir.mkdir()
                
                try:
                    # 步骤1: 保存验证集文件
                    status_text.text("📁 步骤1/5: 保存验证集文件...")
                    progress_bar.progress(10)
                    
                    txt_files, _ = extract_files_from_zip(valid_zip)
                    
                    for content, name in txt_files:
                        with open(valid_dir / name, 'wb') as f:
                            f.write(content)
                    
                    progress_bar.progress(20)
                    
                    # 步骤2: 保存模版和参数
                    status_text.text("📋 步骤2/5: 准备特征模版...")
                    progress_bar.progress(25)
                    
                    template_path = Path(temp_dir) / 'feature_template.csv'
                    st.session_state.template_data.to_csv(template_path, index=False)
                    
                    params = st.session_state.processing_params
                    
                    progress_bar.progress(30)
                    
                    # 步骤3: 生成R脚本
                    status_text.text("📝 步骤3/5: 生成处理脚本...")
                    
                    r_script = f"""
# 设置用户库路径
user_lib <- Sys.getenv("R_LIBS_USER")
if (user_lib == "") {{
    user_lib <- "~/R/library"
}}
if (!dir.exists(user_lib)) {{
    dir.create(user_lib, recursive = TRUE)
}}
.libPaths(c(user_lib, .libPaths()))

library('MALDIquant')
library('MALDIquantForeign')

cat("使用训练集模版处理验证集...\\n")

# 读取特征模版
template <- read.csv('{template_path.as_posix()}')
template_mz <- template$mz
cat(sprintf("特征模版: %d 个m/z\\n", length(template_mz)))

# 读取验证集
cat("读取验证集TXT文件...\\n")
validation_spectra <- importTxt('{valid_dir.as_posix()}')
cat(sprintf("导入验证集: %d 个光谱\\n", length(validation_spectra)))

# 预处理
cat("执行预处理（1/4）: 强度转换...\\n")
validation_spectra <- transformIntensity(validation_spectra, method = "sqrt")

cat("执行预处理（2/4）: 平滑处理...\\n")
validation_spectra <- smoothIntensity(validation_spectra, method = "SavitzkyGolay",
                                      halfWindowSize = {params['halfWindowSize']})

cat("执行预处理（3/4）: 基线去除...\\n")
validation_spectra <- removeBaseline(validation_spectra, method = "SNIP",
                                     iterations = {params['iterations']})

cat("执行预处理（4/4）: 强度校准...\\n")
validation_spectra <- calibrateIntensity(validation_spectra, method = "TIC")

# 对齐
cat("对齐验证集光谱...\\n")
validation_spectra <- alignSpectra(validation_spectra,
                                   halfWindowSize = {params['halfWindowSize']},
                                   SNR = {params['SNR']},
                                   tolerance = {params['tolerance']},
                                   warpingMethod = "lowess")

# 使用模版提取强度
cat("使用模版提取强度...\\n")
n_samples <- length(validation_spectra)
n_features <- length(template_mz)
intensity_matrix <- matrix(0, nrow = n_samples, ncol = n_features)

for (i in 1:n_samples) {{
  if (i %% 50 == 0) {{
    cat(sprintf("  处理进度: %d/%d\\n", i, n_samples))
  }}
  spec <- validation_spectra[[i]]
  
  for (j in 1:n_features) {{
    target_mz <- template_mz[j]
    
    if (length(spec@mass) > 0) {{
      idx <- which(abs(spec@mass - target_mz) <= 2)
      if (length(idx) > 0) {{
        closest_idx <- idx[which.min(abs(spec@mass[idx] - target_mz))]
        intensity_matrix[i, j] <- spec@intensity[closest_idx]
      }}
    }}
  }}
}}

# 设置列名和行名
colnames(intensity_matrix) <- paste0("mz_", round(template_mz))
sample_names <- sapply(validation_spectra, function(s) basename(s@metaData$file))
rownames(intensity_matrix) <- sample_names

# 保存结果
cat("保存验证集结果...\\n")
valid_df <- as.data.frame(intensity_matrix)
valid_df <- cbind(sample = rownames(valid_df), valid_df)
write.csv(valid_df,
          file = '{temp_dir}/peak_intensity_validation.csv',
          row.names = FALSE)

cat("验证集处理完成!\\n")
cat(sprintf("  样本数: %d\\n", nrow(valid_df)))
cat(sprintf("  特征数: %d (与训练集一致)\\n", ncol(valid_df) - 1))
"""
                    
                    progress_bar.progress(35)
                    
                    # 步骤4: 执行R脚本
                    status_text.text("🔬 步骤4/5: 处理验证集数据（这可能需要几分钟）...")
                    progress_bar.progress(40)
                    
                    stdout, stderr, returncode = run_r_script(r_script, temp_dir)
                    
                    if returncode == 0:
                        # 步骤5: 读取结果
                        status_text.text("📊 步骤5/5: 读取处理结果...")
                        progress_bar.progress(85)
                        
                        valid_df = pd.read_csv(Path(temp_dir) / 'peak_intensity_validation.csv')
                        
                        progress_bar.progress(95)
                        
                        status_text.text("✅ 处理完成！")
                        progress_bar.progress(100)
                        
                        import time
                        time.sleep(0.5)
                        
                        status_text.empty()
                        progress_bar.empty()
                        
                        st.success("✅ 验证集处理完成！")
                        
                        # 显示摘要
                        st.subheader("📊 处理摘要")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("验证集样本数", len(valid_df))
                        with col2:
                            st.metric("特征数量", len(valid_df.columns) - 1)
                        with col3:
                            st.metric("特征一致性", "✅ 与训练集一致")
                        
                        # 显示日志
                        with st.expander("查看处理日志"):
                            st.code(stdout, language='text')
                        
                        # 数据预览
                        with st.expander("数据预览"):
                            st.dataframe(valid_df.head(10), use_container_width=True)
                        
                        # 下载
                        st.divider()
                        st.subheader("📥 下载结果")
                        
                        st.download_button(
                            "📊 下载验证集结果",
                            data=valid_df.to_csv(index=False),
                            file_name="peak_intensity_validation.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ 处理失败！\n\n{stderr}")
                        with st.expander("查看详细日志"):
                            st.code(stdout, language='text')
                
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ 发生错误: {str(e)}")
                
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)

st.divider()
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p><strong>MALDI-TOF MS 模版化处理平台</strong></p>
</div>
""", unsafe_allow_html=True)
