# 设置用户库路径
user_lib <- Sys.getenv("R_LIBS_USER")
if (user_lib == "") {
    user_lib <- "~/R/library"
}
if (!dir.exists(user_lib)) {
    dir.create(user_lib, recursive = TRUE)
}
.libPaths(c(user_lib, .libPaths()))

# 设置多个CRAN镜像（提高下载速度和成功率）
options(repos = c(
    CRAN1 = "https://cloud.r-project.org",
    CRAN2 = "https://cran.rstudio.com",
    CRAN3 = "https://mirror.lzu.edu.cn/CRAN/"
))

# 设置并行下载
options(Ncpus = 4)

cat("==========================================\n")
cat("开始安装R包及其依赖...\n")
cat("==========================================\n\n")

# 首先安装基础依赖包
cat("步骤 1/3: 安装基础依赖包...\n")
base_deps <- c("Rcpp", "xml2", "httr", "curl")

for (pkg in base_deps) {
    if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
        cat(sprintf("  安装依赖: %s...\n", pkg))
        tryCatch({
            install.packages(
                pkg, 
                lib = user_lib, 
                dependencies = TRUE,
                quiet = TRUE
            )
            cat(sprintf("  ✅ %s 完成\n", pkg))
        }, error = function(e) {
            cat(sprintf("  ⚠️ %s 安装失败（可能不影响主包）\n", pkg))
        })
    }
}

cat("\n步骤 2/3: 安装 MALDIquant...\n")
# 安装 MALDIquant（核心包，通常没问题）
if (!require("MALDIquant", character.only = TRUE, quietly = TRUE)) {
    cat("  正在安装 MALDIquant...\n")
    tryCatch({
        install.packages(
            "MALDIquant", 
            lib = user_lib, 
            dependencies = TRUE,
            quiet = FALSE
        )
        cat("  ✅ MALDIquant 安装成功\n")
    }, error = function(e) {
        cat(sprintf("  ❌ MALDIquant 安装失败: %s\n", e$message))
        cat("  尝试从源码安装...\n")
        install.packages("MALDIquant", lib = user_lib, type = "source")
    })
} else {
    cat("  ✅ MALDIquant 已安装\n")
}

cat("\n步骤 3/3: 安装 MALDIquantForeign 和 readxl...\n")
# 安装 MALDIquantForeign（容易出问题的包）
if (!require("MALDIquantForeign", character.only = TRUE, quietly = TRUE)) {
    cat("  正在安装 MALDIquantForeign...\n")
    tryCatch({
        install.packages(
            "MALDIquantForeign", 
            lib = user_lib, 
            dependencies = TRUE,
            quiet = FALSE
        )
        cat("  ✅ MALDIquantForeign 安装成功\n")
    }, error = function(e) {
        cat(sprintf("  ❌ 第一次安装失败: %s\n", e$message))
        cat("  尝试方案2: 从源码安装...\n")
        tryCatch({
            install.packages("MALDIquantForeign", lib = user_lib, type = "source")
            cat("  ✅ MALDIquantForeign 源码安装成功\n")
        }, error = function(e2) {
            cat(sprintf("  ❌ 源码安装也失败: %s\n", e2$message))
            cat("  尝试方案3: 手动安装依赖后重试...\n")
            # 手动安装可能缺失的依赖
            deps <- c("readMzXmlData", "XML")
            for (dep in deps) {
                tryCatch({
                    install.packages(dep, lib = user_lib)
                }, error = function(e3) {
                    cat(sprintf("    依赖 %s 安装失败\n", dep))
                })
            }
            # 最后再试一次
            install.packages("MALDIquantForeign", lib = user_lib, dependencies = TRUE)
        })
    })
} else {
    cat("  ✅ MALDIquantForeign 已安装\n")
}

# 安装 readxl
if (!require("readxl", character.only = TRUE, quietly = TRUE)) {
    cat("  正在安装 readxl...\n")
    tryCatch({
        install.packages(
            "readxl", 
            lib = user_lib, 
            dependencies = TRUE,
            quiet = FALSE
        )
        cat("  ✅ readxl 安装成功\n")
    }, error = function(e) {
        cat(sprintf("  ❌ readxl 安装失败: %s\n", e$message))
    })
} else {
    cat("  ✅ readxl 已安装\n")
}

cat("\n==========================================\n")
cat("验证安装结果...\n")
cat("==========================================\n\n")

# 验证所有包
packages <- c("MALDIquant", "MALDIquantForeign", "readxl")
all_success <- TRUE

for (pkg in packages) {
    if (require(pkg, character.only = TRUE, quietly = TRUE)) {
        cat(sprintf("✅ %s - 可以正常加载\n", pkg))
    } else {
        cat(sprintf("❌ %s - 加载失败！\n", pkg))
        all_success <- FALSE
    }
}

cat("\n==========================================\n")
if (all_success) {
    cat("🎉 所有R包安装并验证成功！\n")
} else {
    cat("⚠️ 部分包安装失败，请检查上述错误信息\n")
}
cat("==========================================\n")


