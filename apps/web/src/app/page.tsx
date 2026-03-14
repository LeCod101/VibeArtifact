/**
 * 公开首页 - Claude 暖色风格 + 合成引擎交互展示
 *
 * 暖米色背景，居中品牌标语 + CTA，下方合成引擎三步骤动态展示。
 */
"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Github,
  Languages,
  Activity,
  Globe,
  Database,
  Workflow,
  FileText,
  CheckCircle2,
  BoxSelect,
  Settings,
  TerminalSquare,
} from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 页面文案 */
const copy = {
  tagline: {
    zh: "AI Product Engineering OS",
    en: "AI Product Engineering OS",
  },
  subtitle: {
    zh: "用一句话，自动生成全栈系统",
    en: "Generate full-stack systems from a single sentence",
  },
  ctaPrimary: {
    zh: "开始使用",
    en: "Get Started",
  },
  ctaGithub: {
    zh: "GitHub",
    en: "GitHub",
  },
  hasAccount: {
    zh: "已有账号？",
    en: "Already have an account?",
  },
  login: {
    zh: "登录",
    en: "Sign In",
  },
};

export default function HomePage() {
  const { locale, toggleLocale } = useLocale();
  const [activeTab, setActiveTab] = useState(0);
  const footerSections = [
    {
      title: L(t.footer.ecosystem, locale),
      items: L(t.footer.ecosystemItems, locale) as readonly string[],
    },
    {
      title: L(t.footer.developers, locale),
      items: L(t.footer.developerItems, locale) as readonly string[],
    },
  ] as const;

  /** 自动轮播 Tab，每 5 秒切换 */
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveTab((prev) => (prev + 1) % 3);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const tabLabels: readonly string[] = L(t.interactive.tabs, locale);

  return (
    <div className="min-h-screen bg-background">
      {/* 语言切换 */}
      <div className="fixed top-6 right-6 z-30">
        <button
          onClick={toggleLocale}
          className="flex items-center gap-2 h-9 px-4 rounded-full border border-border bg-card text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <Languages size={14} />
          {locale === "zh" ? "EN" : "中文"}
        </button>
      </div>

      {/* ===== Hero 区域 ===== */}
      <section className="flex flex-col items-center justify-center text-center px-6 pt-32 pb-20 md:pt-40 md:pb-28">
        <div className="flex flex-col items-center max-w-2xl animate-reveal">
          {/* Logo 图标 */}
          <svg viewBox="60 30 180 110" className="h-16 w-16 text-foreground mb-8">
            <g fill="currentColor">
              <polygon points="85,40 119,108 109,128 65,40" />
              <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
              <polygon points="150.5,105 199.5,105 207,120 143,120" />
            </g>
          </svg>

          {/* 品牌标语 */}
          <h1 className="font-serif-display text-4xl md:text-5xl lg:text-6xl font-medium text-foreground mb-4 leading-tight">
            {L(copy.tagline, locale)}
          </h1>

          {/* 副标语 */}
          <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-md">
            {L(copy.subtitle, locale)}
          </p>

          {/* CTA 按钮组 */}
          <div className="flex items-center gap-4 mb-8">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 h-12 px-8 rounded-full bg-primary text-primary-foreground font-medium text-sm hover:opacity-90 transition-opacity"
            >
              {L(copy.ctaPrimary, locale)}
              <ArrowRight size={16} />
            </Link>
            <a
              href="https://github.com/LeCod101/vibeartifact"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 h-12 px-6 rounded-full border border-border bg-card text-foreground font-medium text-sm hover:bg-accent transition-colors"
            >
              <Github size={16} />
              {L(copy.ctaGithub, locale)}
            </a>
          </div>

          {/* 登录链接 */}
          <p className="text-sm text-muted-foreground">
            {L(copy.hasAccount, locale)}{" "}
            <Link
              href="/login"
              className="text-foreground font-medium hover:underline underline-offset-4"
            >
              {L(copy.login, locale)}
            </Link>
          </p>
        </div>
      </section>

      {/* ===== 合成引擎交互展示 ===== */}
      <section className="px-6 pb-24 md:pb-32">
        <div className="max-w-[1100px] mx-auto">
          {/* 卡片容器 */}
          <div className="relative group rounded-3xl border border-border overflow-hidden shadow-sm">
            {/* 扫描线 */}
            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-border to-transparent animate-scan z-20 opacity-60" />

            <div className="relative bg-secondary rounded-[calc(1.5rem-1px)] overflow-hidden">
              <div className="grid lg:grid-cols-12 min-h-[580px]">
                {/* ===== 左侧面板 ===== */}
                <div className="lg:col-span-4 border-r border-border p-8 lg:p-10 flex flex-col justify-between bg-card">
                  <div className="space-y-12">
                    {/* 标题 */}
                    <div className="space-y-2">
                      <h3 className="text-foreground text-xl font-bold tracking-tight flex items-center gap-3 font-heading">
                        <Activity className="text-foreground/70 animate-pulse" size={20} />
                        {L(t.interactive.engineTitle, locale)}
                      </h3>
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground ml-8">
                        {L(t.interactive.engineSub, locale)}
                      </p>
                    </div>

                    {/* 步骤 Tab */}
                    <div className="space-y-3 relative before:absolute before:inset-y-3 before:left-[11px] before:w-px before:bg-border before:-z-10">
                      {tabLabels.map((tab, i) => (
                        <button
                          key={tab}
                          onClick={() => setActiveTab(i)}
                          className={`w-full text-left group/btn relative pl-9 py-4 rounded-xl transition-all duration-500 ${
                            activeTab === i
                              ? "bg-secondary border border-border shadow-sm"
                              : "hover:bg-secondary/50"
                          }`}
                        >
                          <div
                            className={`text-xs font-bold uppercase tracking-[0.15em] transition-all duration-500 ${
                              activeTab === i
                                ? "text-foreground translate-x-1"
                                : "text-muted-foreground group-hover/btn:text-foreground/70"
                            }`}
                          >
                            <span className="text-[10px] text-muted-foreground mr-2">
                              STEP 0{i + 1}
                            </span>
                            {tab}
                          </div>
                          {/* 时间线节点圆点 */}
                          <div
                            className={`absolute left-[5px] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full transition-all duration-500 ring-4 ring-card ${
                              activeTab === i
                                ? "bg-foreground shadow-md scale-125"
                                : "bg-border"
                            }`}
                          />
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 状态监控条 */}
                  <div className="p-5 rounded-2xl bg-secondary border border-border">
                    <div className="flex justify-between items-center mb-3">
                      <div className="text-[10px] font-bold text-foreground uppercase tracking-widest flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-foreground rounded-full animate-pulse" />
                        {L(t.interactive.statusLabel, locale)}
                      </div>
                      <div className="text-[10px] font-mono text-muted-foreground">98%</div>
                    </div>
                    <div className="w-full h-1.5 bg-border/50 rounded-full overflow-hidden">
                      <div className="w-[98%] h-full bg-gradient-to-r from-muted-foreground via-foreground to-muted-foreground animate-gradient-x rounded-full" />
                    </div>
                  </div>
                </div>

                {/* ===== 右侧面板 ===== */}
                <div className="lg:col-span-8 p-8 lg:p-10 relative flex flex-col justify-center overflow-hidden bg-card">
                  {/* 网格背景 */}
                  <div className="absolute inset-0 bg-[linear-gradient(var(--border)_1px,transparent_1px),linear-gradient(90deg,var(--border)_1px,transparent_1px)] bg-[size:40px_40px] opacity-30 pointer-events-none" />

                  <div className="font-mono text-[13px] leading-relaxed relative z-10">
                    {/* Step 01 - 解码意图 */}
                    {activeTab === 0 && (
                      <div className="space-y-8 animate-reveal">
                        <div className="flex items-center gap-4">
                          <span className="px-3 py-1.5 bg-foreground text-primary-foreground text-[10px] font-bold rounded uppercase">
                            Step 01
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest text-foreground flex items-center gap-2">
                            {L(t.interactive.step01Label, locale)}
                            <span className="flex gap-1">
                              <span className="w-1 h-1 bg-foreground rounded-full animate-bounce" />
                              <span className="w-1 h-1 bg-foreground rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                              <span className="w-1 h-1 bg-foreground rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                            </span>
                          </span>
                        </div>

                        {/* 输入文字展示 */}
                        <div className="text-foreground text-2xl lg:text-3xl font-bold tracking-tight leading-snug">
                          <span className="relative">
                            <span className="text-muted-foreground">&gt;</span>{" "}
                            {locale === "zh" ? (
                              <>
                                构建一个支持{" "}
                                <span className="text-foreground/80 border-b border-foreground/30 px-0.5">
                                  Stripe
                                </span>{" "}
                                支付、
                                <span className="text-muted-foreground italic">RBAC</span>{" "}
                                权限和实时库存推送的跨境电商平台。
                              </>
                            ) : (
                              <>
                                Build a cross-border e-commerce platform with{" "}
                                <span className="text-foreground/80 border-b border-foreground/30 px-0.5">
                                  Stripe
                                </span>{" "}
                                payments,{" "}
                                <span className="text-muted-foreground italic">RBAC</span>{" "}
                                permissions, and real-time inventory push.
                              </>
                            )}
                            <span className="absolute -right-4 top-1 w-[3px] h-7 bg-foreground animate-blink" />
                          </span>
                        </div>

                        {/* 识别卡片 */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-6">
                          <div className="p-5 bg-secondary hover:bg-accent rounded-2xl border border-border transition-all hover:-translate-y-0.5 hover:shadow-md group">
                            <BoxSelect className="text-foreground/60 mb-3 group-hover:scale-110 transition-transform" size={18} />
                            <div className="text-foreground text-[11px] font-bold uppercase mb-2">
                              {L(t.interactive.identifyEntities, locale)}
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              <span className="px-2 py-1 bg-card border border-border rounded text-muted-foreground text-[10px]">
                                Product_SKU
                              </span>
                              <span className="px-2 py-1 bg-card border border-border rounded text-muted-foreground text-[10px]">
                                Vendor_Auth
                              </span>
                            </div>
                          </div>
                          <div className="p-5 bg-secondary hover:bg-accent rounded-2xl border border-border transition-all hover:-translate-y-0.5 hover:shadow-md group">
                            <Settings className="text-muted-foreground mb-3 animate-spin-slow group-hover:text-foreground/60" size={18} />
                            <div className="text-foreground text-[11px] font-bold uppercase mb-2">
                              {L(t.interactive.identifyServices, locale)}
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              <span className="px-2 py-1 bg-card border border-border rounded text-foreground text-[10px]">
                                Stripe_Webhooks
                              </span>
                              <span className="px-2 py-1 bg-card border border-border rounded text-muted-foreground text-[10px]">
                                Redis_Stream
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Step 02 - 架构推演 */}
                    {activeTab === 1 && (
                      <div className="space-y-8 animate-reveal">
                        <div className="flex items-center gap-4">
                          <span className="px-3 py-1.5 bg-foreground text-primary-foreground text-[10px] font-bold rounded uppercase">
                            Step 02
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest text-foreground flex items-center gap-2">
                            {L(t.interactive.step02Label, locale)}
                            <span className="w-4 h-4 rounded-full border-t-2 border-foreground animate-spin" />
                          </span>
                        </div>

                        <div className="grid grid-cols-1 gap-5">
                          {/* 架构图谱 */}
                          <div className="p-5 border border-border rounded-2xl bg-secondary relative overflow-hidden">
                            <div className="font-bold mb-5 flex items-center gap-3 text-foreground text-[11px] uppercase tracking-widest relative z-10">
                              <Workflow size={16} className="text-foreground/60" />
                              {L(t.interactive.archDiagram, locale)}
                            </div>
                            <div className="h-28 flex items-center justify-between px-6 relative z-10">
                              <div className="w-11 h-11 rounded-xl bg-card border border-border flex items-center justify-center shadow-sm z-10">
                                <Globe size={18} className="text-foreground" />
                              </div>
                              <div className="flex-1 h-[2px] bg-border relative mx-4">
                                <div className="absolute top-1/2 left-0 w-8 h-[2px] bg-foreground -translate-y-1/2 animate-move-x" />
                                <div className="absolute top-1/2 left-1/4 w-3 h-3 bg-[#00c853] rounded-full -translate-y-1/2 shadow-[0_0_8px_rgba(0,200,83,0.3)]" />
                                <div className="absolute top-1/2 left-3/4 w-3 h-3 bg-foreground rounded-full -translate-y-1/2" />
                              </div>
                              <div className="w-11 h-11 rounded-xl bg-card border border-border flex items-center justify-center shadow-sm z-10">
                                <Database size={18} className="text-muted-foreground" />
                              </div>
                            </div>
                          </div>

                          {/* ERM */}
                          <div className="p-5 border border-border rounded-2xl bg-secondary flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <Database size={16} className="text-muted-foreground" />
                              <div>
                                <div className="text-foreground text-[11px] font-bold uppercase tracking-widest mb-1">
                                  {L(t.interactive.ermTitle, locale)}
                                </div>
                                <div className="text-muted-foreground text-[10px]">
                                  {L(t.interactive.ermDesc, locale)}
                                </div>
                              </div>
                            </div>
                            <div className="w-28 space-y-2">
                              <div className="h-1.5 w-full bg-border/50 rounded-full relative overflow-hidden">
                                <div className="absolute inset-0 bg-foreground/50 animate-shimmer" />
                              </div>
                              <div className="h-1.5 w-[70%] bg-border/50 rounded-full relative overflow-hidden">
                                <div className="absolute inset-0 bg-muted-foreground animate-shimmer" style={{ animationDelay: "0.4s" }} />
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Step 03 - 系统构建交付 */}
                    {activeTab === 2 && (
                      <div className="space-y-6 animate-reveal">
                        <div className="flex items-center gap-4">
                          <span className="px-3 py-1.5 bg-[#00c853] text-white text-[10px] font-bold rounded uppercase">
                            Step 03
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest text-foreground flex items-center gap-2">
                            {L(t.interactive.step03Label, locale)}
                            <CheckCircle2 size={14} className="text-[#00c853]" />
                          </span>
                        </div>

                        {/* 文件列表 */}
                        <div className="space-y-3">
                          {[
                            {
                              name: "server/api/v1/stripe_adapter.go",
                              status: "COMPILED",
                              isGreen: false,
                            },
                            {
                              name: "client/components/Dashboard.tsx",
                              status: "COMPILED",
                              isGreen: false,
                            },
                            {
                              name: "infra/terraform/main.tf",
                              status: "DEPLOYED",
                              isGreen: true,
                            },
                          ].map((file) => (
                            <div
                              key={file.name}
                              className={`flex justify-between items-center px-5 py-3.5 border bg-card hover:bg-secondary transition-all rounded-xl cursor-default group/file hover:shadow-sm ${
                                file.isGreen ? "border-[#00c853]/30" : "border-border"
                              }`}
                            >
                              <div className="flex items-center gap-3">
                                <FileText
                                  size={14}
                                  className="text-muted-foreground group-hover/file:text-foreground transition-colors"
                                />
                                <span className="text-[12px] text-muted-foreground group-hover/file:text-foreground transition-colors">
                                  {file.name}
                                </span>
                              </div>
                              <div className="flex items-center gap-3">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest ${
                                    file.isGreen
                                      ? "bg-secondary text-[#00c853]"
                                      : "bg-secondary text-foreground"
                                  }`}
                                >
                                  {file.status}
                                </span>
                                <CheckCircle2 size={14} className="text-[#00c853]" />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 终端状态条 */}
                  <div className="mt-6 self-end px-4 py-2 bg-foreground border border-foreground rounded-lg shadow-lg flex items-center gap-4 cursor-pointer hover:shadow-xl transition-all z-10 w-full max-w-sm relative overflow-hidden">
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#00c853] animate-pulse" />
                    <div className="flex items-center gap-3 text-[10px] font-bold text-primary-foreground/70 uppercase tracking-widest pl-2">
                      <TerminalSquare size={14} className="text-primary-foreground/80" />
                      /var/log/va_engine.log
                    </div>
                    <div className="mx-auto flex-1 w-px h-3 bg-primary-foreground/20" />
                    <div className="text-[10px] font-bold text-primary-foreground/80 animate-pulse flex items-center gap-1">
                      Running
                      <span className="w-2 h-2 rounded-full bg-[#00c853] inline-block" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-border/80 bg-background">
        <div className="mx-auto max-w-[1180px] px-6 py-16 md:py-20">
          <div className="grid gap-14 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.6fr)_minmax(0,0.6fr)]">
            <div className="space-y-6">
              <div className="inline-flex flex-col items-start gap-3">
                <svg viewBox="60 30 180 110" className="h-14 w-14 text-foreground">
                  <g fill="currentColor">
                    <polygon points="85,40 119,108 109,128 65,40" />
                    <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
                    <polygon points="150.5,105 199.5,105 207,120 143,120" />
                  </g>
                </svg>
                <p className="text-base font-semibold tracking-tight text-foreground">
                  VibeArtifact
                </p>
              </div>

              <p className="max-w-md text-sm leading-7 text-muted-foreground md:text-[15px]">
                {L(t.footer.desc, locale)}
              </p>
            </div>

            {footerSections.map((section) => (
              <div key={section.title} className="space-y-5">
                <h3 className="text-sm font-semibold tracking-tight text-foreground md:text-base">
                  {section.title}
                </h3>
                <ul className="space-y-3">
                  {section.items.map((item, index) => (
                    <li
                      key={item}
                      className="flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground md:text-[15px]"
                    >
                      <span>{item}</span>
                      {section.title === L(t.footer.developers, locale) && index === 1 ? (
                        <span className="inline-flex h-1.5 w-1.5 rounded-full bg-foreground" />
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-14 flex flex-col gap-6 border-t border-border/80 pt-8 md:mt-16 md:flex-row md:items-center md:justify-between">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-muted-foreground">
              (c) 2026 VibeArtifact Inc. All Rights Reserved.
            </p>

            <div className="flex items-center gap-3">
              <a
                href="https://github.com/LeCod101/VibeArtifact"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="VibeArtifact GitHub"
                className="inline-flex h-12 w-12 items-center justify-center rounded-full border border-border bg-background/70 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                <Github size={18} />
              </a>
              <a
                href="https://github.com/LeCod101/VibeArtifact/blob/main/README.md"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="VibeArtifact documentation"
                className="inline-flex h-12 w-12 items-center justify-center rounded-full border border-border bg-background/70 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                <Globe size={18} />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
