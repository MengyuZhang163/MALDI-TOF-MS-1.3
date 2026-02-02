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

# 安装必需的R包
cat("开始安装R包...\n")

packages <- c("MALDIquant", "MALDIquantForeign", "readxl")

for (pkg in packages) {
    if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
        cat(sprintf("正在安装 %s...\n", pkg))
        install.packages(pkg, lib = user_lib, dependencies = TRUE)
        cat(sprintf("✓ %s 安装完成\n", pkg))
    } else {
        cat(sprintf("✓ %s 已安装\n", pkg))
    }
}

cat("\n所有R包安装完成！\n")
