# FOC Reference — 中英双语学习参考版

[English](README.md) | [简体中文](README.zh-CN.md)

> [!IMPORTANT]
> **版权与来源声明（Copyright & Attribution）**
>
> 本网站的所有原始正文、数学推导、交互式仿真图表及视觉设计版权均归原网站 **[focreference.com](https://focreference.com/)** 原作者所有。
>
> 本仓库仅作为原网站的**非官方中英双语翻译与静态重建版本，纯粹用于个人电机控制技术学习、教学研究与非商业交流**，并非原作者的官方源码仓库。若原版权所有者认为本仓库存在任何不当之处，请提交 Issue 联系修改或移除。

---

## 项目简介

[FOC Reference](https://focreference.com/) 是一份关于永磁同步电机（PMSM）**磁场定向控制（Field-Oriented Control, FOC）**的交互式技术参考手册——内容从旋转空间矢量与 Clarke/Park 坐标变换出发，一路延伸至电流环/转速环整定、无位置传感器观测器，以及可直接用于量产的中断服务程序（ISR）软件架构。

本项目基于原站公开页面构建了完整的 **29 页中英双语对照静态网站**，并支持一键切换中英文：
- **6 大核心章节（共 24 页）**：
  1. **基础（Foundations）**：空间矢量、三相瞬时功率与 3/2 系数、Clarke 与 Park 变换、标幺化与定点数 Q 格式缩放
  2. **电机（The Machine）**：PMSM 的 $dq$ 电压与磁链模型、电机四参数台架实测与单位陷阱、电磁转矩与 MTPA、弱磁控制包络线
  3. **逆变器（The Inverter）**：三相全桥与导通/开关损耗、六步换相、空间矢量调制（SVPWM）与最小-最大零序注入、死区效应与补偿
  4. **传感与测量（Sensing）**：分流电阻采样窗口、ADC 量化噪声在 $dq$ 坐标系下的分布、直流母线纹波与制动能量、位置传感器与 $d$ 轴零位偏移
  5. **控制与估算（Control & Estimation）**：基于电机参数的电流环零极点对消整定与抗积分饱和、级联速度/位置环、离散采样与混叠、无位置传感器估算（磁链观测器与滑模观测器 SMO）
  6. **工程实现（Implementation）**：控制链路时序与相位裕度预算、MCU 关键外设与影子寄存器规则、向内依赖的三层软件架构、驱动器分步安全上电调试
- **首页、搜索页与 3 篇速查参考页**：
  - 交互式闭环首页（`index.html`）、中英全文搜索（`search.html`）、故障排查 32 例（`failures.html`）、公式速查表（`formulas.html`）以及全局符号约定（`notation.html`）。

### 翻译与人工校对说明

- 全站 29 个中文页面（`src/docs/zh/*.html`）以及全部章节中的 SVG 信号流图/架构框图均已对照英文原版（`src/docs/en/*.html`）完成逐段专业审校，统一了电机控制与电力电子领域术语。
- 100% 原样保留了所有 KaTeX 数学公式、C/TypeScript 代码块及交互式 Canvas 仿真控件。
- 点击任意页面右上角导航栏中的 **English / 中文** 按钮即可在同一章节路径下无缝切换中英文。

---

## 本地运行与构建

需要安装 **Node.js 20+**。

```bash
# 安装依赖
npm install

# 启动本地开发服务器
npm run dev
```

启动后在浏览器访问 `http://localhost:4321/zh/`（或英文版 `http://localhost:4321/en/`）。

### 构建静态网站与搜索索引

```bash
npm run build
npm run preview
```

`npm run build` 会调用 `astro build` 生成静态文件至 `dist/`，随后运行 **Pagefind** 生成中英双语全文检索索引，并自动同步至 `public/pagefind/`。

---

## 部署至 GitHub Pages

本仓库已内置 GitHub Actions 自动部署工作流（`.github/workflows/deploy.yml`），会自动识别仓库的 `SITE_URL` 与二级路径 `BASE_PATH`，无论部署在根域名还是 `https://<用户名>.github.io/<仓库名>/` 二级目录下均可正常加载所有资源与搜索索引：

1. 将本仓库推送至 GitHub（`main` 分支）。
2. 进入 GitHub 仓库的 **Settings → Pages**。
3. 在 **Build and deployment → Source** 下拉框中选择 **GitHub Actions**。
4. 需要发布或更新站点时，进入仓库的 **Actions** 标签页，选择左侧的 **Deploy to GitHub Pages**，点击右上角的 **Run workflow** 手动触发构建与部署。

---

## 目录结构

- `src/docs/en/` — 原版英文 HTML 页面（共 29 页）。
- `src/docs/zh/` — 校对后的简体中文 HTML 页面（共 29 页）。
- `src/docs/pages.json` — 全站页面路由清单。
- `src/pages/[...route].astro` — 双语路由生成、语言切换按钮注入与 `BASE_URL` 路径重写。
- `src/pages/index.astro` — 根路径入口（默认跳转至 `/zh/`）。
- `public/_astro/` — 原站编译后的交互式 Canvas 仿真脚本、样式表及 KaTeX 字体资源。
- `public/i18n.css` — 中文排版优化与语言切换按钮样式。
