"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Github,
  CheckCircle2,
  Globe,
  Command,
  Monitor,
  Workflow,
  Cpu,
  Activity,
  Zap,
  Code2,
  Database,
  ShieldCheck,
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

/** Helper: pick value by locale */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

const capabilityMeta = [
  { icon: Cpu, stat: "99.9%", color: "px-cyan", gradient: "from-white/40 to-white/10" },
  { icon: Code2, stat: "< 100ms", color: "px-purple", gradient: "from-slate-500 to-slate-400" },
  { icon: Monitor, stat: "Multi-Cloud", color: "px-orange", gradient: "from-slate-600 to-slate-500" },
  { icon: Workflow, stat: "Zero", color: "amber", gradient: "from-slate-400 to-slate-300" },
  { icon: FileText, stat: "Real-time", color: "px-green", gradient: "from-white/30 to-white/5" },
  { icon: ShieldCheck, stat: "100%", color: "blue", gradient: "from-slate-600 to-slate-400" },
];

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

export default function Home() {
  const { locale, toggleLocale } = useLocale();
  const [scrolled, setScrolled] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [visibleSections, setVisibleSections] = useState<Record<string, boolean>>({});

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

  const capItems = t.capabilities.items;
  const tabLabels: readonly string[] = L(t.interactive.tabs, locale);

  return (
    <div className="min-h-screen bg-[#020205] text-slate-300 font-sans selection:bg-indigo-500/40 overflow-x-hidden antialiased tracking-tight">
      {/* ===== Background ===== */}
      {/* ===== 背景极光 + 点阵 ===== */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[70%] h-[70%] bg-indigo-600/10 blur-[180px] rounded-full mix-blend-screen animate-pulse-slow" />
        <div
          className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-purple-600/15 blur-[150px] rounded-full mix-blend-screen animate-float"
          style={{ animationDelay: "2s" }}
        />
        <div className="absolute inset-0 bg-[radial-gradient(#ffffff08_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
      </div>

      {/* ===== Nav ===== */}
      <nav
        className={`fixed top-0 w-full z-[100] transition-all duration-700 ${scrolled
          ? "py-4 bg-[#020205]/70 backdrop-blur-2xl border-b border-white/5 shadow-[0_4px_30px_rgba(0,0,0,0.5)]"
          : "py-8 bg-transparent"
          }`}
      >
        <div className="max-w-[1200px] mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-10">
            <div className="flex items-center group cursor-pointer">
              <LogoSvg
                className="h-16 md:h-20 w-auto text-white transition-all duration-500 group-hover:opacity-80"
              />
            </div>
          </div>
          <div className="flex items-center gap-8">
            <div className="hidden md:flex items-center gap-6 text-sm font-semibold text-slate-400">
              <span className="hover:text-white transition-colors cursor-pointer">
                {L(t.nav.product, locale)}
              </span>
              <span className="hover:text-white transition-colors cursor-pointer">
                {L(t.nav.docs, locale)}
              </span>
              <span className="hover:text-white transition-colors cursor-pointer">
                {L(t.nav.pricing, locale)}
              </span>
              <Link
                href="/login"
                className="hover:text-white transition-colors"
              >
                {L(t.nav.login, locale)}
              </Link>
            </div>

            {/* 语言切换 */}
            <button
              onClick={toggleLocale}
              className="flex items-center gap-2 h-9 px-4 rounded-full border border-white/10 bg-white/[0.03] text-sm font-bold text-slate-400 hover:text-white hover:border-white/40 transition-all"
            >
              <Languages size={14} />
              {locale === "zh" ? "EN" : "中文"}
            </button>

            <button className="relative group overflow-hidden h-11 px-8 bg-indigo-600 text-white text-[12px] font-black uppercase tracking-widest rounded-full flex items-center gap-2 hover:shadow-[0_0_30px_rgba(99,102,241,0.4)] transition-all active:scale-95 border border-white/20 shadow-lg shadow-indigo-600/20">
              {L(t.nav.cta, locale)}{" "}
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </nav>

      {/* ===== Hero ===== */}
      <section id="hero" className="relative pt-64 pb-32">
        <div
          className={`max-w-[1200px] mx-auto px-6 transition-all duration-1000 transform ${visibleSections.hero ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
        >
          <div className="flex flex-col items-center text-center">
            <a
              href="#"
              className="group inline-flex items-center gap-3 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 backdrop-blur-md mb-12 hover:border-indigo-500/40 transition-colors"
            >
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-indigo-500/20">
                <Zap size={12} className="text-indigo-400 fill-indigo-400 animate-pulse" />
              </span>
              <span className="text-xs font-bold text-indigo-300 group-hover:text-white transition-colors">
                {L(t.hero.badge, locale)}
              </span>
              <ChevronRight
                size={14}
                className="text-indigo-500 group-hover:text-white group-hover:translate-x-1 transition-all"
              />
            </a>

            <h1 className="text-6xl md:text-[100px] font-black tracking-[-0.04em] leading-[0.95] mb-12">
              <span className="text-white drop-shadow-lg">
                {L(t.hero.title1, locale)}
              </span>
              <br />
              <div className="relative inline-block mt-4">
                <span className="absolute -inset-2 bg-indigo-500/10 blur-2xl rounded-full" />
                <span className="relative text-gradient-indigo italic">
                  {L(t.hero.title2, locale)}
                </span>
              </div>
            </h1>

            <p className="text-xl md:text-2xl text-slate-400 max-w-3xl leading-relaxed mb-16 font-medium">
              {L(t.hero.desc, locale)}
              <strong className="text-white font-bold">{L(t.hero.descBold, locale)}</strong>
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mb-4">
              <button className="h-14 px-10 bg-white text-black rounded-xl font-black text-[13px] uppercase tracking-widest hover:bg-slate-200 transition-all transition-all hover:-translate-y-0.5 active:scale-95 flex items-center gap-3 shadow-[0_0_30px_rgba(255,255,255,0.2)]">
                {L(t.hero.btnPrimary, locale)}{" "}
                <Sparkles size={16} className="text-black/80 animate-wiggle" />
              </button>
              <button className="h-14 px-10 bg-white/[0.03] border border-white/10 text-white rounded-xl font-bold text-[13px] hover:bg-white/10 transition-all backdrop-blur-sm flex items-center gap-3">
                <Github size={18} className="text-white" /> {L(t.hero.btnGithub, locale)}
              </button>
            </div>

            <div className="text-[11px] text-slate-500 font-medium flex items-center justify-center gap-6">
              <span className="flex items-center gap-1">
                <CheckCircle2 size={12} className="text-slate-300" /> {L(t.hero.noCreditCard, locale)}
              </span>
              <span className="flex items-center gap-1">
                <CheckCircle2 size={12} className="text-slate-300" /> {L(t.hero.deploy, locale)}
              </span>
            </div>

            {/* Trusted By */}
            <div className="mt-32 pt-12 border-t border-white/5 w-full flex flex-col items-center">
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.3em] mb-8">
                {L(t.hero.trustedBy, locale)}
              </p>
              <div className="flex flex-wrap items-center justify-center gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-700">
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

      {/* ===== Interactive Showcase ===== */}
      <section id="interactive" className="py-24 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[800px] h-[600px] bg-white/[0.02] blur-[120px] rounded-full pointer-events-none" />

        <div
          className={`max-w-[1200px] mx-auto px-6 relative z-10 transition-all duration-1000 delay-200 transform ${visibleSections.interactive ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
        >
          <div className="relative group p-[1px] rounded-[2.5rem] bg-gradient-to-br from-indigo-500/30 via-purple-500/10 to-cyan-500/30 glow-border-indigo overflow-hidden">
            {/* Scan line */}
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-white to-transparent animate-scan z-20 opacity-80" />

            <div className="relative bg-[#050508]/95 rounded-[calc(2.5rem-1px)] overflow-hidden backdrop-blur-3xl shadow-2xl">
              <div className="grid lg:grid-cols-12 min-h-[660px]">
                {/* Left sidebar */}
                <div className="lg:col-span-4 border-r border-white/5 p-12 flex flex-col justify-between bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wMykiLz48L3N2Zz4=')]">
                  <div className="space-y-16">
                    <div className="space-y-3">
                      <h3 className="text-white text-2xl font-black tracking-tight uppercase italic flex items-center gap-3">
                        <Activity className="text-white animate-pulse glow-white" size={24} />{" "}
                        {L(t.interactive.engineTitle, locale)}
                      </h3>
                      <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/70 ml-9">
                        {L(t.interactive.engineSub, locale)}
                      </p>
                    </div>
                    <div className="space-y-4 relative before:absolute before:inset-y-4 before:left-[11px] before:w-px before:bg-white/10 before:-z-10">
                      {tabLabels.map((tab, i) => (
                        <button
                          key={tab}
                          onClick={() => setActiveTab(i)}
                          className={`w-full text-left group/btn relative pl-10 py-5 rounded-xl transition-all duration-500 ${activeTab === i
                            ? "bg-white/[0.02] border border-white/5"
                            : "hover:bg-white/[0.01]"
                            }`}
                        >
                          <div
                            className={`text-[13px] font-black uppercase tracking-[0.2em] transition-all duration-700 ${activeTab === i
                              ? "text-white translate-x-1 glow-text"
                              : "text-slate-500 group-hover/btn:text-slate-300"
                              }`}
                          >
                            <span className="text-[10px] text-slate-600 mr-2">STEP 0{i + 1}</span>{" "}
                            {tab}
                          </div>
                          <div
                            className={`absolute left-[5px] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full transition-all duration-500 ring-4 ring-[#050508] ${activeTab === i
                              ? "bg-white shadow-[0_0_20px_rgba(255,255,255,0.5)] scale-125"
                              : "bg-slate-800"
                              }`}
                          />
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Status monitor */}
                  <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/20 shadow-[inset_0_0_20px_rgba(255,255,255,0.03)]">
                    <div className="flex justify-between items-center mb-3">
                      <div className="text-[10px] font-black text-white uppercase tracking-widest flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />{" "}
                        {L(t.interactive.statusLabel, locale)}
                      </div>
                      <div className="text-[10px] font-mono text-slate-400">98%</div>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800/50 rounded-full overflow-hidden">
                      <div className="w-[98%] h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-500 animate-gradient-x" />
                    </div>
                  </div>
                </div>

                {/* Right panel */}
                <div className="lg:col-span-8 p-12 relative flex flex-col justify-center overflow-hidden">
                  <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

                  <div className="font-mono text-[13px] leading-relaxed relative z-10">
                    {/* Step 01 */}
                    {activeTab === 0 && (
                      <div className="space-y-10 animate-reveal">
                        <div className="flex items-center gap-4 text-white">
                          <span className="px-3 py-1.5 bg-white/5 border border-white/30 text-[10px] font-black rounded uppercase shadow-[0_0_15px_rgba(0,210,255,0.2)]">
                            Step 01
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                            {L(t.interactive.step01Label, locale)}{" "}
                            <span className="flex gap-1">
                              <span className="w-1 h-1 bg-white rounded-full animate-bounce" />
                              <span className="w-1 h-1 bg-white rounded-full animate-bounce delay-100" />
                              <span className="w-1 h-1 bg-white rounded-full animate-bounce delay-200" />
                            </span>
                          </span>
                        </div>
                        <div className="text-white text-3xl lg:text-4xl font-bold tracking-tight leading-snug">
                          <span className="relative">
                            <span className="text-white">&gt;</span>{" "}
                            {locale === "zh" ? (
                              <>
                                构建一个支持{" "}
                                <span className="text-gradient-silver px-1 border-b border-white/50">
                                  Stripe
                                </span>{" "}
                                支付、<span className="text-slate-400 italic">RBAC</span>{" "}
                                权限和实时库存推送的跨境电商平台。
                              </>
                            ) : (
                              <>
                                Build a cross-border e-commerce platform with{" "}
                                <span className="text-gradient-silver px-1 border-b border-white/50">
                                  Stripe
                                </span>{" "}
                                payments,{" "}
                                <span className="text-slate-400 italic">RBAC</span> permissions,
                                and real-time inventory push.
                              </>
                            )}
                            <span className="absolute -right-4 top-1 w-[3px] h-8 bg-white animate-blink" />
                          </span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-10">
                          <div className="p-6 bg-glass hover:bg-white/[0.04] rounded-2xl border border-white/10 hover:border-white/50 transition-all hover:-translate-y-1 group">
                            <BoxSelect
                              className="text-white mb-4 group-hover:scale-110 transition-transform"
                              size={20}
                            />
                            <div className="text-white text-[12px] font-black uppercase mb-2">
                              {L(t.interactive.identifyEntities, locale)}
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <span className="px-2 py-1 bg-white/5 border border-white/10 rounded text-slate-400 text-[10px]">
                                Product_SKU
                              </span>
                              <span className="px-2 py-1 bg-white/5 border border-white/10 rounded text-slate-400 text-[10px]">
                                Vendor_Auth
                              </span>
                            </div>
                          </div>
                          <div className="p-6 bg-glass hover:bg-white/[0.04] rounded-2xl border border-white/10 hover:border-purple-500/50 transition-all hover:-translate-y-1 group">
                            <Settings
                              className="text-slate-400 mb-4 animate-spin-slow group-hover:text-slate-300"
                              size={20}
                            />
                            <div className="text-white text-[12px] font-black uppercase mb-2">
                              {L(t.interactive.identifyServices, locale)}
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <span className="px-2 py-1 bg-white/5 border border-purple-500/20 rounded text-slate-300 text-[10px] glow-purple">
                                Stripe_Webhooks
                              </span>
                              <span className="px-2 py-1 bg-white/5 border border-white/10 rounded text-slate-400 text-[10px]">
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
                        <div className="flex items-center gap-4 text-slate-400">
                          <span className="px-3 py-1.5 bg-white/5 border border-white/30 text-[10px] font-black rounded uppercase shadow-[0_0_15px_rgba(168,85,247,0.2)]">
                            Step 02
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                            {L(t.interactive.step02Label, locale)}{" "}
                            <span className="w-4 h-4 rounded-full border-t-2 border-purple-400 animate-spin" />
                          </span>
                        </div>
                        <div className="grid grid-cols-1 gap-6">
                          <div className="p-6 border border-white/10 rounded-2xl bg-glass relative overflow-hidden group/arch">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 blur-3xl rounded-full" />
                            <div className="font-bold mb-6 flex items-center gap-4 text-white text-[11px] uppercase tracking-widest relative z-10">
                              <Workflow size={16} className="text-white" />{" "}
                              {L(t.interactive.archDiagram, locale)}
                            </div>
                            <div className="h-32 flex items-center justify-between px-8 relative z-10">
                              <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/30 flex items-center justify-center glow-white z-10">
                                <Globe size={20} className="text-white" />
                              </div>
                              <div className="flex-1 h-[2px] bg-white/5 relative mx-4">
                                <div className="absolute top-1/2 left-0 w-8 h-[2px] bg-white -translate-y-1/2 animate-move-x shadow-[0_0_10px_#00d2ff]" />
                                <div className="absolute top-1/2 left-1/4 w-3 h-3 bg-[#00c853] rounded-full -translate-y-1/2 shadow-[0_0_15px_#00c853]" />
                                <div className="absolute top-1/2 left-3/4 w-3 h-3 bg-slate-500 rounded-full -translate-y-1/2 shadow-[0_0_15px_#a855f7]" />
                              </div>
                              <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/30 flex items-center justify-center shadow-[0_0_20px_rgba(168,85,247,0.3)] z-10">
                                <Database size={20} className="text-slate-400" />
                              </div>
                            </div>
                          </div>
                          <div className="p-6 border border-white/10 rounded-2xl bg-glass flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <Database size={16} className="text-slate-400" />
                              <div>
                                <div className="text-white text-[11px] font-bold uppercase tracking-widest mb-1">
                                  {L(t.interactive.ermTitle, locale)}
                                </div>
                                <div className="text-slate-500 text-[10px]">
                                  {L(t.interactive.ermDesc, locale)}
                                </div>
                              </div>
                            </div>
                            <div className="w-32 space-y-2">
                              <div className="h-1.5 w-full bg-white/5 rounded-full relative overflow-hidden">
                                <div className="absolute inset-0 bg-white animate-shimmer" />
                              </div>
                              <div className="h-1.5 w-[70%] bg-white/5 rounded-full relative overflow-hidden">
                                <div
                                  className="absolute inset-0 bg-slate-500 animate-shimmer"
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
                        <div className="flex items-center gap-4 text-slate-300">
                          <span className="px-3 py-1.5 bg-white/5 border border-white/20 text-[10px] font-black rounded uppercase shadow-[0_0_15px_rgba(0,200,83,0.2)]">
                            Step 03
                          </span>
                          <span className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                            {L(t.interactive.step03Label, locale)} <CheckCircle2 size={14} />
                          </span>
                        </div>
                        <div className="space-y-4">
                          {[
                            {
                              name: "server/api/v1/stripe_adapter.go",
                              status: "COMPILED",
                              color: "text-white",
                              bg: "bg-white/5",
                              border: "border-white/20",
                            },
                            {
                              name: "client/components/Dashboard.tsx",
                              status: "COMPILED",
                              color: "text-white",
                              bg: "bg-white/5",
                              border: "border-white/20",
                            },
                            {
                              name: "infra/terraform/main.tf",
                              status: "DEPLOYED",
                              color: "text-slate-300",
                              bg: "bg-white/5",
                              border: "border-white/20 glow-green",
                            },
                          ].map((file) => (
                            <div
                              key={file.name}
                              className={`flex justify-between items-center px-6 py-4 border bg-glass hover:bg-white/[0.05] transition-all rounded-xl cursor-default group/file ${file.border}`}
                            >
                              <div className="flex items-center gap-3">
                                <FileText
                                  size={14}
                                  className="text-slate-500 group-hover/file:text-white transition-colors"
                                />
                                <span className="text-[12px] text-slate-400 group-hover/file:text-white transition-colors">
                                  {file.name}
                                </span>
                              </div>
                              <div className="flex items-center gap-4">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest ${file.bg} ${file.color}`}
                                >
                                  {file.status}
                                </span>
                                <CheckCircle2 size={16} className="text-slate-300" />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Web Terminal */}
                  <div className="mt-8 self-end px-4 py-2 bg-[#050508] border border-white/10 rounded-lg shadow-xl flex items-center gap-4 cursor-pointer hover:border-white/40 transition-all z-10 w-full max-w-sm relative overflow-hidden">
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#00c853] animate-pulse" />
                    <div className="flex items-center gap-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest pl-2">
                      <TerminalSquare size={14} className="text-white" /> /var/log/va_engine.log
                    </div>
                    <div className="mx-auto flex-1 w-px h-3 bg-white/10" />
                    <div className="text-[10px] font-black text-slate-300 animate-pulse flex items-center gap-1">
                      Running <span className="w-2 h-2 rounded-full bg-[#00c853] inline-block" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== Capabilities ===== */}
      <section id="capabilities" className="py-32 relative">
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="mb-20 flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-4">
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-black text-white tracking-tight uppercase italic leading-tight">
                {L(t.capabilities.sectionTitle1, locale)} <br />{" "}
                <span className="text-white">{L(t.capabilities.sectionTitle2, locale)}</span>
              </h2>
            </div>
            <p className="text-slate-400 max-w-sm font-medium text-[13px] border-l-2 border-white/20 pl-4 py-1">
              {L(t.capabilities.sectionDesc, locale)}
            </p>
          </div>

          <div
            className={`grid md:grid-cols-12 gap-6 transition-all duration-1000 transform ${visibleSections.capabilities ? "opacity-100 translate-y-0" : "opacity-0 translate-y-20"
              }`}
          >
            {capItems.map((item, i) => {
              const meta = capabilityMeta[i];
              const Icon = meta.icon;
              const colSpan = i === 0 || i === 3 || i === 4 ? "md:col-span-7" : "md:col-span-5";
              const isCyan = meta.color === "px-cyan";
              const isGreen = meta.color === "px-green";
              const isOrange = meta.color === "px-orange";
              const isPurple = meta.color === "px-purple";

              const statTextColor = isCyan
                ? "text-white"
                : isGreen
                  ? "text-slate-300"
                  : isOrange
                    ? "text-slate-400"
                    : isPurple
                      ? "text-white"
                      : "text-slate-300";
              const iconBgClass = isCyan
                ? "bg-white text-black"
                : "bg-white/[0.05] text-white";

              return (
                <div
                  key={i}
                  className={`group relative overflow-hidden bg-[#111113] border border-white/[0.05] rounded-3xl transition-all duration-500 hover:border-white/20 shadow-xl ${colSpan}`}
                  style={{ transitionDelay: `${i * 100}ms` }}
                >
                  <div
                    className={`absolute -top-32 -right-32 w-80 h-80 bg-gradient-to-br ${meta.gradient} opacity-0 group-hover:opacity-10 blur-[100px] transition-opacity duration-700 rounded-full pointer-events-none`}
                  />

                  <div className="relative z-10 p-8 lg:p-10 h-full flex flex-col">
                    <div className="flex justify-between items-start mb-10">
                      <div
                        className={`w-14 h-14 rounded-[14px] flex items-center justify-center transition-all duration-500 ${iconBgClass} group-hover:scale-110 shadow-lg`}
                      >
                        <Icon size={24} className="transition-colors" />
                      </div>
                      <div className="text-right">
                        <div className={`text-4xl font-black tracking-tighter ${statTextColor}`}>
                          {meta.stat}
                        </div>
                        <div className="text-[11px] text-slate-500 font-bold tracking-widest mt-1">
                          {L(item.statLabel, locale)}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4 mb-10">
                      <h4 className="text-white text-2xl font-bold tracking-tight">
                        {L(item.title, locale)}
                      </h4>
                      <p className="text-[14px] leading-relaxed text-slate-400 font-medium max-w-md">
                        {L(item.desc, locale)}
                      </p>
                    </div>

                    <div className="mt-auto pt-6 border-t border-white/[0.05] space-y-3">
                      {(L(item.features, locale) as readonly string[]).map((feature, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-3 text-[13px] text-slate-300 font-medium"
                        >
                          <div className="w-4 h-4 rounded-full border border-white/20 flex items-center justify-center">
                            <CheckCircle2 size={10} className="text-slate-300" />
                          </div>
                          {feature}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section id="cta" className="py-48 relative overflow-hidden text-center border-t border-white/5">
        <div className="absolute inset-0 bg-[#020205]" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[1000px] h-[400px] bg-gradient-to-t from-indigo-500/20 to-transparent blur-[100px] pointer-events-none" />
        <div className="absolute inset-x-0 bottom-0 h-[400px] bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:linear-gradient(to_top,black_0%,transparent_100%)] pointer-events-none" />

        <div
          className={`max-w-[1200px] mx-auto px-6 relative z-10 transition-all duration-1000 transform ${visibleSections.cta ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
        >
          <div className="inline-block p-[1px] rounded-full bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent mb-8">
            <div className="px-6 py-2 rounded-full bg-[#020205] border border-white/5 text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />{" "}
              {L(t.cta.badge, locale)}
            </div>
          </div>
          <h2 className="text-5xl md:text-[80px] font-black tracking-[-0.04em] mb-12 leading-tight">
            <span className="text-white">{L(t.cta.title1, locale)}</span> <br />
            <span className="text-gradient-indigo italic">{L(t.cta.title2, locale)}</span>
          </h2>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <button className="h-16 px-14 bg-white text-black rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 transition-transform shadow-[0_0_40px_rgba(255,255,255,0.1)] active:scale-95 flex items-center gap-2">
              {L(t.cta.btnPrimary, locale)} <ArrowRight size={16} />
            </button>
            <button className="h-16 px-14 bg-glass border border-white/10 text-white rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-white/10 transition-all active:scale-95 flex items-center justify-center">
              {L(t.cta.btnSecondary, locale)}
            </button>
          </div>
          <p className="mt-8 text-xs text-slate-500 font-medium tracking-widest uppercase">
            {L(t.cta.bottomText, locale)}
          </p>
        </div>
      </section>

      {/* ===== Footer ===== */}
      <footer className="py-16 border-t border-white/5 bg-[#010103] relative z-10">
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
            <div className="md:col-span-2 space-y-6">
              <div className="flex items-center gap-3">
                <LogoSvg
                  className="h-16 md:h-20 w-auto text-white"
                />
              </div>
              <p className="text-sm text-slate-500 max-w-sm leading-relaxed">
                {L(t.footer.desc, locale)}
              </p>
            </div>
            <div className="space-y-4">
              <h4 className="text-white font-bold text-sm tracking-widest uppercase">
                {L(t.footer.ecosystem, locale)}
              </h4>
              <ul className="space-y-2 text-sm text-slate-500">
                {(L(t.footer.ecosystemItems, locale) as readonly string[]).map((item) => (
                  <li key={item} className="hover:text-white transition-colors cursor-pointer">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="text-white font-bold text-sm tracking-widest uppercase">
                {L(t.footer.developers, locale)}
              </h4>
              <ul className="space-y-2 text-sm text-slate-500">
                {(L(t.footer.developerItems, locale) as readonly string[]).map((item, idx) => (
                  <li key={item} className="hover:text-white transition-colors cursor-pointer">
                    {item}
                    {idx === 1 && <span className="text-slate-300 ml-1">●</span>}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-600">
              &copy; 2026 VibeArtifact Inc. All Rights Reserved.
            </div>
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 hover:border-white/50 border border-transparent transition-all cursor-pointer">
                <Github size={16} />
              </div>
              <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 hover:border-white/50 border border-transparent transition-all cursor-pointer">
                <Globe size={16} />
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
