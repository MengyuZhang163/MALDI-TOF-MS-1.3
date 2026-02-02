# 备用安装脚本 - 使用 BiocManager
# 如果 install_r_packages.R 失败，可以尝试这个脚本

# 设置用户库路径
user_lib <- Sys.getenv("R_LIBS_USER")
if (user_lib == "") {
    user_lib <- "~/R/library"
}
if (!dir.exists(user_lib)) {
    dir.create(user_lib, recursive = TRUE)
}
.libPaths(c(user_lib, .libPaths()))

# 设置CRAN镜像
options(repos = c(CRAN = "https://cloud.r-project.org"))

cat("==========================================\n")
cat("使用 BiocManager 安装 R 包\n")
cat("==========================================\n\n")

# 安装 BiocManager
if (!requireNamespace("BiocManager", quietly = TRUE)) {
    cat("安装 BiocManager...\n")
    install.packages("BiocManager", lib = user_lib)
}

# 使用 BiocManager 安装包（更可靠）
packages <- c("MALDIquant", "MALDIquantForeign", "readxl")

for (pkg in packages) {
    cat(sprintf("\n安装 %s...\n", pkg))
    tryCatch({
        BiocManager::install(pkg, lib = user_lib, update = FALSE, ask = FALSE)
        cat(sprintf("✅ %s 安装完成\n", pkg))
    }, error = function(e) {
        cat(sprintf("❌ %s 安装失败: %s\n", pkg, e$message))
    })
}

cat("\n==========================================\n")
cat("验证安装...\n")
cat("==========================================\n\n")

for (pkg in packages) {
    if (require(pkg, character.only = TRUE, quietly = TRUE)) {
        cat(sprintf("✅ %s - 可以正常加载\n", pkg))
    } else {
        cat(sprintf("❌ %s - 加载失败\n", pkg))
    }
}

cat("\n==========================================\n")
cat("安装完成！\n")
cat("==========================================\n")
