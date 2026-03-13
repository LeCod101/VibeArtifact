"use client";

/**
 * 首页 - VibeArtifact 营销落地页
 * 配色方案：Apple Pure White — 苹果官网风格浅色极简
 * 页面主背景：#FFFFFF（纯白）
 * 卡片背景：#F5F5F7（Apple 经典浅灰）
 * 卡片 hover：#EBEBED（稍深浅灰）
 * 标题色：#1D1D1F（Apple 标题黑）
 * 正文色：#6E6E73（Apple 正文灰）
 * 副标题色：#86868B（Apple 次要灰）
 * 边框色：#D2D2D7（Apple 浅灰线）
 * 强调按钮：黑底白字（Apple 风格）
 * 无 glow，靠 box-shadow + 间距做层次
 */

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Github,
  CheckCircle2,
  Globe,
  Command,
  Workflow,
  Activity,
  Zap,
  Database,
  FileText,
  Sparkles,
  Settings,
  TerminalSquare,
  BoxSelect,
  Waves,
  Fingerprint,
  ChevronRight,
  Languages,
} from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";

/**
 * 多语言取值辅助函数
 * 根据当前 locale 从双语对象中取出对应值
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/**
 * Capabilities 卡片元数据
 * numericValue: 计数器动画的目标数值（null 表示不走计数器，直接淡入）
 * decimals: 小数位数
 * displayText: 无数值项的静态展示文字
 * 标题、描述、后缀均从 i18n 翻译系统获取
 */
const capabilityMeta = [
  { numericValue: 12, decimals: 0 },
  { numericValue: 99.9, decimals: 1 },
  { numericValue: 3, decimals: 0 },
  { numericValue: 100, decimals: 0 },
  { numericValue: 5, decimals: 0 },
  {
    // 无穷符号，不走计数器，直接淡入
    numericValue: null,
    decimals: 0,
    displayText: "\u221E",
  },
];

/**
 * Logo SVG 组件
 */
function LogoSvg(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 300 250" {...props}>
      <g fill="currentColor">
        <polygon points="85,40 119,108 109,128 65,40" />
        <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
        <polygon points="150.5,105 199.5,105 207,120 143,120" />
      </g>
      <text
        x="150"
        y="215"
        fontFamily="'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"
        fontSize="32"
        fontWeight="600"
        letterSpacing="-0.02em"
        textAnchor="middle"
        fill="currentColor"
      >
        VibeArtifact
      </text>
    </svg>
  );
}

/**
 * 数字计数器动画 Hook
 * 从 0 动画到目标值，使用 easeOutExpo 缓动
 * @param target 目标数值
 * @param duration 动画时长（毫秒）
 * @param decimals 小数位数
 * @param shouldAnimate 是否开始动画
 */
function useCountUp(
  target: number,
  duration: number,
  decimals: number,
  shouldAnimate: boolean
) {
  const [value, setValue] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!shouldAnimate || target === 0) return;

    let startTime: number | null = null;
    let rafId: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // easeOutExpo 缓动函数：快速到达后缓慢趋近
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const current = eased * target;

      setValue(current);

      if (progress < 1) {
        rafId = requestAnimationFrame(animate);
      } else {
        setValue(target);
        setDone(true);
      }
    };

    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
  }, [shouldAnimate, target, duration, decimals]);

  return { value, done };
}

/**
 * 单个 Capability 卡片中的统计数字组件
 * 带有滚动触发的计数器动画和完成后的弹跳效果
 * 对于无穷等无数值的项，使用淡入 + 缩放动画
 * @param meta 卡片元数据（数值、小数位数）
 * @param suffix 数值后缀（来自 i18n 翻译）
 * @param isVisible 是否进入视口
 */
function AnimatedStat({
  meta,
  suffix,
  isVisible,
}: {
  meta: (typeof capabilityMeta)[number];
  suffix: string;
  isVisible: boolean;
}) {
  const { numericValue, decimals } = meta;
  const displayText =
    "displayText" in meta ? (meta as { displayText: string }).displayText : "";

  // 无数值项（如无穷），直接淡入显示
  if (numericValue === null) {
    return (
      <span
        className={`inline-block transition-all duration-700 ${
          isVisible
            ? "animate-fade-in-scale"
            : "opacity-0 scale-75"
        }`}
      >
        {displayText}
      </span>
    );
  }

  // 有数值项，走计数器动画
  const { value, done } = useCountUp(numericValue, 1800, decimals, isVisible);

  return (
    <span
      className={`inline-block transition-transform duration-300 ${
        done ? "animate-stat-bounce" : ""
      }`}
    >
      {value.toFixed(decimals)}
      {suffix}
    </span>
  );
}

