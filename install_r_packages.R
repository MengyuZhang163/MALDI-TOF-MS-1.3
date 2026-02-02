# 设置用户库路径
user_lib <- Sys.getenv("R_LIBS_USER")
if (user_lib == "") {
    user_lib <- "~/R/library"
}
if (!dir.exists(user_lib)) {
    dir.create(user_lib, recursive = TRUE)
}
.libPaths(c(user_lib, .libPaths()))

# 设置CRAN镜像（使用最快的镜像）
options(repos = c(CRAN = "https://cloud.r-project.org"))

# 设置并行下载，加快速度
options(Ncpus = 4)

cat("==========================================\n")
cat("开始安装R包...\n")
cat(sprintf("时间: %s\n", Sys.time()))
cat("==========================================\n\n")

# 定义要安装的包
packages <- c("MALDIquant", "MALDIquantForeign", "readxl")

# 逐个安装
for (i in seq_along(packages)) {
    pkg <- packages[i]
    cat(sprintf("\n[%d/%d] 处理 %s...\n", i, length(packages), pkg))
    
    # 检查是否已安装
    if (require(pkg, character.only = TRUE, quietly = TRUE)) {
        cat(sprintf("✅ %s 已安装，跳过\n", pkg))
        next
    }
    
    # 安装包
    cat(sprintf("⏳ 正在安装 %s...\n", pkg))
    cat("   这可能需要几分钟，请耐心等待...\n")
    
    tryCatch({
        install.packages(
            pkg, 
            lib = user_lib, 
            dependencies = TRUE,
            quiet = FALSE
        )
        
        # 验证安装
        if (require(pkg, character.only = TRUE, quietly = TRUE)) {
            cat(sprintf("✅ %s 安装并验证成功\n", pkg))
        } else {
            cat(sprintf("⚠️ %s 安装完成但无法加载\n", pkg))
        }
    }, error = function(e) {
        cat(sprintf("❌ %s 安装失败: %s\n", pkg, e$message))
        
        # 尝试源码安装
        cat("   尝试从源码安装...\n")
        tryCatch({
            install.packages(pkg, lib = user_lib, type = "source")
            cat(sprintf("✅ %s 源码安装成功\n", pkg))
        }, error = function(e2) {
            cat(sprintf("❌ 源码安装也失败: %s\n", e2$message))
        })
    })
}

cat("\n==========================================\n")
cat("验证安装结果...\n")
cat("==========================================\n\n")

# 最终验证
all_success <- TRUE
for (pkg in packages) {
    if (require(pkg, character.only = TRUE, quietly = TRUE)) {
        cat(sprintf("✅ %s - OK\n", pkg))
    } else {
        cat(sprintf("❌ %s - 失败\n", pkg))
        all_success <- FALSE
    }
}

cat("\n==========================================\n")
if (all_success) {
    cat("🎉 所有R包安装成功！\n")
} else {
    cat("⚠️ 部分包安装失败\n")
}
cat(sprintf("完成时间: %s\n", Sys.time()))
cat("==========================================\n")
