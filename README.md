# 🔬 MALDI-TOF MS 模版化处理平台

基于训练集建立特征模版，批量处理验证集的质谱数据分析工具。

## 功能特点

- ✅ **训练集模版建立**：一次性建立特征模版
- ✅ **验证集批量处理**：使用相同模版处理多批次数据
- ✅ **特征一致性保证**：确保训练集和验证集特征完全一致
- ✅ **可视化进度展示**：实时显示处理进度
- ✅ **参数可调**：支持自定义预处理参数

## 使用方法

### 阶段1：建立训练集模版
1. 准备训练集ZIP文件（包含TXT光谱文件和Excel样本信息）
2. 上传并点击"建立训练集模版"
3. 下载特征模版和处理结果

### 阶段2：处理验证集
1. 上传验证集ZIP文件（包含TXT光谱文件）
2. 系统自动使用训练集模版
3. 下载验证集处理结果

## 数据格式要求

### 训练集ZIP文件应包含：
- 多个 `.txt` 格式的质谱数据文件
- 1个 `.xlsx` 或 `.xls` 格式的样本信息文件
  - 必需列：`file`（文件名）和 `group`（分组）

示例Excel文件：
```
file          | group
------------- | -------
sample1.txt   | A
sample2.txt   | A
sample3.txt   | B
```

### 验证集ZIP文件应包含：
- 多个 `.txt` 格式的质谱数据文件

## 处理参数说明

- **半峰宽 (halfWindowSize)**：峰检测窗口大小，默认90
- **信噪比阈值 (SNR)**：峰检测信噪比，默认2.0
- **对齐容差 (tolerance)**：光谱对齐容差，默认0.008
- **基线去除迭代次数 (iterations)**：SNIP算法迭代次数，默认100

## 技术栈

- **前端**：Streamlit
- **数据处理**：Python (Pandas) + R (MALDIquant)
- **核心算法**：
  - 强度转换（平方根）
  - Savitzky-Golay 平滑
  - SNIP 基线去除
  - TIC 强度校准
  - Lowess 光谱对齐

## 部署说明

### 本地运行
```bash
# 安装依赖
pip install -r requirements.txt

# 确保安装了R和必需的R包
Rscript install_r_packages.R

# 运行应用
streamlit run app.py
```

### Streamlit Cloud部署
1. 将所有文件上传到GitHub仓库
2. 登录 [Streamlit Cloud](https://streamlit.io/cloud)
3. 选择仓库并部署

## 注意事项

⚠️ **首次部署**：需要5-10分钟安装R环境和R包

⚠️ **资源限制**：
- Streamlit Cloud 免费版内存限制：1GB
- 建议单次处理样本数 < 500

⚠️ **文件大小**：单个ZIP文件建议 < 200MB

## 常见问题

**Q: R包安装失败怎么办？**
A: 检查 `install_r_packages.R` 文件是否存在，并查看安装日志。

**Q: 处理超时怎么办？**
A: 减少样本数量或调整处理参数。

**Q: 特征数量不一致？**
A: 确保使用相同的训练集模版处理验证集。

## 作者

MALDI-TOF MS 分析平台

## 许可

MIT License