export default function Home() {
  const { locale, toggleLocale } = useLocale();
  const [scrolled, setScrolled] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [visibleSections, setVisibleSections] = useState<Record<string, boolean>>({});

  // Capabilities 区块可见性检测（用于触发卡片入场和计数器动画）
  const [capabilitiesVisible, setCapabilitiesVisible] = useState(false);
  const capabilitiesRef = useRef<HTMLDivElement>(null);

  // 时间线滚动驱动状态：记录线条亮灯进度（0-1）和每张卡片是否被激活
  const [timelineProgress, setTimelineProgress] = useState(0);
  const [litNodes, setLitNodes] = useState<boolean[]>(new Array(6).fill(false));
  // 每张卡片的 ref，用于计算节点位置
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
      const sections = ["hero", "interactive", "capabilities", "cta"];
      const currentVisible: Record<string, boolean> = {};
      sections.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          currentVisible[id] = rect.top < window.innerHeight * 0.85;
        }
      });
      setVisibleSections(currentVisible);
    };

    window.addEventListener("scroll", handleScroll);
    handleScroll();

    const interval = setInterval(() => {
      setActiveTab((prev) => (prev + 1) % 3);
    }, 5000);

    return () => {
      window.removeEventListener("scroll", handleScroll);
      clearInterval(interval);
    };
  }, []);

  /**
   * IntersectionObserver 检测 Capabilities 区块进入视口
   * 用于触发卡片入场动画和数字计数器动画
   */
  useEffect(() => {
    const el = capabilitiesRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setCapabilitiesVisible(true);
          // 只触发一次
          observer.disconnect();
        }
      },
      { threshold: 0.15 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  /**
   * 时间线滚动驱动效果
   * 监听滚动位置，计算 Capabilities 区块内的进度比例
   * 逐步点亮时间线上的节点，并驱动垂直线的亮灯长度
   */
  useEffect(() => {
    const handleTimelineScroll = () => {
      const container = capabilitiesRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const windowH = window.innerHeight;

      // 区块顶部进入视口到底部离开视口的进度
      const totalTravel = rect.height + windowH;
      const scrolled = windowH - rect.top;
      const progress = Math.max(0, Math.min(1, scrolled / totalTravel));
      setTimelineProgress(progress);

      // 逐个检测卡片是否进入视口并点亮节点
      const newLit = cardRefs.current.map((ref) => {
        if (!ref) return false;
        const cardRect = ref.getBoundingClientRect();
        // 卡片中心线在视口 75% 以上时点亮
        const cardCenter = cardRect.top + cardRect.height / 2;
        return cardCenter < windowH * 0.75;
      });
      setLitNodes(newLit);
    };

    window.addEventListener("scroll", handleTimelineScroll, { passive: true });
    handleTimelineScroll();
    return () => window.removeEventListener("scroll", handleTimelineScroll);
  }, []);

  const tabLabels: readonly string[] = L(t.interactive.tabs, locale);

  return (
    <div className="min-h-screen bg-white text-[#6E6E73] font-sans selection:bg-[#0071E3]/20 overflow-x-hidden antialiased tracking-tight">
      {/* ===== 背景装饰（极淡渐变色块，替代原暗底发光） ===== */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[70%] h-[70%] bg-[#F5F5F7]/60 blur-[180px] rounded-full animate-pulse-slow" />
        <div
          className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-[#E8E8ED]/40 blur-[150px] rounded-full animate-float"
          style={{ animationDelay: "2s" }}
        />
      </div>

      {/* ===== 导航栏（Apple 毛玻璃白底） ===== */}
      <nav
        className={`fixed top-0 w-full z-[100] transition-all duration-700 ${scrolled
          ? "py-4 bg-white/80 backdrop-blur-2xl border-b border-[#D2D2D7] shadow-[0_1px_3px_rgba(0,0,0,0.08)]"
          : "py-8 bg-transparent"
          }`}
      >
        <div className="max-w-[1200px] mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-10">
            <div className="flex items-center group cursor-pointer">
              <LogoSvg
                className="h-16 md:h-20 w-auto text-[#1D1D1F] transition-all duration-500 group-hover:opacity-70"
              />
            </div>
          </div>
          <div className="flex items-center gap-8">
            <div className="hidden md:flex items-center gap-6 text-sm font-semibold text-[#6E6E73]">
              <span className="hover:text-[#1D1D1F] transition-colors cursor-pointer">
                {L(t.nav.product, locale)}
              </span>
              <span className="hover:text-[#1D1D1F] transition-colors cursor-pointer">
                {L(t.nav.docs, locale)}
              </span>
              <span className="hover:text-[#1D1D1F] transition-colors cursor-pointer">
                {L(t.nav.pricing, locale)}
              </span>
              <Link
                href="/login"
                className="hover:text-[#1D1D1F] transition-colors"
              >
                {L(t.nav.login, locale)}
              </Link>
            </div>

            {/* 语言切换按钮 */}
            <button
              onClick={toggleLocale}
              className="flex items-center gap-2 h-9 px-4 rounded-full border border-[#D2D2D7] bg-white text-sm font-bold text-[#6E6E73] hover:text-[#1D1D1F] hover:border-[#86868B] transition-all"
            >
              <Languages size={14} />
              {locale === "zh" ? "EN" : "中文"}
            </button>

            {/* CTA 按钮 - Apple 黑底白字风格 */}
            <button className="relative group overflow-hidden h-11 px-8 bg-[#1D1D1F] text-white text-[12px] font-black uppercase tracking-widest rounded-full flex items-center gap-2 hover:bg-[#000000] transition-all active:scale-95 shadow-sm">
              {L(t.nav.cta, locale)}{" "}
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </nav>

      {/* ===== Hero 区块 ===== */}
      <section id="hero" className="relative pt-64 pb-32">
        <div
          className={`max-w-[1200px] mx-auto px-6 transition-all duration-1000 transform ${visibleSections.hero ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
        >
          <div className="flex flex-col items-center text-center">
            {/* 徽章 - Apple 浅色风格 */}
            <a
              href="#"
              className="group inline-flex items-center gap-3 px-4 py-2 rounded-full bg-[#F5F5F7] border border-[#D2D2D7] mb-12 hover:border-[#86868B] transition-colors"
            >
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-[#1D1D1F]">
                <Zap size={12} className="text-white fill-white animate-pulse" />
              </span>
              <span className="text-xs font-bold text-[#86868B] group-hover:text-[#1D1D1F] transition-colors">
                {L(t.hero.badge, locale)}
              </span>
              <ChevronRight
                size={14}
                className="text-[#86868B] group-hover:text-[#1D1D1F] group-hover:translate-x-1 transition-all"
              />
            </a>

            {/* 标题 - Apple 黑色 #1D1D1F */}
            <h1 className="text-6xl md:text-[100px] font-black tracking-[-0.04em] leading-[0.95] mb-12 font-heading">
              <span className="text-[#1D1D1F]">
                {L(t.hero.title1, locale)}
              </span>
              <br />
              <div className="relative inline-block mt-4">
                <span className="relative text-gradient-silver italic">
                  {L(t.hero.title2, locale)}
                </span>
              </div>
            </h1>

            <p className="text-xl md:text-2xl text-[#86868B] max-w-3xl leading-relaxed mb-16 font-medium">
              {L(t.hero.desc, locale)}
              <strong className="text-[#1D1D1F] font-bold">{L(t.hero.descBold, locale)}</strong>
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mb-4">
              {/* 主按钮 - Apple 黑底白字 */}
              <button className="h-14 px-10 bg-[#1D1D1F] text-white rounded-xl font-black text-[13px] uppercase tracking-widest hover:bg-black transition-all hover:-translate-y-0.5 active:scale-95 flex items-center gap-3 shadow-lg">
                {L(t.hero.btnPrimary, locale)}{" "}
                <Sparkles size={16} className="text-white/80 animate-wiggle" />
              </button>
              {/* 次要按钮 - Apple 细边框风格 */}
              <button className="h-14 px-10 bg-white border border-[#D2D2D7] text-[#1D1D1F] rounded-xl font-bold text-[13px] hover:bg-[#F5F5F7] transition-all flex items-center gap-3">
                <Github size={18} className="text-[#1D1D1F]" /> {L(t.hero.btnGithub, locale)}
              </button>
            </div>

            <div className="text-[11px] text-[#86868B] font-medium flex items-center justify-center gap-6">
              <span className="flex items-center gap-1">
                <CheckCircle2 size={12} className="text-[#1D1D1F]" /> {L(t.hero.noCreditCard, locale)}
              </span>
              <span className="flex items-center gap-1">
                <CheckCircle2 size={12} className="text-[#1D1D1F]" /> {L(t.hero.deploy, locale)}
              </span>
            </div>

            {/* Trusted By */}
            <div className="mt-32 pt-12 border-t border-[#D2D2D7] w-full flex flex-col items-center">
              <p className="text-[11px] font-bold text-[#86868B] uppercase tracking-[0.3em] mb-8">
                {L(t.hero.trustedBy, locale)}
              </p>
              <div className="flex flex-wrap items-center justify-center gap-12 text-[#86868B] opacity-60 hover:opacity-100 transition-all duration-700">
                <div className="flex items-center gap-2 font-black text-xl">
                  <Globe size={24} /> GLOBEX
                </div>
                <div className="flex items-center gap-2 font-black text-xl italic">
                  <Command size={24} /> COMMAND_
                </div>
                <div className="flex items-center gap-2 font-black text-xl">
                  <Waves size={24} /> SYNTH
                </div>
                <div className="flex items-center gap-2 font-black text-xl uppercase">
                  <Fingerprint size={24} /> VaultTech
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== Interactive Showcase 区块 ===== */}
      <section id="interactive" className="py-24 relative">
        <div
          className={`max-w-[1200px] mx-auto px-6 relative z-10 transition-all duration-1000 delay-200 transform ${visibleSections.interactive ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
        >
          {/* 卡片容器 - Apple 浅灰背景 + 细边框 + 阴影 */}
          <div className="relative group rounded-[2.5rem] border border-[#D2D2D7] overflow-hidden shadow-[0_2px_20px_rgba(0,0,0,0.06)]">
            {/* 扫描线（浅灰色） */}
            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#D2D2D7] to-transparent animate-scan z-20 opacity-60" />

            <div className="relative bg-[#F5F5F7] rounded-[calc(2.5rem-1px)] overflow-hidden">
              <div className="grid lg:grid-cols-12 min-h-[660px]">
                {/* 左侧面板 */}
                <div className="lg:col-span-4 border-r border-[#D2D2D7] p-12 flex flex-col justify-between bg-white">
                  <div className="space-y-16">
                    <div className="space-y-3">
                      <h3 className="text-[#1D1D1F] text-2xl font-black tracking-tight uppercase italic flex items-center gap-3 font-heading">
                        <Activity className="text-[#1D1D1F]/70 animate-pulse" size={24} />{" "}
                        {L(t.interactive.engineTitle, locale)}
                      </h3>
                      <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#86868B] ml-9">
                        {L(t.interactive.engineSub, locale)}
                      </p>
                    </div>
                    <div className="space-y-4 relative before:absolute before:inset-y-4 before:left-[11px] before:w-px before:bg-[#D2D2D7] before:-z-10">
                      {tabLabels.map((tab, i) => (
                        <button
                          key={tab}
                          onClick={() => setActiveTab(i)}
                          className={`w-full text-left group/btn relative pl-10 py-5 rounded-xl transition-all duration-500 ${activeTab === i
                            ? "bg-[#F5F5F7] border border-[#D2D2D7] shadow-sm"
                            : "hover:bg-[#F5F5F7]/50"
                            }`}
                        >
                          <div
                            className={`text-[13px] font-black uppercase tracking-[0.2em] transition-all duration-700 ${activeTab === i
                              ? "text-[#1D1D1F] translate-x-1"
                              : "text-[#86868B] group-hover/btn:text-[#6E6E73]"
                              }`}
                          >
                            <span className="text-[10px] text-[#86868B] mr-2">STEP 0{i + 1}</span>{" "}
                            {tab}
                          </div>
                          <div
                            className={`absolute left-[5px] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full transition-all duration-500 ring-4 ring-white ${activeTab === i
                              ? "bg-[#1D1D1F] shadow-md scale-125"
                              : "bg-[#D2D2D7]"
                              }`}
                          />
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 状态监控条 */}
                  <div className="p-6 rounded-2xl bg-[#F5F5F7] border border-[#D2D2D7]">
                    <div className="flex justify-between items-center mb-3">
                      <div className="text-[10px] font-black text-[#1D1D1F] uppercase tracking-widest flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-[#1D1D1F] rounded-full animate-pulse" />{" "}
                        {L(t.interactive.statusLabel, locale)}
                      </div>
                      <div className="text-[10px] font-mono text-[#86868B]">98%</div>
                    </div>
                    <div className="w-full h-1.5 bg-[#D2D2D7]/50 rounded-full overflow-hidden">
                      <div className="w-[98%] h-full bg-gradient-to-r from-[#86868B] via-[#1D1D1F] to-[#86868B] animate-gradient-x rounded-full" />
                    </div>
                  </div>
                </div>

                {/* 右侧面板 */}
                <div className="lg:col-span-8 p-12 relative flex flex-col justify-center overflow-hidden bg-white">
                  <div className="absolute inset-0 bg-[linear-gradient(rgba(210,210,215,0.3)_1px,transparent_1px),linear-gradient(90deg,rgba(210,210,215,0.3)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

                  <div className="font-mono text-[13px] leading-relaxed relative z-10">
                    {/* Step 01 */}
                    {activeTab === 0 && (
                      <div className="space-y-10 animate-reveal">
                        <div className="flex items-center gap-4 text-[#1D1D1F]">
                          <span className="px-3 py-1.5 bg-[#1D1D1F] text-white text-[10px] font-black rounded uppercase">
                            Step 01
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                            {L(t.interactive.step01Label, locale)}{" "}
                            <span className="flex gap-1">
                              <span className="w-1 h-1 bg-[#1D1D1F] rounded-full animate-bounce" />
                              <span className="w-1 h-1 bg-[#1D1D1F] rounded-full animate-bounce delay-100" />
                              <span className="w-1 h-1 bg-[#1D1D1F] rounded-full animate-bounce delay-200" />
                            </span>
                          </span>
                        </div>
                        <div className="text-[#1D1D1F] text-3xl lg:text-4xl font-bold tracking-tight leading-snug">
                          <span className="relative">
                            <span className="text-[#86868B]">&gt;</span>{" "}
                            {locale === "zh" ? (
                              <>
                                构建一个支持{" "}
                                <span className="text-gradient-silver px-1 border-b border-[#1D1D1F]/30">
                                  Stripe
                                </span>{" "}
                                支付、<span className="text-[#86868B] italic">RBAC</span>{" "}
                                权限和实时库存推送的跨境电商平台。
                              </>
                            ) : (
                              <>
                                Build a cross-border e-commerce platform with{" "}
                                <span className="text-gradient-silver px-1 border-b border-[#1D1D1F]/30">
                                  Stripe
                                </span>{" "}
                                payments,{" "}
                                <span className="text-[#86868B] italic">RBAC</span> permissions,
                                and real-time inventory push.
                              </>
                            )}
                            <span className="absolute -right-4 top-1 w-[3px] h-8 bg-[#1D1D1F] animate-blink" />
                          </span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-10">
                          <div className="p-6 bg-[#F5F5F7] hover:bg-[#EBEBED] rounded-2xl border border-[#D2D2D7] hover:border-[#86868B] transition-all hover:-translate-y-1 hover:shadow-md group">
                            <BoxSelect
                              className="text-[#1D1D1F]/70 mb-4 group-hover:scale-110 transition-transform"
                              size={20}
                            />
                            <div className="text-[#1D1D1F] text-[12px] font-black uppercase mb-2">
                              {L(t.interactive.identifyEntities, locale)}
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <span className="px-2 py-1 bg-white border border-[#D2D2D7] rounded text-[#6E6E73] text-[10px]">
                                Product_SKU
                              </span>
                              <span className="px-2 py-1 bg-white border border-[#D2D2D7] rounded text-[#6E6E73] text-[10px]">
                                Vendor_Auth
                              </span>
                            </div>
                          </div>
                          <div className="p-6 bg-[#F5F5F7] hover:bg-[#EBEBED] rounded-2xl border border-[#D2D2D7] hover:border-[#86868B] transition-all hover:-translate-y-1 hover:shadow-md group">
                            <Settings
                              className="text-[#86868B] mb-4 animate-spin-slow group-hover:text-[#1D1D1F]/70"
                              size={20}
                            />
                            <div className="text-[#1D1D1F] text-[12px] font-black uppercase mb-2">
                              {L(t.interactive.identifyServices, locale)}
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <span className="px-2 py-1 bg-white border border-[#D2D2D7] rounded text-[#1D1D1F] text-[10px]">
                                Stripe_Webhooks
                              </span>
                              <span className="px-2 py-1 bg-white border border-[#D2D2D7] rounded text-[#6E6E73] text-[10px]">
                                Redis_Stream
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Step 02 */}
                    {activeTab === 1 && (
                      <div className="space-y-10 animate-reveal">
                        <div className="flex items-center gap-4 text-[#6E6E73]">
                          <span className="px-3 py-1.5 bg-[#1D1D1F] text-white text-[10px] font-black rounded uppercase">
                            Step 02
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                            {L(t.interactive.step02Label, locale)}{" "}
                            <span className="w-4 h-4 rounded-full border-t-2 border-[#1D1D1F] animate-spin" />
                          </span>
                        </div>
                        <div className="grid grid-cols-1 gap-6">
                          <div className="p-6 border border-[#D2D2D7] rounded-2xl bg-[#F5F5F7] relative overflow-hidden group/arch">
                            <div className="font-bold mb-6 flex items-center gap-4 text-[#1D1D1F] text-[11px] uppercase tracking-widest relative z-10">
                              <Workflow size={16} className="text-[#1D1D1F]/70" />{" "}
                              {L(t.interactive.archDiagram, locale)}
                            </div>
                            <div className="h-32 flex items-center justify-between px-8 relative z-10">
                              <div className="w-12 h-12 rounded-xl bg-white border border-[#D2D2D7] flex items-center justify-center shadow-sm z-10">
                                <Globe size={20} className="text-[#1D1D1F]" />
                              </div>
                              <div className="flex-1 h-[2px] bg-[#D2D2D7] relative mx-4">
                                <div className="absolute top-1/2 left-0 w-8 h-[2px] bg-[#1D1D1F] -translate-y-1/2 animate-move-x" />
                                <div className="absolute top-1/2 left-1/4 w-3 h-3 bg-[#00c853] rounded-full -translate-y-1/2 shadow-[0_0_8px_rgba(0,200,83,0.3)]" />
                                <div className="absolute top-1/2 left-3/4 w-3 h-3 bg-[#1D1D1F] rounded-full -translate-y-1/2" />
                              </div>
                              <div className="w-12 h-12 rounded-xl bg-white border border-[#D2D2D7] flex items-center justify-center shadow-sm z-10">
                                <Database size={20} className="text-[#86868B]" />
                              </div>
                            </div>
                          </div>
                          <div className="p-6 border border-[#D2D2D7] rounded-2xl bg-[#F5F5F7] flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <Database size={16} className="text-[#86868B]" />
                              <div>
                                <div className="text-[#1D1D1F] text-[11px] font-bold uppercase tracking-widest mb-1">
                                  {L(t.interactive.ermTitle, locale)}
                                </div>
                                <div className="text-[#86868B] text-[10px]">
                                  {L(t.interactive.ermDesc, locale)}
                                </div>
                              </div>
                            </div>
                            <div className="w-32 space-y-2">
                              <div className="h-1.5 w-full bg-[#D2D2D7]/50 rounded-full relative overflow-hidden">
                                <div className="absolute inset-0 bg-[#1D1D1F]/60 animate-shimmer" />
                              </div>
                              <div className="h-1.5 w-[70%] bg-[#D2D2D7]/50 rounded-full relative overflow-hidden">
                                <div
                                  className="absolute inset-0 bg-[#86868B] animate-shimmer"
                                  style={{ animationDelay: "0.4s" }}
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Step 03 */}
                    {activeTab === 2 && (
                      <div className="space-y-8 animate-reveal">
                        <div className="flex items-center gap-4 text-[#1D1D1F]">
                          <span className="px-3 py-1.5 bg-[#00c853] text-white text-[10px] font-black rounded uppercase">
                            Step 03
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                            {L(t.interactive.step03Label, locale)} <CheckCircle2 size={14} className="text-[#00c853]" />
                          </span>
                        </div>
                        <div className="space-y-4">
                          {[
                            {
                              name: "server/api/v1/stripe_adapter.go",
                              status: "COMPILED",
                              color: "text-[#1D1D1F]",
                              bg: "bg-[#F5F5F7]",
                              border: "border-[#D2D2D7]",
                            },
                            {
                              name: "client/components/Dashboard.tsx",
                              status: "COMPILED",
                              color: "text-[#1D1D1F]",
                              bg: "bg-[#F5F5F7]",
                              border: "border-[#D2D2D7]",
                            },
                            {
                              name: "infra/terraform/main.tf",
                              status: "DEPLOYED",
                              color: "text-[#00c853]",
                              bg: "bg-[#F5F5F7]",
                              border: "border-[#00c853]/30",
                            },
                          ].map((file) => (
                            <div
                              key={file.name}
                              className={`flex justify-between items-center px-6 py-4 border bg-white hover:bg-[#F5F5F7] transition-all rounded-xl cursor-default group/file hover:shadow-sm ${file.border}`}
                            >
                              <div className="flex items-center gap-3">
                                <FileText
                                  size={14}
                                  className="text-[#86868B] group-hover/file:text-[#1D1D1F] transition-colors"
                                />
                                <span className="text-[12px] text-[#6E6E73] group-hover/file:text-[#1D1D1F] transition-colors">
                                  {file.name}
                                </span>
                              </div>
                              <div className="flex items-center gap-4">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest ${file.bg} ${file.color}`}
                                >
                                  {file.status}
                                </span>
                                <CheckCircle2 size={16} className="text-[#00c853]" />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Web Terminal - 保留深色终端外观（终端本身就是深色的） */}
                  <div className="mt-8 self-end px-4 py-2 bg-[#1D1D1F] border border-[#1D1D1F] rounded-lg shadow-lg flex items-center gap-4 cursor-pointer hover:shadow-xl transition-all z-10 w-full max-w-sm relative overflow-hidden">
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#00c853] animate-pulse" />
                    <div className="flex items-center gap-3 text-[10px] font-bold text-white/70 uppercase tracking-widest pl-2">
                      <TerminalSquare size={14} className="text-white/80" /> /var/log/va_engine.log
                    </div>
                    <div className="mx-auto flex-1 w-px h-3 bg-white/20" />
                    <div className="text-[10px] font-black text-white/80 animate-pulse flex items-center gap-1">
                      Running <span className="w-2 h-2 rounded-full bg-[#00c853] inline-block" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== Capabilities 区块 ===== */}
      {/* Apple Pure White 风格 · 时间线贯穿 · 数字计数器 · hover 微交互 */}
      <section
        id="capabilities"
        className="py-32 relative"
        style={{ background: "#F5F5F7" }}
        ref={capabilitiesRef}
      >
        <div className="max-w-[1200px] mx-auto px-6">
          {/* 区块标题 */}
          <div className="mb-20 text-center">
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-black text-[#1D1D1F] tracking-tight leading-tight font-heading">
              {L(t.capabilities.sectionTitle, locale)}
            </h2>
            <p className="mt-6 text-[#6E6E73] max-w-xl mx-auto font-medium text-[15px]">
              {L(t.capabilities.sectionDesc, locale)}
            </p>
          </div>

          {/* 卡片容器（带时间线） */}
          <div className="relative">
            {/* === 垂直时间线 === */}
            {/* 底色浅灰线 */}
            <div
              className="absolute left-6 md:left-10 top-0 bottom-0 w-[2px] rounded-full hidden md:block"
              style={{ background: "#D2D2D7" }}
            />
            {/* 亮灯线（滚动驱动，黑色从上到下） */}
            <div
              className="absolute left-6 md:left-10 top-0 w-[2px] rounded-full hidden md:block transition-[height] duration-100 ease-linear"
              style={{
                height: `${timelineProgress * 100}%`,
                background: "linear-gradient(to bottom, #1D1D1F, #1D1D1F 90%, transparent)",
              }}
            />

            {/* === 6 张卡片 === */}
            <div className="flex flex-col gap-5">
              {capabilityMeta.map((meta, i) => {
                const isLit = litNodes[i];
                // 从 i18n 翻译获取卡片内容
                const card = t.capabilities.cards[i];
                const cardSuffix = L(card.suffix, locale);
                const cardTitle = L(card.title, locale);
                const cardDesc = L(card.desc, locale);
                return (
                  <div
                    key={i}
                    ref={(el) => { cardRefs.current[i] = el; }}
                    className="relative md:pl-24"
                  >
                    {/* 时间线节点圆点 */}
                    <div
                      className={`
                        absolute left-[14px] md:left-[30px] top-1/2 -translate-y-1/2
                        w-4 h-4 rounded-full z-10
                        border-2 transition-all duration-500 hidden md:block
                        ${isLit
                          ? "bg-[#1D1D1F] border-[#1D1D1F] animate-node-glow"
                          : "bg-white border-[#D2D2D7]"
                        }
                      `}
                    />

                    {/* 卡片主体 */}
                    <div
                      className={`
                        group relative overflow-hidden rounded-[16px]
                        border transition-all duration-[400ms]
                        ${capabilitiesVisible ? "animate-card-enter" : "opacity-0"}
                        hover:-translate-y-1
                        hover:shadow-lg
                      `}
                      style={{
                        background: "#FFFFFF",
                        borderColor: "#D2D2D7",
                        animationDelay: capabilitiesVisible ? `${i * 150}ms` : "0ms",
                        transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)",
                      }}
                      onMouseEnter={(e) => {
                        const el = e.currentTarget;
                        el.style.borderColor = "#86868B";
                        el.style.background = "#FAFAFA";
                      }}
                      onMouseLeave={(e) => {
                        const el = e.currentTarget;
                        el.style.borderColor = "#D2D2D7";
                        el.style.background = "#FFFFFF";
                      }}
                    >
                      {/* 卡片内部：左侧统计数字 + 右侧标题描述 */}
                      <div className="relative z-10 p-9 flex flex-col sm:flex-row items-start gap-8">
                        {/* 左侧：统计数字区域 */}
                        <div className="flex-shrink-0 w-full sm:w-[200px] flex flex-col items-center sm:items-start justify-center">
                          <div
                            className="text-5xl md:text-6xl font-black tracking-tighter font-mono-jb text-[#1D1D1F] group-hover:scale-110 transition-all duration-[400ms] origin-left"
                            style={{
                              transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)",
                            }}
                          >
                            <AnimatedStat meta={meta} suffix={cardSuffix} isVisible={capabilitiesVisible} />
                          </div>
                        </div>

                        {/* 右侧：标题 + 描述 */}
                        <div className="flex-1 min-w-0">
                          <h4 className="text-[#1D1D1F] text-xl md:text-2xl font-bold tracking-tight font-heading mb-3">
                            {cardTitle}
                          </h4>
                          <p className="text-[14px] leading-relaxed text-[#6E6E73] font-medium">
                            {cardDesc}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* ===== CTA 区块 ===== */}
      <section id="cta" className="py-48 relative overflow-hidden text-center border-t border-[#D2D2D7]">
        <div className="absolute inset-0 bg-white" />

        <div
          className={`max-w-[1200px] mx-auto px-6 relative z-10 transition-all duration-1000 transform ${visibleSections.cta ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
        >
          <div className="inline-block mb-8">
            <div className="px-6 py-2 rounded-full bg-[#F5F5F7] border border-[#D2D2D7] text-[11px] font-bold text-[#86868B] uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#1D1D1F] animate-pulse" />{" "}
              {L(t.cta.badge, locale)}
            </div>
          </div>
          <h2 className="text-5xl md:text-[80px] font-black tracking-[-0.04em] mb-12 leading-tight font-heading">
            <span className="text-[#1D1D1F]">{L(t.cta.title1, locale)}</span> <br />
            <span className="text-gradient-silver italic">{L(t.cta.title2, locale)}</span>
          </h2>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            {/* CTA 主按钮 - Apple 黑底白字 */}
            <button className="h-16 px-14 bg-[#1D1D1F] text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 hover:bg-black transition-all shadow-lg active:scale-95 flex items-center gap-2">
              {L(t.cta.btnPrimary, locale)} <ArrowRight size={16} />
            </button>
            {/* 次要按钮 - Apple 细边框 */}
            <button className="h-16 px-14 bg-white border border-[#D2D2D7] text-[#1D1D1F] rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-[#F5F5F7] transition-all active:scale-95 flex items-center justify-center">
              {L(t.cta.btnSecondary, locale)}
            </button>
          </div>
          <p className="mt-8 text-xs text-[#86868B] font-medium tracking-widest uppercase">
            {L(t.cta.bottomText, locale)}
          </p>
        </div>
      </section>

      {/* ===== Footer（Apple 浅灰底） ===== */}
      <footer className="py-16 border-t border-[#D2D2D7] bg-[#F5F5F7] relative z-10">
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
            <div className="md:col-span-2 space-y-6">
              <div className="flex items-center gap-3">
                <LogoSvg
                  className="h-16 md:h-20 w-auto text-[#1D1D1F]"
                />
              </div>
              <p className="text-sm text-[#86868B] max-w-sm leading-relaxed">
                {L(t.footer.desc, locale)}
              </p>
            </div>
            <div className="space-y-4">
              <h4 className="text-[#1D1D1F] font-bold text-sm tracking-widest uppercase">
                {L(t.footer.ecosystem, locale)}
              </h4>
              <ul className="space-y-2 text-sm text-[#86868B]">
                {(L(t.footer.ecosystemItems, locale) as readonly string[]).map((item) => (
                  <li key={item} className="hover:text-[#1D1D1F] transition-colors cursor-pointer">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="text-[#1D1D1F] font-bold text-sm tracking-widest uppercase">
                {L(t.footer.developers, locale)}
              </h4>
              <ul className="space-y-2 text-sm text-[#86868B]">
                {(L(t.footer.developerItems, locale) as readonly string[]).map((item, idx) => (
                  <li key={item} className="hover:text-[#1D1D1F] transition-colors cursor-pointer">
                    {item}
                    {idx === 1 && <span className="text-[#1D1D1F] ml-1">&bull;</span>}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-[#D2D2D7] flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#86868B]">
              &copy; 2026 VibeArtifact Inc. All Rights Reserved.
            </div>
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-full bg-[#F5F5F7] flex items-center justify-center text-[#86868B] hover:text-[#1D1D1F] hover:bg-[#EBEBED] border border-[#D2D2D7] transition-all cursor-pointer">
                <Github size={16} />
              </div>
              <div className="w-10 h-10 rounded-full bg-[#F5F5F7] flex items-center justify-center text-[#86868B] hover:text-[#1D1D1F] hover:bg-[#EBEBED] border border-[#D2D2D7] transition-all cursor-pointer">
                <Globe size={16} />
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
